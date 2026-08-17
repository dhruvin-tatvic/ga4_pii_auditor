from flask import Flask, jsonify
from app.services.orchestrator import run_audit

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "service": "GA4 PII Auditor"})

@app.route("/api/audit", methods=["POST"])
def trigger_audit():
    try:
        message, status_code = run_audit()
        if status_code != 200:
            return jsonify({"status": "error", "message": message}), status_code
        return jsonify({"status": "success", "message": message})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
