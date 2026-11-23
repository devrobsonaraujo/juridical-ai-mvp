
import uuid

import pytest

from app.services.processing_job_service import (
    _validate_attempt_token,
    _validate_lease_seconds,
    claim_next_processing_job,
    complete_processing_job,
    recover_expired_processing_jobs,
    renew_processing_job_lease,
    update_processing_job_progress,
)


def new_uuid():
    return str(uuid.uuid4())


def test_valid_attempt_token():
    token = new_uuid()
    assert _validate_attempt_token(token) == token


def test_invalid_attempt_token():
    with pytest.raises(ValueError, match="UUID válido"):
        _validate_attempt_token("invalid")


def test_missing_attempt_token():
    with pytest.raises(ValueError, match="UUID válido"):
        _validate_attempt_token(None)


def test_invalid_lease_seconds():
    with pytest.raises(ValueError, match="lease_seconds"):
        _validate_lease_seconds(10)


def test_valid_lease_seconds():
    assert _validate_lease_seconds(300) == 300


def test_claim_rejects_invalid_source():
    with pytest.raises(ValueError, match="source_type"):
        claim_next_processing_job(
            worker_id="worker-test",
            source_type="invalid",
        )


def test_renew_rejects_invalid_token():
    with pytest.raises(ValueError, match="UUID válido"):
        renew_processing_job_lease(
            job_id=new_uuid(),
            worker_id="worker-test",
            attempt_token="invalid",
        )


def test_progress_rejects_100():
    with pytest.raises(ValueError, match="entre 0 e 99"):
        update_processing_job_progress(
            job_id=new_uuid(),
            worker_id="worker-test",
            attempt_token=new_uuid(),
            progress=100,
        )


def test_progress_rejects_negative():
    with pytest.raises(ValueError, match="entre 0 e 99"):
        update_processing_job_progress(
            job_id=new_uuid(),
            worker_id="worker-test",
            attempt_token=new_uuid(),
            progress=-1,
        )


def test_completion_requires_attempt_token():
    with pytest.raises(ValueError, match="UUID válido"):
        complete_processing_job(
            job_id=new_uuid(),
            worker_id="worker-test",
        )


def test_recovery_rejects_invalid_limit():
    with pytest.raises(ValueError, match="limit"):
        recover_expired_processing_jobs(limit=0)
