import logging
import sys
import time
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from app.services.orchestrator import run_audit, run_single_audit, run_mass_audit

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ga4_backend")
logger.setLevel(logging.INFO)

app = Flask(__name__)
CORS(app)

@app.before_request
def log_request_info():
    g.start_time = time.time()
    query_str = f"?{request.query_string.decode('utf-8')}" if request.query_string else ""
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    
    payload_info = ""
    if request.is_json:
        try:
            body = request.get_json(silent=True)
            if body:
                payload_str = str(body)
                if len(payload_str) > 300:
                    payload_str = payload_str[:300] + "... (truncated)"
                payload_info = f" | Payload: {payload_str}"
        except Exception:
            pass

    logger.info(f"➡️  [REQUEST] {request.method} {request.path}{query_str} from {client_ip}{payload_info}")

@app.after_request
def log_response_info(response):
    start_time = getattr(g, "start_time", None)
    duration_str = f" in {(time.time() - start_time) * 1000:.1f}ms" if start_time else ""
    query_str = f"?{request.query_string.decode('utf-8')}" if request.query_string else ""
    
    if response.status_code >= 500:
        level = logging.ERROR
        icon = "❌"
    elif response.status_code >= 400:
        level = logging.WARNING
        icon = "⚠️"
    else:
        level = logging.INFO
        icon = "✅"
        
    logger.log(
        level,
        f"{icon} [RESPONSE] {request.method} {request.path}{query_str} -> {response.status_code}{duration_str}"
    )
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    query_str = f"?{request.query_string.decode('utf-8')}" if request.query_string else ""
    logger.exception(f"💥 [ERROR] Unhandled exception on {request.method} {request.path}{query_str}: {str(e)}")
    return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "service": "GA4 PII Auditor"})

@app.route("/api/audit", methods=["POST"])
def trigger_audit():
    logger.info("Starting complete audit run...")
    try:
        message, status_code = run_audit()
        if status_code != 200:
            logger.warning(f"Audit completed with error status {status_code}: {message}")
            return jsonify({"status": "error", "message": message}), status_code
        logger.info(f"Audit completed successfully: {message}")
        return jsonify({"status": "success", "message": message})
    except Exception as e:
        logger.exception(f"Failed during full audit execution: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/audit/scheduled", methods=["POST"])
def trigger_scheduled_audit():
    try:
        import threading
        logger.info("Spawning background thread for scheduled audit (last week)...")
        thread = threading.Thread(target=run_audit, kwargs={"force_last_week": True})
        thread.start()
        return jsonify({"status": "success", "message": "Audit started in the background"}), 202
    except Exception as e:
        logger.exception(f"Failed to start scheduled audit background thread: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/audit/single", methods=["POST"])
def trigger_single_audit():
    try:
        payload = request.json
        if not payload:
            logger.warning("Single audit triggered without JSON payload")
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400
        
        prop_id = payload.get("property_id", "Unknown")
        client_name = payload.get("client_name", "Unknown")
        logger.info(f"Running single audit for Property ID: {prop_id} (Client: {client_name})")
        
        message, status_code = run_single_audit(payload)
        if status_code != 200:
            logger.warning(f"Single audit failed with status {status_code}: {message}")
            return jsonify({"status": "error", "message": message}), status_code
            
        logger.info(f"Single audit succeeded for Property ID: {prop_id}")
        return jsonify({"status": "success", "message": message})
    except Exception as e:
        logger.exception(f"Exception during single audit execution: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/audit/mass", methods=["POST"])
def trigger_mass_audit():
    try:
        payload = request.json
        if not payload:
            logger.warning("Mass audit triggered without JSON payload")
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400
            
        audits_count = len(payload) if isinstance(payload, list) else len(payload.get("audits", [])) if isinstance(payload, dict) else "?"
        logger.info(f"Triggering mass audit for {audits_count} properties...")
        
        message, status_code = run_mass_audit(payload)
        if status_code != 200:
            logger.warning(f"Mass audit completed with status {status_code}: {message}")
            return jsonify({"status": "error", "message": message}), status_code
            
        logger.info(f"Mass audit completed successfully: {message}")
        return jsonify({"status": "success", "message": message})
    except Exception as e:
        logger.exception(f"Exception during mass audit execution: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/properties", methods=["GET"])
def get_properties():
    access_email = request.args.get("access_email")
    if not access_email:
        logger.warning("Missing access_email parameter in GET /api/properties")
        return jsonify({"status": "error", "message": "Missing access_email"}), 400
    try:
        from app.services.ga4_client import GA4Client
        logger.info(f"Fetching properties list from GA4 for access_email='{access_email}'...")
        client = GA4Client(access_email)
        props = client.get_properties_list()
        logger.info(f"Successfully retrieved {len(props)} GA4 properties for '{access_email}'")
        return jsonify({"status": "success", "properties": props})
    except Exception as e:
        logger.exception(f"Error fetching GA4 properties for '{access_email}': {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/client-list", methods=["GET"])
def get_client_list():
    try:
        from app.services.sheets_client import SheetsClient
        logger.info("Fetching client list from Google Sheets...")
        clients = SheetsClient().get_client_list()
        logger.info(f"Successfully retrieved {len(clients)} clients from Google Sheets")
        return jsonify({"status": "success", "clients": clients})
    except Exception as e:
        logger.exception(f"Error fetching client list from Google Sheets: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
