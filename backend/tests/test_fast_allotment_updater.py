"""Zero-room jobs must close the category (IsClosed/Closed), not just send
NoOfRoom=0 with the category left open - see fast_allotment_updater.py's
module docstring."""
import pytest

from app.integrations.pms.fast_allotment_updater import push_allotment, push_jobs_concurrent
from app.integrations.pms.api_client import PMSApiClient


@pytest.fixture(autouse=True)
def _fake_login(monkeypatch):
    """login() otherwise makes a real HTTP call - stub it out so these tests
    never touch the network, matching dry_run's own "no network call" intent."""
    def fake_login(self):
        self.hotel_id = 1
        self.user_id = "1"
        self._token = "fake-token"
        return self
    monkeypatch.setattr(PMSApiClient, "login", fake_login)


def test_zero_room_job_closes_the_category():
    jobs = [{
        'room_type': 'deluxe', 'label': 'Deluxe', 'checkbox_value': 'DLT',
        'start_date': '2026/10/01', 'end_date': '2026/10/03', 'number_of_rooms': 0,
    }]
    result = push_jobs_concurrent(jobs, dry_run=True, username='u', password='p')
    payload = result['results'][0]['payload']
    assert payload['IsClosed'] is True
    assert payload['Closed'] == 'X'
    assert 'closed' in payload['Remark']


def test_positive_room_job_stays_open():
    jobs = [{
        'room_type': 'deluxe', 'label': 'Deluxe', 'checkbox_value': 'DLT',
        'start_date': '2026/10/01', 'end_date': '2026/10/03', 'number_of_rooms': 5,
    }]
    result = push_jobs_concurrent(jobs, dry_run=True, username='u', password='p')
    payload = result['results'][0]['payload']
    assert payload['IsClosed'] is False
    assert payload['Closed'] == '0'
    assert 'closed' not in payload['Remark']


def test_single_call_helper_closes_on_zero_rooms():
    result = push_allotment(
        company_id=1001, room_type='DLT', start_date='2026-10-01', end_date='2026-10-03',
        number_of_rooms=0, remark='test', dry_run=True, username='u', password='p',
    )
    assert result['request_payload']['IsClosed'] is True
    assert result['request_payload']['Closed'] == 'X'


def test_single_call_helper_open_on_positive_rooms():
    result = push_allotment(
        company_id=1001, room_type='DLT', start_date='2026-10-01', end_date='2026-10-03',
        number_of_rooms=3, remark='test', dry_run=True, username='u', password='p',
    )
    assert result['request_payload']['IsClosed'] is False
    assert result['request_payload']['Closed'] == '0'


def test_on_result_streams_once_per_job_not_just_at_the_end():
    jobs = [
        {'room_type': 'deluxe', 'label': 'Deluxe', 'checkbox_value': 'DLT',
         'start_date': '2026/10/01', 'end_date': '2026/10/03', 'number_of_rooms': 5},
        {'room_type': 'premiere', 'label': 'Premiere', 'checkbox_value': 'PRKG',
         'start_date': '2026/10/01', 'end_date': '2026/10/03', 'number_of_rooms': 0},
    ]
    seen = []
    result = push_jobs_concurrent(jobs, dry_run=True, username='u', password='p', on_result=seen.append)
    assert len(seen) == len(jobs) == len(result['results'])
    assert {r['job']['room_type'] for r in seen} == {'deluxe', 'premiere'}


def _job(number_of_rooms=5):
    return {'room_type': 'deluxe', 'label': 'Deluxe', 'checkbox_value': 'DLT',
            'start_date': '2026/10/01', 'end_date': '2026/10/03', 'number_of_rooms': number_of_rooms}


def test_transient_failure_is_retried_and_can_succeed(monkeypatch):
    """A job that fails once (PMS-side transient error) then succeeds on
    retry must be reported as one final success, not a failure - this is the
    exact "PMS backend buckled under concurrency" case seen in production."""
    calls = {'n': 0}

    def flaky_save_allotment(self, **kwargs):
        calls['n'] += 1
        if calls['n'] < 2:
            return {'IsSuccess': False, 'Message': 'error occurred while sending the request'}
        return {'IsSuccess': True}
    monkeypatch.setattr(PMSApiClient, 'save_allotment', flaky_save_allotment)

    retries_seen = []
    result = push_jobs_concurrent(
        [_job()], dry_run=False, username='u', password='p',
        on_retry=lambda attempt, count, max_attempts: retries_seen.append((attempt, count, max_attempts)),
        max_retries=2, retry_delay=0,
    )
    assert result['success_count'] == 1
    assert result['results'][0]['attempts'] == 2
    assert retries_seen == [(2, 1, 3)]


def test_persistent_failure_is_reported_only_after_exhausting_retries(monkeypatch):
    def always_fail(self, **kwargs):
        return {'IsSuccess': False, 'Message': 'still broken'}
    monkeypatch.setattr(PMSApiClient, 'save_allotment', always_fail)

    result = push_jobs_concurrent([_job()], dry_run=False, username='u', password='p', max_retries=2, retry_delay=0)
    assert result['success_count'] == 0
    assert result['results'][0]['attempts'] == 3
    assert result['results'][0]['error'] == 'still broken'


def test_on_result_not_called_for_intermediate_retry_attempts(monkeypatch):
    """A job under retry must not stream a premature FAILED before its final
    outcome - on_result should fire exactly once per job, for the final try."""
    calls = {'n': 0}

    def flaky_save_allotment(self, **kwargs):
        calls['n'] += 1
        if calls['n'] < 2:
            return {'IsSuccess': False, 'Message': 'transient'}
        return {'IsSuccess': True}
    monkeypatch.setattr(PMSApiClient, 'save_allotment', flaky_save_allotment)

    seen = []
    push_jobs_concurrent(
        [_job()], dry_run=False, username='u', password='p',
        on_result=seen.append, max_retries=2, retry_delay=0,
    )
    assert len(seen) == 1
    assert seen[0]['success'] is True
