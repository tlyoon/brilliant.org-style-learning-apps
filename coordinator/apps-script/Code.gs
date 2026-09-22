const COORDINATOR_VERSION = 4;
const JOB_SHEET = 'Jobs';
const HEADERS = [
  'project_name', 'job_key', 'drive_file_id', 'source_version', 'subchapter_id', 'relative_path',
  'status', 'worker_id', 'lease_expires_at', 'heartbeat_at', 'attempt_count',
  'branch', 'pr_url', 'error_code', 'error_message', 'updated_at'
];
const LEGACY_HEADERS = HEADERS.slice(1);
const RECEIPT_ACTIONS = [
  'claim', 'snapshot', 'heartbeat', 'review_pending', 'generated', 'failed', 'retry_failed',
  'completed', 'checkpoint_save', 'checkpoint_delete', 'checkpoint_clear'
];
const RECEIPT_PREFIX = 'REQUEST_RECEIPT:';
const RECEIPT_LIMIT = 100;

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
  return withLock_(() => {
    const replay = requestReceipt_(request);
    if (replay !== null) return replay;
    const result = dispatchUnlocked_(request);
    saveRequestReceipt_(request, result);
    return result;
  });
}

function dispatchUnlocked_(request) {
  switch (request.action) {
    case 'health': return health_(request);
    case 'claim': return claim_(request);
    case 'snapshot': return snapshot_(request);
    case 'heartbeat': return heartbeat_(request);
    case 'review_pending': return updateStatus_(request, 'review_pending');
    case 'generated': return updateStatus_(request, 'generated');
    case 'failed': return fail_(request);
    case 'retry_failed': return retryFailed_(request);
    case 'completed': return complete_(request);
    case 'checkpoint_save': return checkpointSave_(request);
    case 'checkpoint_load': return checkpointLoad_(request);
    case 'checkpoint_delete': return checkpointDelete_(request);
    case 'checkpoint_clear': return checkpointClear_(request);
    default: throw coded_('INVALID_ACTION', 'Unsupported coordinator action');
  }
}

function receiptAction_(action) {
  return RECEIPT_ACTIONS.includes(String(action || ''));
}

function requestId_(request) {
  const requestId = String(request.request_id || '');
  if (!/^[A-Za-z0-9_-]{16,128}$/.test(requestId)) {
    throw coded_('INVALID_REQUEST', 'State-changing coordinator actions require a valid request_id');
  }
  return requestId;
}

function requestHash_(request) {
  const value = {...request};
  delete value.token;
  const digest = Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    JSON.stringify(value)
  );
  return Utilities.base64EncodeWebSafe(digest);
}

function requestReceipt_(request) {
  if (!receiptAction_(request.action)) return null;
  const requestId = requestId_(request);
  const raw = PropertiesService.getScriptProperties().getProperty(RECEIPT_PREFIX + requestId);
  if (!raw) return null;
  let receipt;
  try {
    receipt = JSON.parse(raw);
  } catch (error) {
    throw coded_('INVALID_RECEIPT', 'Stored coordinator request receipt is unreadable');
  }
  if (String(receipt.project_name) !== String(request.project_name) ||
      String(receipt.action) !== String(request.action) ||
      String(receipt.request_hash) !== requestHash_(request)) {
    throw coded_('REQUEST_ID_REUSED', 'Coordinator request_id was reused for a different operation');
  }
  return receipt.result;
}

function saveRequestReceipt_(request, result) {
  if (!receiptAction_(request.action)) return;
  const requestId = requestId_(request);
  const properties = PropertiesService.getScriptProperties();
  properties.setProperty(RECEIPT_PREFIX + requestId, JSON.stringify({
    project_name: request.project_name,
    action: request.action,
    request_hash: requestHash_(request),
    result: result,
    created_at: new Date().toISOString()
  }));
  pruneRequestReceipts_(properties);
}

function pruneRequestReceipts_(properties) {
  const receipts = Object.entries(properties.getProperties())
    .filter(entry => entry[0].startsWith(RECEIPT_PREFIX))
    .map(entry => {
      try {
        return {key: entry[0], created_at: String(JSON.parse(entry[1]).created_at || '')};
      } catch (error) {
        return {key: entry[0], created_at: ''};
      }
    })
    .sort((left, right) => right.created_at.localeCompare(left.created_at));
  receipts.slice(RECEIPT_LIMIT).forEach(receipt => properties.deleteProperty(receipt.key));
}

