
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

from app.services.processing_job_service import (
    _connect,
    claim_next_processing_job,
    complete_processing_job,
    create_processing_job,
    get_processing_job,
    recover_expired_processing_jobs,
    renew_processing_job_lease,
    update_processing_job_progress,
)


created_jobs = []


def check(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"[OK] {message}")


def get_test_owners():
    owner_a = str(
        uuid.UUID(os.environ["TEST_OWNER_A"])
    )
    owner_b = str(
        uuid.UUID(os.environ["TEST_OWNER_B"])
    )

    if owner_a == owner_b:
        raise ValueError(
            "Use dois usuários de teste diferentes."
        )

    return owner_a, owner_b


def ensure_safe_test_environment():
    """
    Evita interferência com tarefas já existentes.

    Este teste deve ser executado somente quando
    não houver jobs pendentes ou em processamento.
    """
    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM public.processing_jobs
                WHERE status IN ('queued', 'processing')
                """
            )
            total = cursor.fetchone()["total"]

    if total != 0:
        raise RuntimeError(
            "Existem tarefas pendentes ou em processamento. "
            "Execute este teste apenas em uma fila de testes "
            "sem jobs ativos."
        )


def create_test_job(owner_id, filename):
    job = create_processing_job(
        owner_user_id=owner_id,
        source_type="simulation",
        original_filename=filename,
    )

    created_jobs.append(str(job["id"]))
    return job


def force_expire_test_lease(job_id):
    """
    Simula uma queda de worker alterando apenas
    o lease de uma tarefa criada pelo teste.
    """
    if job_id not in created_jobs:
        raise ValueError(
            "A tarefa não pertence a este teste."
        )

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.processing_jobs
                SET lease_expires_at =
                    now() - interval '10 seconds'
                WHERE id = %s
                  AND source_type = 'simulation'
                  AND status = 'processing'
                RETURNING id
                """,
                (job_id,),
            )

            if cursor.fetchone() is None:
                raise AssertionError(
                    "Não foi possível expirar o lease."
                )


def set_max_attempts(job_id, value):
    if job_id not in created_jobs:
        raise ValueError(
            "A tarefa não pertence a este teste."
        )

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.processing_jobs
                SET max_attempts = %s
                WHERE id = %s
                  AND status = 'queued'
                  AND attempts = 0
                RETURNING id
                """,
                (value, job_id),
            )

            if cursor.fetchone() is None:
                raise AssertionError(
                    "Não foi possível configurar tentativas."
                )


def cleanup():
    if not created_jobs:
        return

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM public.processing_jobs
                WHERE id = ANY(%s::uuid[])
                  AND source_type = 'simulation'
                """,
                (created_jobs,),
            )

    print("[OK] Tarefas fictícias removidas")


def test_concurrent_workers(owner_a, owner_b):
    job_a = create_test_job(
        owner_a,
        "__TEST_QUEUE_A.mp4",
    )
    job_b = create_test_job(
        owner_b,
        "__TEST_QUEUE_B.mp4",
    )

    def claim(worker_name):
        return claim_next_processing_job(
            worker_id=worker_name,
            lease_seconds=120,
            source_type="simulation",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(
            claim, "test-worker-a"
        )
        future_b = executor.submit(
            claim, "test-worker-b"
        )

        claimed_a = future_a.result()
        claimed_b = future_b.result()

    check(
        claimed_a is not None and claimed_b is not None,
        "Dois workers reservaram tarefas",
    )

    ids = {
        str(claimed_a["id"]),
        str(claimed_b["id"]),
    }

    check(
        ids == {
            str(job_a["id"]),
            str(job_b["id"]),
        },
        "Cada tarefa foi reservada uma única vez",
    )

    for claimed in (claimed_a, claimed_b):
        job_id = str(claimed["id"])
        worker_id = claimed["worker_id"]
        token = str(claimed["attempt_token"])

        renew_processing_job_lease(
            job_id=job_id,
            worker_id=worker_id,
            attempt_token=token,
            lease_seconds=120,
        )

        update_processing_job_progress(
            job_id=job_id,
            worker_id=worker_id,
            attempt_token=token,
            progress=50,
        )

        completed = complete_processing_job(
            job_id=job_id,
            worker_id=worker_id,
            attempt_token=token,
        )

        check(
            completed["status"] == "completed",
            f"Tarefa {job_id} concluída",
        )

    check(
        get_processing_job(
            str(job_a["id"]), owner_b
        ) is None,
        "Usuário B não consulta tarefa do usuário A",
    )

    check(
        get_processing_job(
            str(job_b["id"]), owner_a
        ) is None,
        "Usuário A não consulta tarefa do usuário B",
    )


def test_expired_lease(owner_a):
    job = create_test_job(
        owner_a,
        "__TEST_EXPIRED_LEASE.mp4",
    )

    job_id = str(job["id"])

    first = claim_next_processing_job(
        worker_id="test-worker-old",
        lease_seconds=120,
        source_type="simulation",
    )

    check(
        str(first["id"]) == job_id,
        "Primeiro worker reservou a tarefa",
    )

    old_token = str(first["attempt_token"])

    force_expire_test_lease(job_id)

    recovered = recover_expired_processing_jobs()

    check(
        any(str(item["id"]) == job_id for item in recovered),
        "Lease expirado recuperado",
    )

    second = claim_next_processing_job(
        worker_id="test-worker-new",
        lease_seconds=120,
        source_type="simulation",
    )

    check(
        str(second["id"]) == job_id,
        "Novo worker reservou a tarefa recuperada",
    )

    check(
        str(second["attempt_token"]) != old_token,
        "Nova tentativa recebeu token diferente",
    )

    try:
        complete_processing_job(
            job_id=job_id,
            worker_id="test-worker-old",
            attempt_token=old_token,
        )
    except ValueError:
        print(
            "[OK] Worker antigo não conseguiu "
            "finalizar a nova tentativa"
        )
    else:
        raise AssertionError(
            "Worker antigo finalizou uma tarefa recuperada."
        )

    completed = complete_processing_job(
        job_id=job_id,
        worker_id="test-worker-new",
        attempt_token=str(second["attempt_token"]),
    )

    check(
        completed["status"] == "completed"
        and completed["attempts"] == 2,
        "Tarefa recuperada concluída na segunda tentativa",
    )


def test_attempt_limit(owner_a):
    job = create_test_job(
        owner_a,
        "__TEST_ATTEMPT_LIMIT.mp4",
    )

    job_id = str(job["id"])
    set_max_attempts(job_id, 1)

    claimed = claim_next_processing_job(
        worker_id="test-worker-limit",
        lease_seconds=120,
        source_type="simulation",
    )

    check(
        str(claimed["id"]) == job_id,
        "Tarefa com limite de uma tentativa reservada",
    )

    force_expire_test_lease(job_id)

    recover_expired_processing_jobs()

    current = get_processing_job(
        job_id=job_id,
        owner_user_id=owner_a,
    )

    check(
        current["status"] == "failed"
        and current["attempts"] == 1,
        "Limite de tentativas encerrou a tarefa",
    )


def main():
    owner_a, owner_b = get_test_owners()

    ensure_safe_test_environment()

    try:
        test_concurrent_workers(owner_a, owner_b)
        test_expired_lease(owner_a)
        test_attempt_limit(owner_a)

        print()
        print(
            "SUCESSO: concorrência, recuperação, "
            "tokens e limite de tentativas validados."
        )

    finally:
        cleanup()


if __name__ == "__main__":
    main()
