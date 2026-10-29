import copy

import pytest

import app as playlist_app


@pytest.fixture
def client():
    original = copy.deepcopy(playlist_app.PLAYLISTS)
    yield playlist_app.app.test_client()
    playlist_app.PLAYLISTS[:] = original


def test_health(client):
    assert client.get('/health').status_code == 200


def test_list_playlists(client):
    res = client.get('/playlists')
    assert res.status_code == 200
    assert res.get_json()["playlists"][0]["name"] == "Boss Fights"


def test_create_playlist(client):
    res = client.post('/playlists', json={"name": "Chill"})
    assert res.status_code == 201
    assert res.get_json()["playlist"] == {"id": 2, "name": "Chill", "track_ids": []}


def test_create_playlist_requires_name(client):
    assert client.post('/playlists', json={}).status_code == 400


def test_add_and_remove_track(client):
    res = client.post('/playlists/1/tracks', json={"track_id": 1})
    assert res.get_json()["playlist"]["track_ids"] == [3, 1]
    res = client.delete('/playlists/1/tracks/3')
    assert res.get_json()["playlist"]["track_ids"] == [1]


def test_playlist_not_found(client):
    assert client.get('/playlists/999').status_code == 404
