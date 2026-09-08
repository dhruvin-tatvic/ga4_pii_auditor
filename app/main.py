from flask import Flask, jsonify, request
from flask_cors import CORS
from app.services.orchestrator import run_audit, run_single_audit, run_mass_audit

app = Flask(__name__)
CORS(app)

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

@app.route("/api/audit/single", methods=["POST"])
def trigger_single_audit():
    try:
        payload = request.json
        if not payload:
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400
        message, status_code = run_single_audit(payload)
        if status_code != 200:
            return jsonify({"status": "error", "message": message}), status_code
        return jsonify({"status": "success", "message": message})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/audit/mass", methods=["POST"])
def trigger_mass_audit():
    try:
        payload = request.json
        if not payload:
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400
        message, status_code = run_mass_audit(payload)
        if status_code != 200:
            return jsonify({"status": "error", "message": message}), status_code
        return jsonify({"status": "success", "message": message})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/properties", methods=["GET"])
def get_properties():
    access_email = request.args.get("access_email")
    if not access_email:
        return jsonify({"status": "error", "message": "Missing access_email"}), 400
    try:
        from app.services.ga4_client import GA4Client
        client = GA4Client(access_email)
        props = client.get_properties_list()
        return jsonify({"status": "success", "properties": props})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
