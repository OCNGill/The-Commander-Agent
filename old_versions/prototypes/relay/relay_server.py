from flask import Flask, request
import requests
import datetime

app = Flask(__name__)

# Explicit list of agent inbox endpoints (your real cluster)
AGENTS = [
    "http://10.0.0.93:8002/inbox",   # Laptop
    "http://10.0.0.139:8003/inbox",  # Steam Deck
    "http://10.0.0.164:8000/inbox",  # Main
    "http://10.0.0.42:8001/inbox",   # HTPC (self)
]

@app.route('/send', methods=['POST'])
def relay():
    msg = request.json
    timestamp = datetime.datetime.now().isoformat()

    print(f"[{timestamp}] RELAY RECEIVED: {msg}")

    # Forward to all agents
    for agent in AGENTS:
        try:
            requests.post(agent, json=msg, timeout=1)
        except Exception as e:
            print(f"FAILED to send to {agent}: {e}")

    return {"status": "relayed", "timestamp": timestamp}

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6000)
