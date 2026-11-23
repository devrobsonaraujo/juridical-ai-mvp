
import argparse
import logging
import os
import socket
import threading
import time
import uuid

from app.services.processing_job_service import (
    claim_next_processing_job,
    complete_processing_job,
    fail_processing_job,
    recover_expired_processing_jobs,
    renew_processing_job_lease,
    update_processing_job_progress,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

LEASE_SECONDS = 120
HEARTBEAT_SECONDS = 30
POLL_SECONDS = 3


def make_worker_id() -> str:
    return (
        f"{socket.gethostname()}-"
        f"{os.getpid()}-"
        f"{uuid.uuid4().hex[:8]}"
    )


def heartbeat_loop(
    job_id: str,
    worker_id: str,
    attempt_token: str,
    stop_event: threading.Event,
    lease_lost: threading.Event,
) -> None:
    while not stop_event.wait(HEARTBEAT_SECONDS):
        try:
            renew_processing_job_lease(
                job_id=job_id,
                worker_id=worker_id,
                attempt_token=attempt_token,
                lease_seconds=LEASE_SECONDS,
            )
        except Exception:
            logger.exception(
                "Falha na renovação do lease do job %s",
                job_id,
            )
            lease_lost.set()
            return


def process_simulation_job(
    job: dict,
    worker_id: str,
) -> None:
    job_id = str(job["id"])
    attempt_token = str(job["attempt_token"])

    if job["source_type"] != "simulation":
        raise ValueError(
            "Este worker aceita somente tarefas simuladas."
        )

    stop_event = threading.Event()
    lease_lost = threading.Event()

    heartbeat = threading.Thread(
        target=heartbeat_loop,
        args=(
            job_id,
            worker_id,
            attempt_token,
            stop_event,
            lease_lost,
        ),
        daemon=True,
    )

    heartbeat.start()

    try:
        for progress in (20, 40, 60, 80, 95):
            if lease_lost.is_set():
                raise RuntimeError(
                    "A reserva da tarefa foi perdida."
                )

            time.sleep(1)

            if lease_lost.is_set():
                raise RuntimeError(
                    "A reserva da tarefa foi perdida."
                )

            update_processing_job_progress(
                job_id=job_id,
                worker_id=worker_id,
                attempt_token=attempt_token,
                progress=progress,
            )

            logger.info(
                "Job %s: %s%%",
                job_id,
                progress,
            )

        if lease_lost.is_set():
            raise RuntimeError(
                "A reserva da tarefa foi perdida."
            )

        complete_processing_job(
            job_id=job_id,
            worker_id=worker_id,
            attempt_token=attempt_token,
        )

        logger.info(
            "Job %s concluído.",
            job_id,
        )

    except Exception:
        logger.exception(
            "Falha no processamento do job %s",
            job_id,
        )

        try:
            fail_processing_job(
                job_id=job_id,
                worker_id=worker_id,
                attempt_token=attempt_token,
                error_message="Falha no processamento simulado.",
            )
        except ValueError:
            logger.warning(
                "Não foi possível finalizar o job %s. "
                "A reserva pode ter expirado.",
                job_id,
            )

    finally:
        stop_event.set()
        heartbeat.join(timeout=5)


def run_worker(once: bool = False) -> None:
    worker_id = make_worker_id()

    logger.info(
        "Worker simulado iniciado: %s",
        worker_id,
    )

    while True:
        try:
            recovered = recover_expired_processing_jobs()

            if recovered:
                logger.info(
                    "%s tarefa(s) recuperada(s).",
                    len(recovered),
                )

            job = claim_next_processing_job(
                worker_id=worker_id,
                lease_seconds=LEASE_SECONDS,
                source_type="simulation",
            )

            if job is None:
                if once:
                    logger.info(
                        "Nenhuma tarefa pendente."
                    )
                    return

                time.sleep(POLL_SECONDS)
                continue

            logger.info(
                "Processando job %s",
                job["id"],
            )

            process_simulation_job(
                job=job,
                worker_id=worker_id,
            )

            if once:
                return

        except KeyboardInterrupt:
            logger.info(
                "Worker interrompido pelo usuário."
            )
            return

        except Exception:
            logger.exception(
                "Erro no ciclo do worker."
            )

            if once:
                raise

            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--once",
        action="store_true",
        help="Processa no máximo uma tarefa e encerra.",
    )

    args = parser.parse_args()

    run_worker(once=args.once)
