import os
import time
import uuid
from datetime import datetime, timezone
from collections import defaultdict, deque

from flask import Flask, jsonify, request
from flask_cors import CORS
from google.auth import default as google_auth_default
from googleapiclient.discovery import build
from openai import OpenAI

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024

ALLOWED_ORIGINS = {
    "https://www.medlivo.com",
    "https://medlivo.com",
    "https://pks-alt.github.io",
}
CORS(app, resources={r"/api/*": {"origins": list(ALLOWED_ORIGINS)}})

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1gqhLy5RnmpNM33HE_4JvecO7lKfZEDiVgrLDzEUa_ac")
MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "30"))

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
_rate = defaultdict(deque)

SYSTEM_PROMPT = """You are Ask Medlivo, the website assistant for Medlivo Inc, a healthcare staffing company.

Primary goals:
1. Help healthcare organizations reach the right Medlivo staffing team.
2. Help healthcare professionals find relevant Medlivo jobs and recruiter support.
3. Answer concise factual questions about Medlivo using only the approved context below.

Medlivo practices:
- Nursing & Allied
- Rehabilitation
- Locum Tenens

Operating rules:
- Do not provide medical advice, diagnosis, treatment guidance, or clinical decision-making.
- Do not ask for or accept patient information or PHI.
- Do not invent jobs, rates, credentials, client names, policies, or capabilities.
- When the visitor needs staff, collect only missing business details: division, role/specialty, organization, location, start timing, number needed, contact name, work email, phone, notes.
- When the visitor is a clinician, collect only missing career details: profession, specialty, preferred locations, travel/local preference, availability, name, email, phone.
- Keep responses short, human, direct, and helpful.
- Prefer one useful next step over long explanations.
- Human fallback: hello@medlivo.com or +1 855-633-5486.

Approved Medlivo context:
Medlivo supports healthcare organizations and clinicians across Nursing & Allied, Rehabilitation, and Locum Tenens. Medlivo emphasizes clinical understanding, operational discipline, clear ownership, credentialing/compliance coordination, assignment readiness, and practical use of technology.
"""

def _origin_allowed():
    origin = request.headers.get("Origin")
    return not origin or origin in ALLOWED_ORIGINS

def _client_key():
    forwarded = request.headers.get("X-Forwarded-For", "")
    return (forwarded.split(",")[0].strip() or request.remote_addr or "unknown")[:80]

def _rate_limited():
    now = time.time()
    bucket = _rate[_client_key()]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    if len(bucket) >= MAX_REQUESTS_PER_MINUTE:
        return True
    bucket.append(now)
    return False

def _sheets():
    credentials, _ = google_auth_default(scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)

def _append_row(tab_name, values):
    service = _sheets()
    service.spreadsheets().values().append(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"'{tab_name}'!A:P",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [values]},
    ).execute()

def _lead_id(prefix):
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

@app.before_request
def protect_api():
    if not request.path.startswith("/api/"):
        return None
    if not _origin_allowed():
        return jsonify({"error": "origin_not_allowed"}), 403
    if _rate_limited():
        return jsonify({"error": "rate_limited"}), 429
    return None

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "medlivo-ai-agent"})

@app.post("/api/medlivo-agent")
def medlivo_agent():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    context = data.get("context") or {}
    if not message:
        return jsonify({"error": "message_required"}), 400
    if len(message) > 2000:
        return jsonify({"error": "message_too_long"}), 400
    if not openai_client:
        return jsonify({
            "message": "I can help with staffing requests, healthcare jobs, Medlivo services, and recruiter support.",
            "actions": [
                {"label": "Request Staff", "href": "request-staff.html"},
                {"label": "Search Jobs", "href": "search-jobs.html"},
                {"label": "Contact Medlivo", "href": "contact.html"},
            ],
        })

    prompt = f"""Visitor message:
{message}

Current page: {data.get('page', '/')}
Current journey context: {context}

Reply in 1-4 short sentences. If a next step is useful, mention it naturally. Do not output HTML."""
    response = openai_client.responses.create(
        model=OPENAI_MODEL,
        instructions=SYSTEM_PROMPT,
        input=prompt,
        store=False,
    )
    return jsonify({"message": response.output_text.strip()})

@app.post("/api/leads/client")
def create_client_lead():
    d = request.get_json(silent=True) or {}
    required = ["organization", "contactName", "workEmail", "role", "location"]
    missing = [k for k in required if not str(d.get(k, "")).strip()]
    if missing:
        return jsonify({"error": "missing_fields", "fields": missing}), 400

    lead_id = _lead_id("CL")
    now = _now_iso()
    row = [
        lead_id,
        now,
        str(d.get("organization", "")).strip(),
        str(d.get("contactName", "")).strip(),
        str(d.get("workEmail", "")).strip(),
        str(d.get("phone", "")).strip(),
        str(d.get("division", "")).strip(),
        str(d.get("role", "")).strip(),
        str(d.get("location", "")).strip(),
        str(d.get("startTiming", "")).strip(),
        str(d.get("numberNeeded", "")).strip(),
        str(d.get("notes", "")).strip(),
        str(d.get("source", "Ask Medlivo")).strip(),
        "New",
        str(d.get("assignedTeam", "")).strip(),
        now,
    ]
    _append_row("Client Leads", row)
    return jsonify({"ok": True, "leadId": lead_id})

@app.post("/api/leads/clinician")
def create_clinician_lead():
    d = request.get_json(silent=True) or {}
    required = ["name", "email", "profession"]
    missing = [k for k in required if not str(d.get(k, "")).strip()]
    if missing:
        return jsonify({"error": "missing_fields", "fields": missing}), 400

    lead_id = _lead_id("CN")
    now = _now_iso()
    row = [
        lead_id,
        now,
        str(d.get("name", "")).strip(),
        str(d.get("email", "")).strip(),
        str(d.get("phone", "")).strip(),
        str(d.get("division", "")).strip(),
        str(d.get("profession", "")).strip(),
        str(d.get("specialty", "")).strip(),
        str(d.get("preferredLocations", "")).strip(),
        str(d.get("travelLocal", "")).strip(),
        str(d.get("availability", "")).strip(),
        str(d.get("resumeLink", "")).strip(),
        str(d.get("source", "Ask Medlivo")).strip(),
        "New",
        str(d.get("assignedRecruiter", "")).strip(),
        now,
    ]
    _append_row("Clinician Leads", row)
    return jsonify({"ok": True, "leadId": lead_id})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