function health_(request) {
  sheet_();
  return {
    status: 'ok',
    project_name: request.project_name,
    coordinator_version: COORDINATOR_VERSION,
    checkpoint_configured: Boolean(PropertiesService.getScriptProperties().getProperty('CHECKPOINT_FOLDER_ID'))
  };
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
  let migrated = false;
  if (!properties.getProperty('WORKER_TOKEN')) {
    const legacy = properties.getProperty('BRILLIANT_WORKER_TOKEN');
    if (legacy) {
      properties.setProperty('WORKER_TOKEN', legacy);
      migrated = true;
    } else {
      const material = [Utilities.getUuid(), Utilities.getUuid(), Utilities.getUuid()].join(':');
      const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, material);
      properties.setProperty('WORKER_TOKEN', Utilities.base64EncodeWebSafe(digest));
      created = true;
    }
  }
  sheet_();
  return {
    project_name: projectName,
    worker_token_created: created,
    legacy_worker_token_migrated: migrated
  };
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
  const legacyActual = sheet.getRange(1, 1, 1, LEGACY_HEADERS.length).getValues()[0];
  if (sheet.getLastColumn() === LEGACY_HEADERS.length &&
      legacyActual.join('|') === LEGACY_HEADERS.join('|')) {
    migrateLegacySheet_(sheet);
  }
  const actual = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  if (actual.join('|') !== HEADERS.join('|')) {
    throw coded_('INVALID_LEDGER', 'Jobs sheet headers do not match the coordinator contract');
  }
  return sheet;
}

