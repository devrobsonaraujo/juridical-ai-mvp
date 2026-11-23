
import uuid

import pytest

from app.services.processing_job_service import (
    _validate_uuid,
    _validate_worker_id,
    create_processing_job,
    get_processing_job,
    list_processing_jobs,
    claim_next_processing_job,
    complete_processing_job,
)


def test_accepts_valid_uuid():
    value = str(uuid.uuid4())

    assert _validate_uuid(value, "id") == value


def test_rejects_invalid_uuid():
    with pytest.raises(ValueError, match="UUID válido"):
        _validate_uuid("usuario-invalido", "id")


def test_rejects_empty_worker_id():
    with pytest.raises(ValueError, match="obrigatório"):
        _validate_worker_id("")


def test_rejects_invalid_source_type():
    with pytest.raises(ValueError, match="source_type"):
        create_processing_job(
            owner_user_id=str(uuid.uuid4()),
            source_type="unknown",
        )


def test_media_job_requires_storage_path():
    with pytest.raises(ValueError, match="storage_path"):
        create_processing_job(
            owner_user_id=str(uuid.uuid4()),
            source_type="media",
        )


def test_rejects_invalid_history_limit():
    with pytest.raises(ValueError, match="limit"):
        list_processing_jobs(
            owner_user_id=str(uuid.uuid4()),
            limit=101,
        )


def test_rejects_invalid_lease():
    with pytest.raises(ValueError, match="lease_seconds"):
        claim_next_processing_job(
            worker_id="worker-test",
            lease_seconds=10,
        )


def test_rejects_invalid_job_id():
    with pytest.raises(ValueError, match="UUID válido"):
        get_processing_job(
            job_id="invalid",
            owner_user_id=str(uuid.uuid4()),
        )


def test_completion_rejects_invalid_media_id():
    with pytest.raises(ValueError, match="UUID válido"):
        complete_processing_job(
            job_id=str(uuid.uuid4()),
            worker_id="worker-test",
            media_id="invalid",
        )
