from flask import Flask, jsonify, request

app = Flask(__name__)

# Estado de reprodução simulado (em memória)
STATE = {"track_id": None, "status": "stopped"}

def current_state():
    return jsonify({"status": "success", "playback": STATE}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "playback_service"}), 200

@app.route('/playback/status', methods=['GET'])
def get_status():
    return current_state()

@app.route('/playback/play', methods=['POST'])
def play():
    data = request.get_json(silent=True) or {}
    track_id = data.get("track_id")
    if not isinstance(track_id, int):
        return jsonify({"status": "error", "message": "Campo 'track_id' (inteiro) é obrigatório"}), 400
    STATE.update(track_id=track_id, status="playing")
    return current_state()

@app.route('/playback/pause', methods=['POST'])
def pause():
    if STATE["status"] != "playing":
        return jsonify({"status": "error", "message": "Nenhuma música tocando"}), 409
    STATE["status"] = "paused"
    return current_state()

@app.route('/playback/resume', methods=['POST'])
def resume():
    if STATE["status"] != "paused":
        return jsonify({"status": "error", "message": "Nenhuma música pausada"}), 409
    STATE["status"] = "playing"
    return current_state()

@app.route('/playback/stop', methods=['POST'])
def stop():
    STATE.update(track_id=None, status="stopped")
    return current_state()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
