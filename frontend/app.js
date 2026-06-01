const API = 'https://candid-nx0c.onrender.com';
let allResults = [], currentJobId = null, totalCandidates = 0, requiredSkillCount = 0;

const AVATAR_COLORS = [
  '#dbeafe:#1e40af', '#fce7f3:#9d174d', '#dcfce7:#166534',
  '#fef3c7:#92400e', '#ede9fe:#5b21b6', '#ffedd5:#9a3412'
];

const barColor = p => p >= 75 ? '#22c55e' : p >= 50 ? '#f59e0b' : '#ef4444';
const badgeCls = p => p >= 75 ? 'badge-green' : p >= 50 ? 'badge-amber' : 'badge-red';
const badgeLabel = p => p >= 75 ? 'Strong' : p >= 50 ? 'Partial' : 'Weak';
const initials = name => (name || '?').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
const avatarStyle = i => { const [bg, fg] = AVATAR_COLORS[i % AVATAR_COLORS.length].split(':'); return `background:${bg};color:${fg}`; };
const getSorted = () => [...allResults].sort((a, b) => b.match_percentage - a.match_percentage);

function toggleTheme() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
  document.getElementById('themeIcon').textContent = isDark ? '☽' : '○';
}

// --- Upload ---

function handleDragOver(e) { e.preventDefault(); document.getElementById('dropArea').classList.add('dragover'); }
function handleDragLeave() { document.getElementById('dropArea').classList.remove('dragover'); }
function handleDrop(e) { e.preventDefault(); handleDragLeave(); handleFiles(e.dataTransfer.files); }

async function handleFiles(files) {
  for (const file of files) {
    if (!file.name.endsWith('.pdf')) { logUpload(`${file.name} — not a PDF`, 'error'); continue; }
    logUpload(`Uploading ${file.name}...`, '');
    const form = new FormData();
    form.append('file', file);
    try {
      const res = await fetch(`${API}/candidates`, { method: 'POST', body: form });
      const d = await res.json();
      res.ok ? logUpload(`OK ${d.name} — ${d.skills_found} skills`, 'success')
              : logUpload(`Failed ${file.name}: ${d.detail}`, 'error');
    } catch { logUpload(`Failed ${file.name}: network error`, 'error'); }
  }
  loadSavedCandidates();
}

function logUpload(msg, cls) {
  const log = document.getElementById('uploadLog');
  const item = Object.assign(document.createElement('div'), { className: `upload-log-item ${cls} fade-in`, textContent: msg });
  log.appendChild(item);
  log.scrollTop = log.scrollHeight;
}

async function loadSavedCandidates() {
  try {
    const candidates = await fetch(`${API}/candidates`).then(r => r.json());
    totalCandidates = candidates.length;
    document.getElementById('candidateCount').textContent = `${totalCandidates} candidate${totalCandidates !== 1 ? 's' : ''}`;
  } catch {}
}

// --- Search ---

async function runSearch() {
  const query = document.getElementById('searchInput').value.trim();
  if (!query) return;
  const btn = document.getElementById('searchBtn');
  const label = document.getElementById('searchBtnLabel');
  btn.disabled = true;
  label.innerHTML = '<div class="spinner"></div>';
  try {
    const parsed = await fetch(`${API}/jobs/parse`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: query })
    }).then(r => r.json());

    const job = await fetch(`${API}/jobs`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: parsed.title || 'Search', description: query, required_skills: parsed.required_skills || [], nice_to_have: parsed.nice_to_have || [] })
    }).then(r => r.json());

    requiredSkillCount = (parsed.required_skills || []).length;
    currentJobId = job.job_id;
    const data = await fetch(`${API}/jobs/${currentJobId}/matches`).then(r => r.json());
    allResults = data.candidates || [];
    renderTable();
    updateStats();
  } catch {
    document.getElementById('resultsTitle').textContent = 'Search failed — is the server running?';
  } finally {
    btn.disabled = false;
    label.textContent = 'Search';
  }
}

function updateStats() {
  const wrap = document.getElementById('statsRow');
  if (!allResults.length) { wrap.style.display = 'none'; return; }
  wrap.style.display = 'grid';
  document.getElementById('statTotal').textContent = totalCandidates;
  document.getElementById('statAvg').textContent = allResults.length;
  document.getElementById('statTop').textContent = requiredSkillCount;
}

function renderTable() {
  const sorted = getSorted();
  document.getElementById('resultsTitle').textContent = `${sorted.length} candidate${sorted.length !== 1 ? 's' : ''} found`;

  if (!sorted.length) {
    document.getElementById('tableWrap').innerHTML = `
      <div class="empty-state">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <p>No candidates matched — try broader skills or upload more resumes</p>
      </div>`;
    return;
  }

  const rows = sorted.map((c, i) => {
    const pct = c.match_percentage;
    const top = (c.matched_skills || []).slice(0, 3);
    const extra = (c.matched_skills || []).length - 3;
    return `<tr onclick="openDrawer(${i})" data-idx="${i}">
      <td><div class="candidate-cell">
        <div class="avatar" style="${avatarStyle(i)}">${initials(c.name)}</div>
        <div><div class="candidate-name">${c.name || 'Unknown'}</div><div class="candidate-email">${c.email || '-'}</div></div>
      </div></td>
      <td><div class="score-bar-wrap">
        <div class="score-bar"><div class="score-bar-fill" style="width:${pct}%;background:${barColor(pct)}"></div></div>
        <span class="score-val">${pct}%</span>
      </div></td>
      <td><span class="req-cell">${c.required_match}</span></td>
      <td><div style="display:flex;flex-wrap:wrap;gap:2px">
        ${top.map(s => `<span class="skill-pill">${s}</span>`).join('')}
        ${extra > 0 ? `<span class="skill-pill">+${extra}</span>` : ''}
      </div></td>
      <td><span class="badge ${badgeCls(pct)}">${badgeLabel(pct)}</span></td>
    </tr>`;
  });

  document.getElementById('tableWrap').innerHTML = `
    <table>
      <thead><tr><th>Candidate</th><th style="min-width:140px">Match</th><th>Required</th><th>Top skills</th><th>Fit</th></tr></thead>
      <tbody>${rows.join('')}</tbody>
    </table>`;
}