function migrateLegacySheet_(sheet) {
  const projectName = PropertiesService.getScriptProperties().getProperty('PROJECT_NAME');
  if (!projectName) throw coded_('NOT_CONFIGURED', 'PROJECT_NAME is required for ledger migration');
  sheet.insertColumnBefore(1);
  sheet.getRange(1, 1).setValue('project_name');
  if (sheet.getLastRow() > 1) {
    const values = Array(sheet.getLastRow() - 1).fill([projectName]);
    sheet.getRange(2, 1, values.length, 1).setValues(values);
  }
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

function candidateMap_(sheet) {
  const byKey = {};
  rows_(sheet).forEach((row, index) => {
    const value = object_(row);
    byKey[scopedKey_(value.project_name, value.job_key)] = {index: index + 2, value: value};
  });
  return byKey;
}

function ensureCandidates_(sheet, request, now) {
  if (!Array.isArray(request.candidates)) {
    throw coded_('INVALID_REQUEST', 'candidates must be an array');
  }
  const byKey = candidateMap_(sheet);
  request.candidates.forEach(candidate => {
    if (!candidate.job_key || !candidate.drive_file_id || !candidate.subchapter_id) return;
    const key = scopedKey_(request.project_name, candidate.job_key);
    let stored = byKey[key];
    if (!stored) {
      const value = {
        project_name: request.project_name, ...candidate,
        status: candidate.local_completed ? 'generated' : 'queued',
        worker_id: '', lease_expires_at: '', heartbeat_at: '', attempt_count: 0,
        branch: '', pr_url: '', error_code: '', error_message: '', updated_at: now.toISOString()
      };
      delete value.local_completed;
      sheet.appendRow(row_(value));
      stored = {index: sheet.getLastRow(), value: value};
      byKey[key] = stored;
    } else if (candidate.local_completed && ['queued', 'interrupted', 'failed'].includes(String(stored.value.status))) {
      stored.value.status = 'generated';
      stored.value.lease_expires_at = '';
      stored.value.heartbeat_at = '';
      stored.value.error_code = '';
      stored.value.error_message = '';
      stored.value.updated_at = now.toISOString();
      sheet.getRange(stored.index, 1, 1, HEADERS.length).setValues([row_(stored.value)]);
    }
  });
  return byKey;
}

function reconcile_(sheet, request, byKey, now) {
  request.candidates.forEach(candidate => {
    const stored = byKey[scopedKey_(request.project_name, candidate.job_key)];
    if (!stored) return;
    const value = stored.value;
    let changed = false;
    const expired = value.status === 'leased' && value.lease_expires_at && new Date(value.lease_expires_at) <= now;
    if (expired) {
      value.status = 'interrupted';
      value.lease_expires_at = '';
      value.heartbeat_at = '';
      value.error_code = value.error_code || 'LEASE_EXPIRED';
      value.error_message = value.error_message || 'Worker heartbeat expired before completion';
      changed = true;
    }
    if (value.status === 'interrupted' && Number(value.attempt_count || 0) >= Number(request.max_job_attempts || 1)) {
      value.status = 'failed';
      value.error_code = value.error_code || 'MAX_ATTEMPTS_EXHAUSTED';
      value.error_message = value.error_message || 'Maximum automatic generation attempts exhausted';
      changed = true;
    }
    if (changed) {
      value.updated_at = now.toISOString();
      sheet.getRange(stored.index, 1, 1, HEADERS.length).setValues([row_(value)]);
    }
  });
}

function candidatePriority_(value, workerId) {
  if (value.status === 'interrupted' && String(value.worker_id) !== String(workerId)) return 0;
  if (value.status === 'queued') return 1;
  if (value.status === 'interrupted') return 2;
  return 99;
}

function chooseCandidate_(request, byKey) {
  let chosen = null;
  let priority = 99;
  request.candidates.forEach(candidate => {
    const stored = byKey[scopedKey_(request.project_name, candidate.job_key)];
    if (!stored) return;
    const current = candidatePriority_(stored.value, request.worker_id);
    if (current < priority) {
      chosen = stored;
      priority = current;
    }
  });
  return chosen;
}

function claim_(request) {
  if (!request.worker_id || !Array.isArray(request.candidates)) {
    throw coded_('INVALID_REQUEST', 'claim requires worker_id and candidates');
  }
  const sheet = sheet_();
  const now = new Date();
  const byKey = ensureCandidates_(sheet, request, now);
  reconcile_(sheet, request, byKey, now);
  const stored = chooseCandidate_(request, byKey);
  if (!stored) throw coded_('NO_AVAILABLE_JOB', 'No queued or interrupted source job is currently available');

  const value = stored.value;
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

function snapshot_(request) {
  if (!request.worker_id || !Array.isArray(request.candidates)) {
    throw coded_('INVALID_REQUEST', 'snapshot requires worker_id and candidates');
  }
  const sheet = sheet_();
  const now = new Date();
  const byKey = ensureCandidates_(sheet, request, now);
  reconcile_(sheet, request, byKey, now);
  const counts = {queued: 0, interrupted: 0, leased: 0, generated: 0, review_pending: 0, completed: 0, failed: 0};
  request.candidates.forEach(candidate => {
    const stored = byKey[scopedKey_(request.project_name, candidate.job_key)];
    if (!stored) return;
    const status = String(stored.value.status || 'queued');
    if (counts[status] !== undefined) counts[status] += 1;
  });
  const next = chooseCandidate_(request, byKey);
  const target = request.candidates.length === 1
    ? byKey[scopedKey_(request.project_name, request.candidates[0].job_key)]
    : null;
  return {
    snapshot: {
      total: request.candidates.length,
      counts: counts,
      next_candidate: next ? {
        job_key: String(next.value.job_key),
        subchapter_id: String(next.value.subchapter_id),
        status: String(next.value.status)
      } : null,
      target_state: target ? {
        status: String(target.value.status),
        attempt_count: Number(target.value.attempt_count || 0),
        error_code: String(target.value.error_code || '')
      } : null
    }
  };
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
  owned.value.status = attempts < Number(request.max_job_attempts || 1) ? 'interrupted' : 'failed';
  owned.value.error_code = request.error_code || 'GENERATOR_ERROR';
  owned.value.error_message = request.error_message || '';
  // Retain worker_id after interruption so the scheduler can prioritize
  // abandoned work on a different PC before retrying it on the same PC.
  owned.value.lease_expires_at = '';
  owned.value.heartbeat_at = '';
  owned.value.updated_at = new Date().toISOString();
  owned.sheet.getRange(owned.rowIndex, 1, 1, HEADERS.length).setValues([row_(owned.value)]);
  return {status: owned.value.status};
}

function retryFailed_(request) {
  if (!request.worker_id || !request.job_key || !request.drive_file_id ||
      !request.source_version || !request.subchapter_id) {
    throw coded_('INVALID_REQUEST', 'retry_failed requires exact worker and source identity');
  }
  const sheet = sheet_();
  const rows = rows_(sheet);
  const index = rows.findIndex(row => {
    const value = object_(row);
    return String(value.project_name) === String(request.project_name) &&
      String(value.job_key) === String(request.job_key);
  });
  if (index < 0) throw coded_('NOT_FOUND', 'Failed job no longer exists');
  const value = object_(rows[index]);
  if (value.status !== 'failed') {
    throw coded_('INVALID_STATUS', 'Only a terminally failed job can be retried explicitly');
  }
  if (String(value.drive_file_id) !== String(request.drive_file_id) ||
      String(value.source_version) !== String(request.source_version) ||
      String(value.subchapter_id) !== String(request.subchapter_id)) {
    throw coded_('SOURCE_MISMATCH', 'Failed job no longer matches the selected Drive source');
  }
  const previousAttemptCount = Number(value.attempt_count || 0);
  const previousErrorCode = String(value.error_code || '');
  value.status = 'interrupted';
  value.worker_id = String(request.worker_id);
  value.lease_expires_at = '';
  value.heartbeat_at = '';
  value.attempt_count = 0;
  // Preserve the last diagnostic until the next successful atomic claim clears it.
  value.updated_at = new Date().toISOString();
  sheet.getRange(index + 2, 1, 1, HEADERS.length).setValues([row_(value)]);
  return {
    status: value.status,
    previous_attempt_count: previousAttemptCount,
    previous_error_code: previousErrorCode
  };
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

function checkpointFolder_() {
  const folderId = PropertiesService.getScriptProperties().getProperty('CHECKPOINT_FOLDER_ID');
  if (!folderId) throw coded_('NOT_CONFIGURED', 'CHECKPOINT_FOLDER_ID is required for auto checkpoints');
  return DriveApp.getFolderById(folderId);
}

function safeStage_(stage) {
  if (!/^[a-z0-9-]+$/.test(String(stage || ''))) {
    throw coded_('INVALID_REQUEST', 'Checkpoint stage name is invalid');
  }
  return String(stage);
}

function checkpointName_(request) {
  const project = String(request.project_name).replace(/[^A-Za-z0-9._-]+/g, '-');
  return project + '--' + String(request.job_key) + '.json';
}

function checkpointFile_(request) {
  const files = checkpointFolder_().getFilesByName(checkpointName_(request));
  return files.hasNext() ? files.next() : null;
}

function checkpointDocument_(request, createIfMissing) {
  const file = checkpointFile_(request);
  if (!file) {
    if (!createIfMissing) return {file: null, value: null};
    return {
      file: null,
      value: {
        project_name: request.project_name,
        job_key: request.job_key,
        source_version: request.source_version,
        stages: {},
        updated_at: new Date().toISOString()
      }
    };
  }
  let value;
  try {
    value = JSON.parse(file.getBlob().getDataAsString('UTF-8'));
  } catch (error) {
    throw coded_('INVALID_CHECKPOINT', 'Checkpoint JSON is unreadable');
  }
  if (String(value.project_name) !== String(request.project_name) ||
      String(value.job_key) !== String(request.job_key) ||
      String(value.source_version) !== String(request.source_version)) {
    throw coded_('CHECKPOINT_SOURCE_MISMATCH', 'Checkpoint belongs to a different source version');
  }
  if (!value.stages || typeof value.stages !== 'object' || Array.isArray(value.stages)) value.stages = {};
  return {file: file, value: value};
}

function requireCheckpointOwner_(request) {
  const owned = owned_(request);
  if (String(owned.value.source_version) !== String(request.source_version)) {
    throw coded_('CHECKPOINT_SOURCE_MISMATCH', 'Lease source version does not match checkpoint request');
  }
  return owned;
}

function writeCheckpoint_(request, document) {
  document.updated_at = new Date().toISOString();
  const text = JSON.stringify(document);
  const existing = checkpointFile_(request);
  if (existing) {
    existing.setContent(text);
  } else {
    checkpointFolder_().createFile(checkpointName_(request), text, MimeType.PLAIN_TEXT);
  }
}

function checkpointSave_(request) {
  requireCheckpointOwner_(request);
  const stage = safeStage_(request.stage);
  const checkpoint = checkpointDocument_(request, true);
  checkpoint.value.stages[stage] = request.document;
  writeCheckpoint_(request, checkpoint.value);
  return {stage: stage};
}

function checkpointLoad_(request) {
  requireCheckpointOwner_(request);
  const checkpoint = checkpointDocument_(request, false);
  return {stages: checkpoint.value ? checkpoint.value.stages : {}};
}

function checkpointDelete_(request) {
  requireCheckpointOwner_(request);
  const stage = safeStage_(request.stage);
  const checkpoint = checkpointDocument_(request, false);
  if (!checkpoint.value) return {stage: stage};
  delete checkpoint.value.stages[stage];
  writeCheckpoint_(request, checkpoint.value);
  return {stage: stage};
}

function checkpointClear_(request) {
  requireCheckpointOwner_(request);
  const file = checkpointFile_(request);
  if (file) file.setTrashed(true);
  return {cleared: true};
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
