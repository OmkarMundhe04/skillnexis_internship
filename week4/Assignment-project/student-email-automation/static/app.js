/**
 * MailPulse — Student Email Automation Dashboard Logic
 * Handles SSE campaign streaming, CSV management, template live preview,
 * audit log filtering, and SMTP connection diagnostics.
 */

document.addEventListener('DOMContentLoaded', () => {
  // --- STATE ---
  let appState = {
    validStudents: [],
    skippedRecords: [],
    logs: [],
    activeLogFilter: 'ALL',
    activeEventSource: null,
    isDispatching: false,
  };

  // --- DOM ELEMENTS ---
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  // Metrics
  const metricValidCount = document.getElementById('metric-valid-count');
  const metricSkippedCount = document.getElementById('metric-skipped-count');
  const metricSenderEmail = document.getElementById('metric-sender-email');
  const metricSafetyMode = document.getElementById('metric-safety-mode');
  const metricCsvFile = document.getElementById('metric-csv-file');

  // Header SMTP Status
  const smtpDot = document.getElementById('smtp-dot');
  const smtpStatusText = document.getElementById('smtp-status-text');
  const btnQuickTestSmtp = document.getElementById('btn-quick-test-smtp');

  // Dispatcher
  const radioModeDry = document.getElementById('radio-mode-dry');
  const radioModeLive = document.getElementById('radio-mode-live');
  const modeCardDry = document.getElementById('mode-card-dry');
  const modeCardLive = document.getElementById('mode-card-live');
  const sliderDelay = document.getElementById('slider-delay');
  const sliderDelayVal = document.getElementById('slider-delay-val');
  const summaryRecipientsCount = document.getElementById('summary-recipients-count');
  const summaryDuration = document.getElementById('summary-duration');
  const summarySender = document.getElementById('summary-sender');
  const btnStartCampaign = document.getElementById('btn-start-campaign');

  // Terminal & Progress
  const progressBarFill = document.getElementById('progress-bar-fill');
  const progressText = document.getElementById('progress-text');
  const progressPercentage = document.getElementById('progress-percentage');
  const streamStatusIndicator = document.getElementById('stream-status-indicator');
  const streamStatusText = document.getElementById('stream-status-text');
  const terminalOutput = document.getElementById('terminal-output');
  const btnClearTerminal = document.getElementById('btn-clear-terminal');

  // Recipients
  const inputNewStudentName = document.getElementById('input-new-student-name');
  const inputNewStudentEmail = document.getElementById('input-new-student-email');
  const btnAddDirectStudent = document.getElementById('btn-add-direct-student');
  const csvDropZone = document.getElementById('csv-drop-zone');
  const csvFileInput = document.getElementById('csv-file-input');
  const filterRecipients = document.getElementById('filter-recipients');
  const recipientsTableBody = document.getElementById('recipients-table-body');
  const badgeValidCount = document.getElementById('badge-valid-count');
  const badgeSkippedCount = document.getElementById('badge-skipped-count');
  const btnRefreshStudents = document.getElementById('btn-refresh-students');

  // Template Studio
  const templateEditor = document.getElementById('template-editor');
  const templatePreviewFrame = document.getElementById('template-preview-frame');
  const btnSaveTemplate = document.getElementById('btn-save-template');

  // Logs
  const logsTableBody = document.getElementById('logs-table-body');
  const filterLogs = document.getElementById('filter-logs');
  const logStatusFilters = document.querySelectorAll('#log-status-filters .pill');
  const btnRefreshLogs = document.getElementById('btn-refresh-logs');
  const btnClearLogs = document.getElementById('btn-clear-logs');

  // Modal
  const modalConfirmLive = document.getElementById('modal-confirm-live');
  const modalRecipientCount = document.getElementById('modal-recipient-count');
  const modalSenderEmail = document.getElementById('modal-sender-email');
  const btnCancelLiveSend = document.getElementById('btn-cancel-live-send');
  const btnConfirmLiveSend = document.getElementById('btn-confirm-live-send');

  // --- TAB ROUTING ---
  function activateTab(tabId) {
    tabButtons.forEach(btn => {
      const isTarget = btn.getAttribute('data-tab') === tabId;
      btn.classList.toggle('active', isTarget);
      btn.setAttribute('aria-selected', isTarget);
    });

    tabContents.forEach(content => {
      content.classList.toggle('active', content.id === tabId);
    });

    // Lazy load or refresh tab contents
    if (tabId === 'tab-recipients') loadStudents();
    if (tabId === 'tab-template') loadTemplate();
    if (tabId === 'tab-logs') loadLogs();
  }

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      activateTab(targetTab);
    });
  });

  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = link.getAttribute('data-tab');
      if (targetTab) activateTab(targetTab);
    });
  });

  // --- TOAST NOTIFICATIONS ---
  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // --- SYSTEM STATUS & METRICS ---
  async function fetchStatus() {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) throw new Error('Failed to fetch system status');
      const data = await res.json();

      metricValidCount.textContent = data.valid_count;
      metricSkippedCount.textContent = data.skipped_count;
      metricSenderEmail.textContent = data.sender_email;
      metricSenderEmail.title = data.sender_email;
      summarySender.textContent = data.sender_email;
      summaryRecipientsCount.textContent = `${data.valid_count} Students`;
      metricCsvFile.textContent = `Source: ${data.csv_filename}`;

      if (data.has_credentials) {
        smtpDot.classList.add('active');
        smtpDot.classList.remove('pulsing');
        smtpStatusText.textContent = 'SMTP Ready';
      } else {
        smtpDot.classList.remove('active');
        smtpDot.classList.remove('pulsing');
        smtpStatusText.textContent = 'SMTP Unset';
      }

      updateEstimatedDuration();
    } catch (err) {
      console.error(err);
      smtpStatusText.textContent = 'Offline';
    }
  }

  function updateEstimatedDuration() {
    const count = parseInt(metricValidCount.textContent, 10) || 0;
    const delay = parseFloat(sliderDelay.value) || 1.0;
    const isDry = radioModeDry.checked;

    if (isDry) {
      const drySecs = Math.max(1, Math.round(count * 0.2));
      summaryDuration.textContent = `~${drySecs}s (Dry Run)`;
    } else {
      const totalSecs = Math.round(count * (delay + 0.3));
      summaryDuration.textContent = `~${totalSecs}s (${Math.ceil(totalSecs / 60)} min)`;
    }
  }

  // --- DISPATCH CONTROLS ---
  function setMode(mode) {
    if (mode === 'dry_run') {
      radioModeDry.checked = true;
      modeCardDry.classList.add('selected');
      modeCardLive.classList.remove('selected');
      btnStartCampaign.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
        Run Safe Simulation (Dry Run)
      `;
      btnStartCampaign.className = 'btn btn-primary btn-block btn-lg';
    } else {
      radioModeLive.checked = true;
      modeCardLive.classList.add('selected');
      modeCardDry.classList.remove('selected');
      btnStartCampaign.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="22" y1="2" x2="11" y2="13"/>
          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
        Launch Live Send
      `;
      btnStartCampaign.className = 'btn btn-danger btn-block btn-lg';
    }
    updateEstimatedDuration();
  }

  modeCardDry.addEventListener('click', () => setMode('dry_run'));
  modeCardLive.addEventListener('click', () => setMode('live'));

  sliderDelay.addEventListener('input', (e) => {
    sliderDelayVal.textContent = `${parseFloat(e.target.value).toFixed(1)}s`;
    updateEstimatedDuration();
  });

  // --- TERMINAL UTILITIES ---
  function appendTerminalLine(text, cssClass = 'info') {
    const line = document.createElement('div');
    line.className = `term-line ${cssClass}`;
    line.textContent = text;
    terminalOutput.appendChild(line);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
  }

  btnClearTerminal.addEventListener('click', () => {
    terminalOutput.innerHTML = '<div class="term-line prompt">Terminal cleared. Ready for next dispatch.</div>';
  });

  // --- SSE REAL-TIME DISPATCH ENGINE ---
  function startCampaign(mode) {
    if (appState.isDispatching) return;

    appState.isDispatching = true;
    btnStartCampaign.disabled = true;
    streamStatusIndicator.classList.add('active');
    streamStatusText.textContent = mode === 'live' ? 'Sending Live...' : 'Simulating...';

    // Reset progress
    progressBarFill.style.width = '0%';
    progressPercentage.textContent = '0%';
    progressText.textContent = 'Initializing campaign...';

    appendTerminalLine(`\n--- CAMPAIGN STARTED [Mode: ${mode.toUpperCase()}] ---`, 'prompt');

    const delay = parseFloat(sliderDelay.value) || 1.0;
    const url = `/api/stream-campaign?mode=${encodeURIComponent(mode)}&delay=${encodeURIComponent(delay)}`;

    const evtSource = new EventSource(url);
    appState.activeEventSource = evtSource;

    evtSource.addEventListener('init', (e) => {
      const data = JSON.parse(e.data);
      appendTerminalLine(`[INIT] ${data.total} recipients queued (${data.skipped} skipped). Rate delay: ${data.delay}s`, 'info');
      progressText.textContent = `Dispatching 0 / ${data.total}`;
    });

    evtSource.addEventListener('status', (e) => {
      const data = JSON.parse(e.data);
      appendTerminalLine(`[STATUS] ${data.message}`, 'info');
      progressText.textContent = data.message;
    });

    evtSource.addEventListener('progress', (e) => {
      const data = JSON.parse(e.data);
      const pct = data.percentage || 0;
      progressBarFill.style.width = `${pct}%`;
      progressPercentage.textContent = `${pct}%`;
      progressText.textContent = `Sent ${data.current} / ${data.total} (${data.status})`;

      let css = 'info';
      if (data.status === 'SENT') css = 'sent';
      else if (data.status === 'FAILED') css = 'failed';
      else if (data.status === 'DRY_RUN') css = 'dryrun';

      appendTerminalLine(`[${data.current}/${data.total}] [${data.status}] ${data.name} <${data.email}> — ${data.details}`, css);
    });

    evtSource.addEventListener('done', (e) => {
      const data = JSON.parse(e.data);
      const summary = data.summary;

      progressBarFill.style.width = '100%';
      progressPercentage.textContent = '100%';
      progressText.textContent = `Campaign Completed!`;

      appendTerminalLine(`\n=== CAMPAIGN SUMMARY ===`, 'prompt');
      appendTerminalLine(`Processed: ${summary.processed} | Sent: ${summary.sent} | Failed: ${summary.failed} | Skipped: ${summary.skipped}`, 'sent');

      evtSource.close();
      finishDispatch(summary);
    });

    evtSource.addEventListener('error', (e) => {
      let errMsg = 'Connection closed or stream error.';
      try {
        if (e.data) {
          const parsed = JSON.parse(e.data);
          if (parsed.error) errMsg = parsed.error;
        }
      } catch (_) {}

      appendTerminalLine(`[ERROR] ${errMsg}`, 'failed');
      showToast(errMsg, 'error');
      evtSource.close();
      finishDispatch();
    });
  }

  function finishDispatch(summary = null) {
    appState.isDispatching = false;
    btnStartCampaign.disabled = false;
    streamStatusIndicator.classList.remove('active');
    streamStatusText.textContent = 'Completed';

    if (summary) {
      showToast(`Campaign finished! ${summary.sent || summary.processed} records processed.`, 'success');
    }
    fetchStatus();
  }

  // Start Campaign Trigger
  btnStartCampaign.addEventListener('click', () => {
    const isLive = radioModeLive.checked;
    if (isLive) {
      modalRecipientCount.textContent = metricValidCount.textContent;
      modalSenderEmail.textContent = metricSenderEmail.textContent;
      modalConfirmLive.showModal();
    } else {
      startCampaign('dry_run');
    }
  });

  btnCancelLiveSend.addEventListener('click', () => {
    modalConfirmLive.close();
  });

  btnConfirmLiveSend.addEventListener('click', () => {
    modalConfirmLive.close();
    startCampaign('live');
  });

  // --- RECIPIENTS (CSV) ---
  async function loadStudents() {
    try {
      const res = await fetch('/api/students');
      const data = await res.json();

      appState.validStudents = data.valid || [];
      appState.skippedRecords = data.skipped || [];

      badgeValidCount.textContent = `${appState.validStudents.length} Valid`;
      badgeSkippedCount.textContent = `${appState.skippedRecords.length} Skipped`;

      renderRecipientsTable();
    } catch (err) {
      console.error(err);
      recipientsTableBody.innerHTML = `<tr><td colspan="6" class="table-empty">Error loading recipients: ${err.message}</td></tr>`;
    }
  }

  function renderRecipientsTable() {
    const filter = (filterRecipients.value || '').toLowerCase().trim();
    let rowsHtml = '';
    let displayIndex = 1;

    // Render Valid Students
    appState.validStudents.forEach((st) => {
      if (filter && !st.name.toLowerCase().includes(filter) && !st.email.toLowerCase().includes(filter)) {
        return;
      }
      rowsHtml += `
        <tr>
          <td>${displayIndex++}</td>
          <td><strong>${escapeHtml(st.name)}</strong></td>
          <td><code>${escapeHtml(st.email)}</code></td>
          <td><span class="badge badge-emerald">VALID</span></td>
          <td>Ready for delivery</td>
          <td style="text-align: right;">
            <button type="button" class="btn btn-danger btn-remove-student" data-email="${escapeHtml(st.email)}" data-name="${escapeHtml(st.name)}" title="Remove student from list">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
              Remove
            </button>
          </td>
        </tr>
      `;
    });

    // Render Skipped Students
    appState.skippedRecords.forEach((sk) => {
      if (filter && !sk.name.toLowerCase().includes(filter) && !sk.email.toLowerCase().includes(filter)) {
        return;
      }
      const canRemove = Boolean(sk.email);
      rowsHtml += `
        <tr>
          <td>${displayIndex++}</td>
          <td>${escapeHtml(sk.name || '—')}</td>
          <td><code>${escapeHtml(sk.email || '—')}</code></td>
          <td><span class="badge badge-amber">SKIPPED</span></td>
          <td class="term-line failed">${escapeHtml(sk.reason || 'Invalid format')}</td>
          <td style="text-align: right;">
            ${canRemove ? `
              <button type="button" class="btn btn-danger btn-remove-student" data-email="${escapeHtml(sk.email)}" data-name="${escapeHtml(sk.name || sk.email)}" title="Remove invalid record">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
                Remove
              </button>
            ` : '—'}
          </td>
        </tr>
      `;
    });

    if (!rowsHtml) {
      rowsHtml = `<tr><td colspan="6" class="table-empty">No student records match your query.</td></tr>`;
    }

    recipientsTableBody.innerHTML = rowsHtml;
  }

  // Handle Direct Add Student
  async function handleDirectAddStudent() {
    const name = (inputNewStudentName.value || '').trim();
    const email = (inputNewStudentEmail.value || '').trim();

    if (!name) {
      showToast('Please enter student name.', 'error');
      inputNewStudentName.focus();
      return;
    }
    if (!email) {
      showToast('Please enter student email.', 'error');
      inputNewStudentEmail.focus();
      return;
    }

    btnAddDirectStudent.disabled = true;
    try {
      const res = await fetch('/api/students/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to add student');

      showToast(data.message, 'success');
      inputNewStudentName.value = '';
      inputNewStudentEmail.value = '';
      loadStudents();
      fetchStatus();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btnAddDirectStudent.disabled = false;
    }
  }

  btnAddDirectStudent.addEventListener('click', handleDirectAddStudent);
  [inputNewStudentName, inputNewStudentEmail].forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleDirectAddStudent();
      }
    });
  });

  // Handle Remove Student via Delegated Click
  recipientsTableBody.addEventListener('click', async (e) => {
    const btn = e.target.closest('.btn-remove-student');
    if (!btn) return;
    const email = btn.getAttribute('data-email');
    const name = btn.getAttribute('data-name') || email;

    if (!confirm(`Are you sure you want to remove ${name} (${email}) from recipients?`)) {
      return;
    }

    btn.disabled = true;
    try {
      const res = await fetch('/api/students/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to remove student');

      showToast(data.message, 'success');
      loadStudents();
      fetchStatus();
    } catch (err) {
      showToast(err.message, 'error');
      btn.disabled = false;
    }
  });

  filterRecipients.addEventListener('input', renderRecipientsTable);
  btnRefreshStudents.addEventListener('click', () => {
    loadStudents();
    fetchStatus();
    showToast('Recipients refreshed', 'info');
  });

  // CSV Drag & Drop Upload
  ['dragenter', 'dragover'].forEach(eventName => {
    csvDropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      csvDropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    csvDropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      csvDropZone.classList.remove('dragover');
    });
  });

  csvDropZone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) handleCsvUpload(files[0]);
  });

  csvFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleCsvUpload(e.target.files[0]);
  });

  async function handleCsvUpload(file) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      showToast('Please upload a valid .csv file.', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    showToast(`Uploading ${file.name}...`, 'info');

    try {
      const res = await fetch('/api/upload-csv', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (!res.ok) throw new Error(data.detail || 'Upload failed');

      showToast(data.message, 'success');
      loadStudents();
      fetchStatus();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // --- TEMPLATE STUDIO ---
  async function loadTemplate() {
    try {
      const res = await fetch('/api/template');
      const data = await res.json();

      templateEditor.value = data.raw_html;
      updateTemplatePreview(data.sample_preview);
    } catch (err) {
      console.error(err);
      showToast('Failed to load email template', 'error');
    }
  }

  function updateTemplatePreview(html) {
    templatePreviewFrame.srcdoc = html;
  }

  let templateDebounceTimer = null;
  templateEditor.addEventListener('input', () => {
    clearTimeout(templateDebounceTimer);
    templateDebounceTimer = setTimeout(() => {
      const raw = templateEditor.value;
      const preview = raw.replace(/\{\{name\}\}/g, 'Alex Morgan');
      updateTemplatePreview(preview);
    }, 300);
  });

  btnSaveTemplate.addEventListener('click', async () => {
    const htmlContent = templateEditor.value;
    try {
      const res = await fetch('/api/template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html: htmlContent }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to save template');

      showToast('Template saved successfully!', 'success');
      updateTemplatePreview(data.sample_preview);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // --- AUDIT LOGS ---
  async function loadLogs() {
    try {
      const res = await fetch('/api/logs?limit=300');
      const data = await res.json();
      appState.logs = data.logs || [];
      renderLogsTable();
    } catch (err) {
      console.error(err);
      logsTableBody.innerHTML = `<tr><td colspan="4" class="table-empty">Error loading audit logs.</td></tr>`;
    }
  }

  function renderLogsTable() {
    const filter = (filterLogs.value || '').toLowerCase().trim();
    const statusFilter = appState.activeLogFilter;

    let rowsHtml = '';
    appState.logs.forEach((log) => {
      if (statusFilter !== 'ALL' && log.status !== statusFilter) return;
      if (filter && !log.name.toLowerCase().includes(filter) && !log.email.toLowerCase().includes(filter) && !log.details.toLowerCase().includes(filter)) {
        return;
      }

      let badgeClass = 'badge-info';
      if (log.status === 'SENT') badgeClass = 'badge-emerald';
      else if (log.status === 'FAILED') badgeClass = 'badge-danger';
      else if (log.status === 'DRY_RUN' || log.status === 'SKIPPED') badgeClass = 'badge-amber';

      rowsHtml += `
        <tr>
          <td><strong>${escapeHtml(log.name || '—')}</strong></td>
          <td><code>${escapeHtml(log.email || '—')}</code></td>
          <td><span class="badge ${badgeClass}">${escapeHtml(log.status)}</span></td>
          <td>${escapeHtml(log.details || '—')}</td>
        </tr>
      `;
    });

    if (!rowsHtml) {
      rowsHtml = `<tr><td colspan="4" class="table-empty">No audit logs found.</td></tr>`;
    }

    logsTableBody.innerHTML = rowsHtml;
  }

  filterLogs.addEventListener('input', renderLogsTable);

  logStatusFilters.forEach(pill => {
    pill.addEventListener('click', () => {
      logStatusFilters.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      appState.activeLogFilter = pill.getAttribute('data-status');
      renderLogsTable();
    });
  });

  btnRefreshLogs.addEventListener('click', () => {
    loadLogs();
    showToast('Logs refreshed', 'info');
  });

  btnClearLogs.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to clear all audit logs?')) return;
    try {
      const res = await fetch('/api/clear-logs', { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        showToast('Audit logs cleared', 'info');
        loadLogs();
      }
    } catch (err) {
      showToast('Failed to clear logs', 'error');
    }
  });

  // --- SMTP QUICK TEST ---
  btnQuickTestSmtp.addEventListener('click', async () => {
    btnQuickTestSmtp.disabled = true;
    smtpStatusText.textContent = 'Testing connection...';
    smtpDot.classList.add('pulsing');
    showToast('Connecting to SMTP server...', 'info');

    try {
      const res = await fetch('/api/test-connection', { method: 'POST' });
      const data = await res.json();

      if (data.success) {
        smtpDot.classList.add('active');
        smtpDot.classList.remove('pulsing');
        smtpStatusText.textContent = 'Connected';
        showToast(data.message, 'success');
      } else {
        smtpDot.classList.remove('active');
        smtpDot.classList.remove('pulsing');
        smtpStatusText.textContent = 'Failed';
        showToast(data.message, 'error');
      }
    } catch (err) {
      smtpStatusText.textContent = 'Error';
      showToast(`SMTP test request failed: ${err.message}`, 'error');
    } finally {
      btnQuickTestSmtp.disabled = false;
    }
  });

  // --- INITIALIZATION ---
  fetchStatus();
  loadStudents();
});
