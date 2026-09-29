# Ask Medlivo Agent Integration

## Purpose
Ask Medlivo is the homepage visitor agent for two primary conversion journeys:
1. Healthcare organizations that need staff.
2. Clinicians looking for jobs.

The frontend is already implemented in `index.html`, `assets/css/medlivo-agent.css`, and `assets/js/medlivo-agent.js`.

On GitHub Pages, the experience runs as a guided concierge with approved Medlivo knowledge and structured routing. When an AI backend is available, the same frontend will call:

`POST /api/medlivo-agent`

No redesign is required.

## Agent behavior
The production agent should:
- Identify visitor intent.
- Ask only for missing information.
- Never request or accept patient information or PHI.
- Stay within staffing, employment, company, credentialing, and workforce topics.
- Route client leads by division.
- Search live ATS inventory for clinicians.
- Offer human handoff at any point.
- Use Medlivo-approved website content as the source of truth.

## Request contract

```json
{
  "message": "We need two PTs in Orlando next month",
  "page": "/",
  "context": {
    "mode": "client",
    "data": {}
  }
}
```

## Response contract

```json
{
  "message": "I can help with that. What type of facility is this?",
  "title": "Next step",
  "actions": [
    {
      "label": "Request Staff",
      "href": "request-staff.html?division=Rehabilitation"
    }
  ]
}
```

## Recommended production tools

### search_jobs
Inputs:
- division
- profession
- specialty
- state
- city
- availability

Returns:
- job id
- title
- division
- profession
- specialty
- city
- state
- pay/rate when approved for display
- start date
- apply URL

### create_staffing_lead
Inputs:
- division
- role/specialty
- organization
- location
- start timing
- number needed
- contact name
- work email
- phone
- notes
- source = "Ask Medlivo"

### create_clinician_lead
Inputs:
- name
- profession
- specialty
- preferred locations
- availability
- email
- phone
- resume URL when supported
- source = "Ask Medlivo"

### human_handoff
Routes:
- Nursing & Allied
- Rehabilitation
- Locum Tenens
- General inquiry

Fallback contact:
- hello@medlivo.com
- +1 855-633-5486

## Privacy and safety
- Do not collect PHI.
- Do not provide medical advice.
- Do not make clinical decisions.
- Do not expose internal client, candidate, or credentialing data.
- Keep session context ephemeral unless the visitor explicitly submits a lead or application.
- Log only information required for conversion, quality, and security.

## Production architecture
Recommended:
- Homepage frontend: existing Ask Medlivo widget.
- AI endpoint: server-side API route.
- Agent: tool-calling model with Medlivo knowledge retrieval.
- Job tool: JobDiva/ATS API.
- Lead tool: CRM, ATS, or Medlivo lead service.
- Observability: conversation outcome, lead conversion, job-search conversion, handoff rate.
- Human fallback: hello@medlivo.com and division-specific routing.

## Conversion events to measure
- agent_opened
- client_intent
- clinician_intent
- general_question
- staffing_request_started
- staffing_request_completed
- job_search_started
- job_clicked
- recruiter_handoff
- contact_handoff
