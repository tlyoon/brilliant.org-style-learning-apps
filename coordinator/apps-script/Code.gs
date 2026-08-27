const JOB_SHEET = 'Jobs';
const HEADERS = [
  'project_name', 'job_key', 'drive_file_id', 'source_version', 'subchapter_id', 'relative_path',
  'status', 'worker_id', 'lease_expires_at', 'heartbeat_at', 'attempt_count',
  'branch', 'pr_url', 'error_code', 'error_message', 'updated_at'
];

function doPost(e) {
  try {
    const request = JSON.parse(e.postData.contents || '{}');
    requireToken_(request.token);
    requireProject_(request.project_name);
    const result = dispatch_(request);
    return json_({ok: true, ...result});
  } catch (error) {
    const code = error.code || 'COORDINATOR_ERROR';
    return json_({ok: false, code: code, error: String(error.message || error)});
  }
}

function dispatch_(request) {
  switch (request.action) {
    case 'health': return withLock_(() => health_(request));
    case 'claim': return withLock_(() => claim_(request));
    case 'heartbeat': return withLock_(() => heartbeat_(request));
    case 'review_pending': return withLock_(() => updateStatus_(request, 'review_pending'));
    case 'failed': return withLock_(() => fail_(request));
    case 'completed': return withLock_(() => complete_(request));
    default: throw coded_('INVALID_ACTION', 'Unsupported coordinator action');
  }
}

function health_(request) {
  sheet_();
  return {status: 'ok', project_name: request.project_name};
}

function requireToken_(provided) {
  const expected = PropertiesService.getScriptProperties().getProperty('WORKER_TOKEN');
  if (!expected || provided !== expected) {
    throw coded_('UNAUTHORIZED', 'Coordinator token is missing or invalid');
  }
}

function requireProject_(provided) {
  const expected = PropertiesService.getScriptProperties().getProperty('PROJECT_NAME');
  if (!expected || provided !== expected) {
    throw coded_('WRONG_PROJECT', 'Coordinator project name is missing or does not match');
  }
}

function initializeCoordinator() {
  const properties = PropertiesService.getScriptProperties();
  const projectName = properties.getProperty('PROJECT_NAME');
  const spreadsheetId = properties.getProperty('JOB_SPREADSHEET_ID');
  if (!projectName) throw coded_('NOT_CONFIGURED', 'Set PROJECT_NAME before initialization');
  if (!spreadsheetId) throw coded_('NOT_CONFIGURED', 'Set JOB_SPREADSHEET_ID before initialization');
  let created = false;
  if (!properties.getProperty('WORKER_TOKEN')) {
    const material = [Utilities.getUuid(), Utilities.getUuid(), Utilities.getUuid()].join(':');
    const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, material);
    properties.setProperty('WORKER_TOKEN', Utilities.base64EncodeWebSafe(digest));
    created = true;
  }
  sheet_();
  return {project_name: projectName, worker_token_created: created};
}

function withLock_(callback) {
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    return callback();
  } finally {
    SpreadsheetApp.flush();
    lock.releaseLock();
  }
}

function sheet_() {
  const spreadsheetId = PropertiesService.getScriptProperties().getProperty('JOB_SPREADSHEET_ID');
  if (!spreadsheetId) throw coded_('NOT_CONFIGURED', 'JOB_SPREADSHEET_ID is not configured');
  const book = SpreadsheetApp.openById(spreadsheetId);
  let sheet = book.getSheetByName(JOB_SHEET);
  if (!sheet) sheet = book.insertSheet(JOB_SHEET);
  if (sheet.getLastRow() === 0) sheet.appendRow(HEADERS);
  const actual = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  if (actual.join('|') !== HEADERS.join('|')) {
    throw coded_('INVALID_LEDGER', 'Jobs sheet headers do not match the coordinator contract');
  }
  return sheet;
}

function rows_(sheet) {
  if (sheet.getLastRow() < 2) return [];
  return sheet.getRange(2, 1, sheet.getLastRow() - 1, HEADERS.length).getValues();
}

function object_(row) {
  const result = {};
  HEADERS.forEach((header, index) => result[header] = row[index]);
  return result;
}

function row_(value) {
  return HEADERS.map(header => value[header] === undefined ? '' : value[header]);
}

function scopedKey_(projectName, jobKey) {
  return String(projectName) + ':' + String(jobKey);
}

