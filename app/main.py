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

@app.route("/api/audit/scheduled", methods=["POST"])
def trigger_scheduled_audit():
    try:
        # Runs the audit forcing the date range to last Sunday-Saturday in a background thread
        # This prevents Cloud Run from timing out the HTTP request
        import threading
        thread = threading.Thread(target=run_audit, kwargs={"force_last_week": True})
        thread.start()
        return jsonify({"status": "success", "message": "Audit started in the background"}), 202
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

@app.route("/api/client-list", methods=["GET"])
def get_client_list():
    try:
        from app.services.sheets_client import SheetsClient
        clients = SheetsClient().get_client_list()
        return jsonify({"status": "success", "clients": clients})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
