import os
import time
import uuid
from datetime import datetime, timezone
from collections import defaultdict, deque
from urllib.parse import urlencode, quote
from urllib.request import Request as URLRequest, urlopen
from urllib.error import HTTPError, URLError

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
CAREER_API_BASE_URL = os.getenv("CAREER_API_BASE_URL", "").rstrip("/")

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

def _clean(value, limit=500):
    return str(value or "").strip()[:limit]

def _valid_email(value):
    value = _clean(value, 254)
    return "@" in value and "." in value.split("@")[-1] and " " not in value

def _client_team(division):
    return {
        "Nursing & Allied": "Nursing & Allied Team",
        "Rehabilitation": "Rehabilitation Team",
        "Locum Tenens": "Locum Tenens Team",
    }.get(_clean(division), "Medlivo Intake")

def _clinician_team(division):
    return {
        "Nursing & Allied": "Nursing & Allied Recruiting",
        "Rehabilitation": "Rehabilitation Recruiting",
        "Locum Tenens": "Locum Tenens Recruiting",
    }.get(_clean(division), "Medlivo Recruiting")

def _client_summary(d):
    parts = [
        _clean(d.get("role")),
        f"in {_clean(d.get('location'))}" if _clean(d.get("location")) else "",
        f"starting {_clean(d.get('startTiming'))}" if _clean(d.get("startTiming")) else "",
        f"{_clean(d.get('numberNeeded'))} needed" if _clean(d.get("numberNeeded")) else "",
    ]
    return " | ".join([p for p in parts if p])

def _clinician_summary(d):
    parts = [
        _clean(d.get("profession")),
        _clean(d.get("specialty")),
        _clean(d.get("preferredLocations")),
        _clean(d.get("travelLocal")),
        f"available {_clean(d.get('availability'))}" if _clean(d.get("availability")) else "",
    ]
    return " | ".join([p for p in parts if p])

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

def _career_api(path, params=None):
    if not CAREER_API_BASE_URL:
        return None, 503
    url = CAREER_API_BASE_URL + path
    if params:
        clean_params = {k: v for k, v in params.items() if v not in (None, "")}
        if clean_params:
            url += "?" + urlencode(clean_params)
    req = URLRequest(url, headers={
        "Accept": "application/json",
        "User-Agent": "Medlivo-Website/1.0",
    }, method="GET")
    try:
        with urlopen(req, timeout=8) as response:
            payload = response.read(1024 * 1024)
            return payload, response.status
    except HTTPError as exc:
        if exc.code == 404:
            return b'{"detail":"Job not found"}', 404
        return None, 503
    except (URLError, TimeoutError):
        return None, 503


@app.get("/api/careers/jobs")
def career_jobs():
    allowed = {"division", "profession", "specialty", "state", "city", "after", "limit"}
    params = {key: request.args.get(key, "") for key in allowed}
    payload, status = _career_api("/api/v1/careers/jobs", params)
    if status != 200 or payload is None:
        return jsonify({"error": "career_jobs_unavailable"}), status
    response = app.response_class(payload, status=200, mimetype="application/json")
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.get("/api/careers/jobs/<job_id>")
def career_job(job_id):
    safe_id = _clean(job_id, 64)
    if not safe_id or any(ch not in "0123456789abcdefABCDEF-" for ch in safe_id):
        return jsonify({"detail": "Job not found"}), 404
    payload, status = _career_api("/api/v1/careers/jobs/" + quote(safe_id, safe=""))
    if status == 404:
        return jsonify({"detail": "Job not found"}), 404
    if status != 200 or payload is None:
        return jsonify({"error": "career_jobs_unavailable"}), 503
    response = app.response_class(payload, status=200, mimetype="application/json")
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.post("/api/leads/client")
def create_client_lead():
    d = request.get_json(silent=True) or {}
    required = ["organization", "contactName", "workEmail", "role", "location"]
    missing = [k for k in required if not _clean(d.get(k))]
    if missing:
        return jsonify({"error": "missing_fields", "fields": missing}), 400
    if not _valid_email(d.get("workEmail")):
        return jsonify({"error": "invalid_email"}), 400

    lead_id = _lead_id("CL")
    now = _now_iso()
    summary = _client_summary(d)
    notes = _clean(d.get("notes"), 1200)
    notes_value = f"Lead summary: {summary}" + (f"\nNotes: {notes}" if notes else "")
    assigned_team = _clean(d.get("assignedTeam")) or _client_team(d.get("division"))

    row = [
        lead_id,
        now,
        _clean(d.get("organization")),
        _clean(d.get("contactName")),
        _clean(d.get("workEmail"), 254),
        _clean(d.get("phone"), 50),
        _clean(d.get("division")),
        _clean(d.get("role")),
        _clean(d.get("location")),
        _clean(d.get("startTiming")),
        _clean(d.get("numberNeeded"), 50),
        notes_value[:1500],
        _clean(d.get("source", "Ask Medlivo")),
        "New",
        assigned_team,
        now,
    ]
    _append_row("Client Leads", row)
    return jsonify({"ok": True, "leadId": lead_id, "assignedTeam": assigned_team, "summary": summary})

@app.post("/api/leads/clinician")
def create_clinician_lead():
    d = request.get_json(silent=True) or {}
    required = ["name", "email", "profession"]
    missing = [k for k in required if not _clean(d.get(k))]
    if missing:
        return jsonify({"error": "missing_fields", "fields": missing}), 400
    if not _valid_email(d.get("email")):
        return jsonify({"error": "invalid_email"}), 400

    lead_id = _lead_id("CN")
    now = _now_iso()
    assigned_recruiter = _clean(d.get("assignedRecruiter")) or _clinician_team(d.get("division"))
    summary = _clinician_summary(d)

    row = [
        lead_id,
        now,
        _clean(d.get("name")),
        _clean(d.get("email"), 254),
        _clean(d.get("phone"), 50),
        _clean(d.get("division")),
        _clean(d.get("profession")),
        _clean(d.get("specialty")),
        _clean(d.get("preferredLocations")),
        _clean(d.get("travelLocal")),
        _clean(d.get("availability")),
        _clean(d.get("resumeLink"), 1000),
        _clean(d.get("source", "Ask Medlivo")),
        "New",
        assigned_recruiter,
        now,
    ]
    _append_row("Clinician Leads", row)
    return jsonify({"ok": True, "leadId": lead_id, "assignedRecruiter": assigned_recruiter, "summary": summary})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