function claim_(request) {
  if (!request.worker_id || !Array.isArray(request.candidates)) {
    throw coded_('INVALID_REQUEST', 'claim requires worker_id and candidates');
  }
  const sheet = sheet_();
  const now = new Date();
  const byKey = {};
  rows_(sheet).forEach((row, index) => {
    const value = object_(row);
    byKey[scopedKey_(value.project_name, value.job_key)] = {index: index + 2, value: value};
  });

  request.candidates.forEach(candidate => {
    if (!candidate.job_key || !candidate.drive_file_id || !candidate.subchapter_id) return;
    const key = scopedKey_(request.project_name, candidate.job_key);
    if (!byKey[key]) {
      const value = {
        project_name: request.project_name, ...candidate, status: 'queued', worker_id: '', lease_expires_at: '', heartbeat_at: '',
        attempt_count: 0, branch: '', pr_url: '', error_code: '', error_message: '',
        updated_at: now.toISOString()
      };
      sheet.appendRow(row_(value));
      byKey[key] = {index: sheet.getLastRow(), value: value};
    }
  });

  for (const candidate of request.candidates) {
    const stored = byKey[scopedKey_(request.project_name, candidate.job_key)];
    if (!stored) continue;
    const value = stored.value;
    const expired = value.status === 'leased' && value.lease_expires_at && new Date(value.lease_expires_at) <= now;
    if (expired) value.status = 'queued';
    if (value.status !== 'queued') continue;
    if (Number(value.attempt_count || 0) >= Number(request.max_job_attempts || 1)) continue;

    value.status = 'leased';
    value.worker_id = request.worker_id;
    value.lease_expires_at = new Date(now.getTime() + Number(request.lease_seconds) * 1000).toISOString();
    value.heartbeat_at = now.toISOString();
    value.attempt_count = Number(value.attempt_count || 0) + 1;
    value.error_code = '';
    value.error_message = '';
    value.updated_at = now.toISOString();
    sheet.getRange(stored.index, 1, 1, HEADERS.length).setValues([row_(value)]);
    return {lease: lease_(value)};
  }
  throw coded_('NO_AVAILABLE_JOB', 'No queued or expired source job is currently available');
}

function owned_(request) {
  const sheet = sheet_();
  const rows = rows_(sheet);
  const index = rows.findIndex(row => {
    const value = object_(row);
    return String(value.project_name) === String(request.project_name) &&
      String(value.job_key) === String(request.job_key);
  });
  if (index < 0) throw coded_('LEASE_LOST', 'Job no longer exists');
  const value = object_(rows[index]);
  if (String(value.worker_id) !== String(request.worker_id) || value.status !== 'leased') {
    throw coded_('LEASE_LOST', 'Job is not leased to this worker');
  }
  if (!value.lease_expires_at || new Date(value.lease_expires_at) <= new Date()) {
    throw coded_('LEASE_LOST', 'Job lease has expired');
  }
  return {sheet: sheet, rowIndex: index + 2, value: value};
}

function heartbeat_(request) {
  const owned = owned_(request);
  const now = new Date();
  owned.value.heartbeat_at = now.toISOString();
  owned.value.lease_expires_at = new Date(now.getTime() + Number(request.lease_seconds) * 1000).toISOString();
  owned.value.updated_at = now.toISOString();
  owned.sheet.getRange(owned.rowIndex, 1, 1, HEADERS.length).setValues([row_(owned.value)]);
  return {lease: lease_(owned.value)};
}

function updateStatus_(request, status) {
  const owned = owned_(request);
  owned.value.status = status;
  owned.value.branch = request.branch || owned.value.branch;
  owned.value.pr_url = request.pr_url || owned.value.pr_url;
  owned.value.lease_expires_at = '';
  owned.value.heartbeat_at = '';
  owned.value.updated_at = new Date().toISOString();
  owned.sheet.getRange(owned.rowIndex, 1, 1, HEADERS.length).setValues([row_(owned.value)]);
  return {status: status};
}

function fail_(request) {
  const owned = owned_(request);
  const attempts = Number(owned.value.attempt_count || 0);
  owned.value.status = attempts < Number(request.max_job_attempts || 1) ? 'queued' : 'failed';
  owned.value.error_code = request.error_code || 'GENERATOR_ERROR';
  owned.value.error_message = request.error_message || '';
  owned.value.worker_id = '';
  owned.value.lease_expires_at = '';
  owned.value.heartbeat_at = '';
  owned.value.updated_at = new Date().toISOString();
  owned.sheet.getRange(owned.rowIndex, 1, 1, HEADERS.length).setValues([row_(owned.value)]);
  return {status: owned.value.status};
}

function complete_(request) {
  const sheet = sheet_();
  const rows = rows_(sheet);
  const index = rows.findIndex(row => {
    const value = object_(row);
    return String(value.project_name) === String(request.project_name) &&
      String(value.job_key) === String(request.job_key);
  });
  if (index < 0) throw coded_('NOT_FOUND', 'Job no longer exists');
  const value = object_(rows[index]);
  if (value.status !== 'review_pending' && value.status !== 'completed') {
    throw coded_('INVALID_STATUS', 'Only a review_pending job can be marked completed');
  }
  value.status = 'completed';
  value.pr_url = request.pr_url || value.pr_url;
  value.updated_at = new Date().toISOString();
  sheet.getRange(index + 2, 1, 1, HEADERS.length).setValues([row_(value)]);
  return {status: 'completed'};
}

function lease_(value) {
  return {
    job_key: String(value.job_key), drive_file_id: String(value.drive_file_id),
    source_version: String(value.source_version), subchapter_id: String(value.subchapter_id),
    relative_path: String(value.relative_path), worker_id: String(value.worker_id),
    lease_expires_at: String(value.lease_expires_at), attempt_count: Number(value.attempt_count)
  };
}

function coded_(code, message) {
  const error = new Error(message);
  error.code = code;
  return error;
}

function json_(value) {
  return ContentService.createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}
