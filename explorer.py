from flask import Flask, render_template_string, jsonify
import json
import os

app = Flask(__name__)
BLOCKCHAIN_FILE = "blockchain.json"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ShadowLedger Explorer</title>
    <style>
        body { font-family: monospace; background: #0f0f0f; color: #00ff88; padding: 2em; }
        .block { border: 1px solid #00ff88; padding: 1em; margin-bottom: 1em; }
    </style>
</head>
<body>
    <h1>🔎 ShadowLedger Explorer</h1>
    {% for block in chain %}
    <div class="block">
        <strong>Block #{{ block.index }}</strong><br>
        Hash: {{ block.hash[:16] }}...<br>
        Miner: {{ block.address[:16] }}...<br>
        Reward: {{ block.reward }} SC<br>
        TX count: {{ block.txs|length }}
    </div>
    {% endfor %}
</body>
</html>
"""

@app.route("/")
def index():
    if os.path.exists(BLOCKCHAIN_FILE):
        with open(BLOCKCHAIN_FILE, "r") as f:
            chain = json.load(f)
    else:
        chain = []
    return render_template_string(open("explorer_template.html").read(), chain=chain)

@app.route("/api/chain")
def api_chain():
    if os.path.exists(BLOCKCHAIN_FILE):
        with open(BLOCKCHAIN_FILE, "r") as f:
            return jsonify(json.load(f))
    return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
