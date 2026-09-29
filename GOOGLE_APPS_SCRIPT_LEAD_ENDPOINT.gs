/**
 * Medlivo Web Leads - Google Apps Script endpoint
 *
 * Recommended deployment:
 * 1. Open the "Medlivo Web Leads" Google Sheet.
 * 2. Extensions -> Apps Script.
 * 3. Paste this code into Code.gs.
 * 4. In Project Settings -> Script Properties, add:
 *      LEAD_ENDPOINT_TOKEN = <long random secret>
 * 5. Deploy -> New deployment -> Web app.
 *      Execute as: Me
 *      Who has access: Anyone
 *
 * IMPORTANT:
 * Do not call this endpoint directly from public browser JavaScript with the token.
 * Put a server-side /api/medlivo-lead route in front of it and keep the token there.
 */

const CLIENT_SHEET = 'Client Leads';
const CLINICIAN_SHEET = 'Clinician Leads';

function doPost(e) {
  try {
    const body = JSON.parse((e.postData && e.postData.contents) || '{}');
    validateToken_(body.token);

    const type = String(body.type || '').trim().toLowerCase();
    const payload = body.payload || {};

    let result;
    if (type === 'client') {
      result = appendClientLead_(payload);
    } else if (type === 'clinician') {
      result = appendClinicianLead_(payload);
    } else {
      throw new Error('Invalid lead type. Use "client" or "clinician".');
    }

    return json_({ ok: true, ...result });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message ? err.message : err) });
  }
}

function appendClientLead_(p) {
  const sheet = getSheet_(CLIENT_SHEET);
  const now = new Date();
  const leadId = createLeadId_('CL');

  const row = [
    leadId,
    now,
    clean_(p.organization),
    clean_(p.contactName),
    clean_(p.email),
    clean_(p.phone),
    clean_(p.division),
    clean_(p.roleSpecialty || p.role),
    clean_(p.location),
    clean_(p.startTiming || p.start),
    numberOrBlank_(p.numberNeeded || p.count),
    clean_(p.notes),
    clean_(p.source || 'Ask Medlivo'),
    clean_(p.status || 'New'),
    clean_(p.assignedTeam),
    now
  ];

  sheet.appendRow(row);
  return { leadId, sheet: CLIENT_SHEET };
}

function appendClinicianLead_(p) {
  const sheet = getSheet_(CLINICIAN_SHEET);
  const now = new Date();
  const leadId = createLeadId_('CN');

  const row = [
    leadId,
    now,
    clean_(p.name),
    clean_(p.email),
    clean_(p.phone),
    clean_(p.division),
    clean_(p.profession),
    clean_(p.specialty),
    clean_(p.preferredLocations || p.location),
    clean_(p.travelLocal),
    clean_(p.availability),
    clean_(p.resumeLink),
    clean_(p.source || 'Ask Medlivo'),
    clean_(p.status || 'New'),
    clean_(p.assignedRecruiter),
    now
  ];

  sheet.appendRow(row);
  return { leadId, sheet: CLINICIAN_SHEET };
}

function getSheet_(name) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(name);
  if (!sheet) throw new Error('Missing sheet: ' + name);
  return sheet;
}

function validateToken_(token) {
  const expected = PropertiesService.getScriptProperties().getProperty('LEAD_ENDPOINT_TOKEN');
  if (!expected) throw new Error('LEAD_ENDPOINT_TOKEN is not configured.');
  if (!token || token !== expected) throw new Error('Unauthorized.');
}

function createLeadId_(prefix) {
  const stamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd-HHmmss');
  const suffix = Utilities.getUuid().slice(0, 6).toUpperCase();
  return prefix + '-' + stamp + '-' + suffix;
}

function clean_(value) {
  if (value === null || value === undefined) return '';
  return String(value).trim().slice(0, 5000);
}

function numberOrBlank_(value) {
  if (value === null || value === undefined || value === '') return '';
  const n = Number(value);
  return Number.isFinite(n) ? n : clean_(value);
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Optional health check for the Apps Script editor.
 */
function testClientLead() {
  const result = appendClientLead_({
    organization: 'Test Facility',
    contactName: 'Test Contact',
    email: 'test@example.com',
    phone: '555-555-5555',
    division: 'Rehabilitation',
    roleSpecialty: 'Physical Therapist',
    location: 'Seattle, WA',
    startTiming: 'ASAP',
    numberNeeded: 2,
    notes: 'Test lead from Apps Script editor',
    source: 'Manual Test'
  });
  Logger.log(result);
}
