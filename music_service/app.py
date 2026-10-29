from flask import Flask, jsonify

app = Flask(__name__)

# Banco de dados simulado (Trilhas Sonoras de Games)
TRACKS = [
    {"id": 1, "title": "Cyberpunk Night", "game": "Cyberpunk 2077", "duration": "3:45", "url": "/stream/1"},
    {"id": 2, "title": "The Fields of Ard Skellig", "game": "The Witcher 3", "duration": "6:10", "url": "/stream/2"},
    {"id": 3, "title": "Rip & Tear", "game": "DOOM Eternal", "duration": "4:12", "url": "/stream/3"}
]

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "music_service"}), 200

@app.route('/music', methods=['GET'])
def get_all_music():
    return jsonify({"status": "success", "tracks": TRACKS}), 200

@app.route('/music/<int:track_id>', methods=['GET'])
def get_music_by_id(track_id):
    track = next((t for t in TRACKS if t["id"] == track_id), None)
    if track:
        return jsonify({"status": "success", "track": track}), 200
    return jsonify({"status": "error", "message": "Música não encontrada"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
