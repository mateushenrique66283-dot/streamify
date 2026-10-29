import pytest

import app as playback_app


@pytest.fixture
def client():
    playback_app.STATE.update(track_id=None, status="stopped")
    return playback_app.app.test_client()


def test_health(client):
    assert client.get('/health').status_code == 200


def test_play_pause_resume_stop(client):
    res = client.post('/playback/play', json={"track_id": 2})
    assert res.get_json()["playback"] == {"track_id": 2, "status": "playing"}
    assert client.post('/playback/pause').get_json()["playback"]["status"] == "paused"
    assert client.post('/playback/resume').get_json()["playback"]["status"] == "playing"
    res = client.post('/playback/stop')
    assert res.get_json()["playback"] == {"track_id": None, "status": "stopped"}


def test_play_requires_track_id(client):
    assert client.post('/playback/play', json={}).status_code == 400


def test_pause_when_stopped(client):
    assert client.post('/playback/pause').status_code == 409
