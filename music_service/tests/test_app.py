import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()


def test_health(client):
    assert client.get('/health').status_code == 200


def test_list_music(client):
    res = client.get('/music')
    assert res.status_code == 200
    assert len(res.get_json()["tracks"]) == 3


def test_get_music_by_id(client):
    res = client.get('/music/2')
    assert res.status_code == 200
    assert res.get_json()["track"]["game"] == "The Witcher 3"


def test_music_not_found(client):
    assert client.get('/music/999').status_code == 404
