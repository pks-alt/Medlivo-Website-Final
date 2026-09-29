# Medlivo Google Sheets Lead Storage

## Google Sheet

**Title:** Medlivo Web Leads

Spreadsheet ID:
`1baJdkUHUpShgUdIt43GJ9ezK_5raxl1cU6qsr42umWM`

Tabs:
- Client Leads
- Clinician Leads

## Recommended architecture

Do not send the Apps Script secret from browser JavaScript.

Use:

`Ask Medlivo -> /api/medlivo-lead -> Apps Script -> Google Sheet`

The server-side API keeps the Apps Script token private.

## Client lead payload

```json
{
  "type": "client",
  "payload": {
    "organization": "ABC Health",
    "contactName": "Jane Smith",
    "email": "jane@abchealth.org",
    "phone": "555-555-1212",
    "division": "Rehabilitation",
    "roleSpecialty": "Physical Therapist",
    "location": "Orlando, FL",
    "startTiming": "Next month",
    "numberNeeded": 2,
    "notes": "Outpatient coverage",
    "source": "Ask Medlivo"
  }
}
```

## Clinician lead payload

```json
{
  "type": "clinician",
  "payload": {
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "555-555-1212",
    "division": "Nursing & Allied",
    "profession": "Registered Nurse",
    "specialty": "ICU",
    "preferredLocations": "Washington",
    "travelLocal": "Travel",
    "availability": "October 15",
    "resumeLink": "",
    "source": "Ask Medlivo"
  }
}
```

## Production note

Google Sheets is a temporary lead store. Keep the field names stable so the same payload can later write to JobDiva, CRM, or a database without changing the Ask Medlivo UI.