// --- Drawer ---

function openDrawer(idx) {
  const c = getSorted()[idx];
  document.querySelectorAll('tbody tr').forEach(r => r.classList.toggle('selected', parseInt(r.dataset.idx) === idx));
  const pct = c.match_percentage;
  const color = barColor(pct);

  document.querySelector('.drawer-topbar').innerHTML = `
    <div class="drawer-header">
      <div class="drawer-avatar" style="${avatarStyle(idx)}">${initials(c.name)}</div>
      <div class="drawer-identity">
        <div class="drawer-name">${c.name || 'Unknown'}</div>
        <div class="drawer-sub">${c.email || 'No email'}</div>
      </div>
      <button class="drawer-close" onclick="closeDrawer()">x</button>
    </div>
    <div class="drawer-match-bar">
      <div class="drawer-match-pct" style="color:${color}">${pct}%</div>
      <div class="drawer-match-detail">
        <div class="drawer-match-label">match score</div>
        <div class="drawer-match-track"><div class="drawer-match-fill" style="width:${pct}%;background:${color}"></div></div>
        <div class="drawer-match-sub">${c.required_match} required skills &nbsp;·&nbsp; score ${c.skill_score}</div>
      </div>
    </div>`;

  document.getElementById('drawerBody').innerHTML = `
    <div class="drawer-section">
      <div class="drawer-section-label">Candidate Summary</div>
      <div class="summary-box" id="aiSummaryText"><span style="color:var(--text3)">Loading...</span></div>
    </div>
    <div class="drawer-section">
      <div class="drawer-section-label">Skills</div>
      <div class="skill-grid">
        ${(c.matched_skills || []).map(s => `<span class="skill-pill skill-matched">+ ${s}</span>`).join('')}
        ${(c.missing_skills || []).map(s => `<span class="skill-pill skill-missing">- ${s}</span>`).join('')}
      </div>
    </div>
    <div class="drawer-section" id="drawerExp"><div class="drawer-section-label">Experience</div><div style="color:var(--text3);font-size:12px">Loading...</div></div>
    <div class="drawer-section" id="drawerEdu"><div class="drawer-section-label">Education</div><div style="color:var(--text3);font-size:12px">Loading...</div></div>`;

  document.getElementById('drawer').classList.add('open');
  document.getElementById('drawerOverlay').classList.add('open');
  fetchCandidateDetail(c.id);
  generateAISummary(c);
}

async function fetchCandidateDetail(id) {
  try {
    const d = await fetch(`${API}/candidates/${id}`).then(r => r.ok ? r.json() : null);
    if (!d) return;

    document.getElementById('drawerExp').innerHTML = `
      <div class="drawer-section-label">Experience</div>
      ${(d.experiences || []).map(e => `
        <div class="exp-item">
          <div class="exp-title">${e.title || '-'}</div>
          <div class="exp-company">${e.company || '-'}</div>
          <div class="exp-dates">${e.start_date || '?'} to ${e.end_date || 'present'}${e.years_calculated ? ' — ' + e.years_calculated.toFixed(1) + 'y' : ''}</div>
          ${e.description ? `<div class="exp-desc">${e.description}</div>` : ''}
        </div>`).join('') || '<div style="color:var(--text3);font-size:12px">No experience data</div>'}`;

    document.getElementById('drawerEdu').innerHTML = `
      <div class="drawer-section-label">Education</div>
      ${(d.education || []).map(e => `
        <div class="edu-item">
          <div class="edu-degree">${e.degree || '-'} in ${e.field || '-'}</div>
          <div class="edu-inst">${e.institution || '-'}${e.graduation_year ? ' — ' + e.graduation_year : ''}</div>
        </div>`).join('') || '<div style="color:var(--text3);font-size:12px">No education data</div>'}`;
  } catch {}
}

async function generateAISummary(c) {
  try {
    const res = await fetch(`${API}/candidates/${c.id}/summary`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: currentJobId })
    });
    if (!res.ok) throw new Error();
    const d = await res.json();
    document.getElementById('aiSummaryText').innerHTML = d.summary;
  } catch {
    const fallback = `${c.required_match} required skills matched.${(c.missing_skills || []).length ? ' Missing: ' + c.missing_skills.slice(0, 3).join(', ') + '.' : ''}`;
    document.getElementById('aiSummaryText').innerHTML = `<span style="color:var(--text2);font-size:12px">${fallback}</span>`;
  }
}

function closeDrawer() {
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('drawerOverlay').classList.remove('open');
  document.querySelectorAll('tbody tr').forEach(r => r.classList.remove('selected'));
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDrawer(); });
document.getElementById('searchInput').addEventListener('keydown', e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) runSearch(); });

loadSavedCandidates();