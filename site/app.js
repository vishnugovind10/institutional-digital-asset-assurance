const reportCache = {};
let currentReport;

async function loadReport(name) {
  if (!reportCache[name]) {
    const response = await fetch(`reports/${name}.json`);
    if (!response.ok) throw new Error(`Unable to load ${name} assessment (${response.status})`);
    reportCache[name] = await response.json();
  }
  currentReport = reportCache[name];
  render();
}

function render() {
  const report = currentReport;
  document.querySelector('#as-of').textContent = `AS OF ${report.as_of}`;
  document.querySelector('#product').textContent = report.product;
  document.querySelector('#decision').textContent = report.decision;
  document.querySelector('#rationale').textContent = report.rationale;
  document.querySelector('#decision-mark').className = report.decision.toLowerCase().replaceAll(' ', '-');
  document.querySelector('#count-total').textContent = report.control_count;
  document.querySelector('#count-pass').textContent = report.summary.PASS;
  document.querySelector('#count-partial').textContent = report.summary.PARTIAL;
  document.querySelector('#count-fail').textContent = report.summary.FAIL;
  document.querySelector('#coverage').textContent = `${report.evidence_coverage_percent}%`;
  document.querySelector('#critical').textContent = report.critical_findings.length;
  document.querySelector('#tab-controls').textContent = report.control_count;
  document.querySelector('#tab-evidence').textContent = report.controls.reduce((sum, control) => sum + control.evidence.length, 0);
  document.querySelectorAll('[data-scenario]').forEach((button) => button.classList.toggle('active', button.dataset.scenario === report.scenario_key));
  renderControls(report.controls);
  renderEvidence(report.controls);
  renderTrace(report);
}

function renderControls(controls) {
  document.querySelector('#control-rows').innerHTML = controls.map((control, index) => `<tr data-control="${index}">
    <td>${escapeHtml(control.id)}</td><td>${escapeHtml(control.domain)}</td><td>${escapeHtml(control.requirement)}</td>
    <td><span class="pill">${escapeHtml(control.severity)}</span></td>
    <td><span class="pill ${control.status.toLowerCase()}">${escapeHtml(control.status)}</span></td>
    <td>${control.blocking ? 'YES' : 'NO'}</td></tr>`).join('');
  document.querySelectorAll('#control-rows tr').forEach((row) => row.addEventListener('click', () => showControl(controls[Number(row.dataset.control)])));
}

function renderEvidence(controls) {
  const records = controls.flatMap((control) => control.evidence.map((item) => ({ ...item, control })));
  document.querySelector('#evidence-list').innerHTML = records.map(({ control, ...item }) => `<article class="evidence-card">
    <div class="evidence-meta"><span>${escapeHtml(item.id)} / ${escapeHtml(control.id)}</span><span class="pill ${item.status.toLowerCase()}">${escapeHtml(item.status)}</span></div>
    <h3>${escapeHtml(item.source)}</h3><p>Supports: ${escapeHtml(control.requirement)}</p>
    <div class="evidence-meta"><span>OBSERVED ${escapeHtml(item.observed_at)}</span><span>${item.status === 'STALE' ? `STALE · ${item.age_days}D / ${item.freshness_days}D LIMIT` : escapeHtml(control.status)}</span></div>
    <p>Integrity reference: <code>${escapeHtml(item.reference)}</code></p></article>`).join('');
}

function renderTrace(report) {
  const entries = [];
  if (report.decision === 'GO') entries.push('<strong>All assessed controls passed.</strong> Linked evidence is within freshness windows, and declared state matches each requirement.');
  for (const control of report.controls.filter((item) => item.status !== 'PASS')) {
    entries.push(`<strong>${escapeHtml(control.id)} · ${escapeHtml(control.status)}.</strong> ${escapeHtml(control.finding)} ${control.blocking ? 'Blocking control.' : ''}`);
  }
  for (const condition of report.conditions) entries.push(`<strong>Remediation · ${escapeHtml(condition.control_id)}.</strong> Owner: ${escapeHtml(condition.owner)}. ${escapeHtml(condition.requirement)}`);
  document.querySelector('#trace').innerHTML = entries.map((entry) => `<div class="trace-item">${entry}</div>`).join('');
}

function showControl(control) {
  const evidence = control.evidence.map((item) => `<div class="detail-box"><strong>${escapeHtml(item.id)} — ${escapeHtml(item.status)}</strong><br>${escapeHtml(item.source)} · observed ${escapeHtml(item.observed_at)}<br><code>${escapeHtml(item.reference)}</code></div>`).join('') || '<div class="detail-box">No linked evidence record.</div>';
  const stale = control.stale_details.length ? `<p>${control.stale_details.map((item) => `${escapeHtml(item.id)} is ${item.age_days} days old; freshness limit is ${item.freshness_days} days.`).join(' ')} The assurance engine cannot infer control effectiveness from stale evidence.</p>` : '';
  document.querySelector('#detail-content').innerHTML = `<span class="pill ${control.status.toLowerCase()}">${escapeHtml(control.status)}</span><h2>${escapeHtml(control.id)} · ${escapeHtml(control.name)}</h2><p>${escapeHtml(control.requirement)}</p><div class="detail-box"><strong>Owner</strong> ${escapeHtml(control.owner)}<br><strong>Severity</strong> ${escapeHtml(control.severity)} · <strong>Blocking</strong> ${control.blocking ? 'Yes' : 'No'}<br><strong>Observed state</strong> <code>${escapeHtml(String(control.system_state))}</code> · expected <code>${escapeHtml(control.expected_state)}</code></div><div class="detail-box"><strong>Finding</strong><br>${escapeHtml(control.finding)}</div>${stale}${evidence}<div class="detail-box"><strong>Remediation</strong><br>${escapeHtml(control.remediation)}</div>`;
  document.querySelector('#detail-dialog').showModal();
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
}

document.querySelectorAll('[data-scenario]').forEach((button) => button.addEventListener('click', () => loadReport(button.dataset.scenario)));
document.querySelectorAll('.tab').forEach((button) => button.addEventListener('click', () => {
  document.querySelectorAll('.tab, .view').forEach((item) => item.classList.remove('active'));
  button.classList.add('active');
  document.querySelector(`#view-${button.dataset.view}`).classList.add('active');
}));
document.querySelector('.close').addEventListener('click', () => document.querySelector('#detail-dialog').close());
document.querySelector('#detail-dialog').addEventListener('click', (event) => { if (event.target === event.currentTarget) event.currentTarget.close(); });
loadReport('go').catch((error) => { document.querySelector('#decision').textContent = 'DATA ERROR'; document.querySelector('#rationale').textContent = error.message; });
