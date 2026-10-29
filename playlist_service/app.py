from flask import Flask, jsonify, request

app = Flask(__name__)

# Banco de dados simulado (em memória)
PLAYLISTS = [
    {"id": 1, "name": "Boss Fights", "track_ids": [3]},
]

def find_playlist(playlist_id):
    return next((p for p in PLAYLISTS if p["id"] == playlist_id), None)

def not_found():
    return jsonify({"status": "error", "message": "Playlist não encontrada"}), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "playlist_service"}), 200

@app.route('/playlists', methods=['GET'])
def get_all_playlists():
    return jsonify({"status": "success", "playlists": PLAYLISTS}), 200

@app.route('/playlists/<int:playlist_id>', methods=['GET'])
def get_playlist(playlist_id):
    playlist = find_playlist(playlist_id)
    if playlist:
        return jsonify({"status": "success", "playlist": playlist}), 200
    return not_found()

@app.route('/playlists', methods=['POST'])
def create_playlist():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name:
        return jsonify({"status": "error", "message": "Campo 'name' é obrigatório"}), 400
    new_id = max((p["id"] for p in PLAYLISTS), default=0) + 1
    playlist = {"id": new_id, "name": name, "track_ids": []}
    PLAYLISTS.append(playlist)
    return jsonify({"status": "success", "playlist": playlist}), 201

@app.route('/playlists/<int:playlist_id>/tracks', methods=['POST'])
def add_track(playlist_id):
    playlist = find_playlist(playlist_id)
    if not playlist:
        return not_found()
    data = request.get_json(silent=True) or {}
    track_id = data.get("track_id")
    if not isinstance(track_id, int):
        return jsonify({"status": "error", "message": "Campo 'track_id' (inteiro) é obrigatório"}), 400
    if track_id not in playlist["track_ids"]:
        playlist["track_ids"].append(track_id)
    return jsonify({"status": "success", "playlist": playlist}), 200

@app.route('/playlists/<int:playlist_id>/tracks/<int:track_id>', methods=['DELETE'])
def remove_track(playlist_id, track_id):
    playlist = find_playlist(playlist_id)
    if not playlist:
        return not_found()
    if track_id not in playlist["track_ids"]:
        return jsonify({"status": "error", "message": "Música não está na playlist"}), 404
    playlist["track_ids"].remove(track_id)
    return jsonify({"status": "success", "playlist": playlist}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
