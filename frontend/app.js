// State
let currentUser = null;
let currentCandidate = null;
let currentMatches = [];

// DOM Elements
const landingPage = document.getElementById('landing-page');
const dashboardView = document.getElementById('dashboard-view');
const authModal = document.getElementById('auth-modal');
const modalClose = document.getElementById('modal-close');
const modalTitle = document.getElementById('modal-title');
const modalSubtitle = document.getElementById('modal-subtitle');
const tabLoginBtn = document.getElementById('tab-login-btn');
const tabRegisterBtn = document.getElementById('tab-register-btn');
const authNameGroup = document.getElementById('auth-name-group');
const authSubmitBtn = document.getElementById('auth-submit-btn');
const authForm = document.getElementById('auth-form');
const authStatus = document.getElementById('auth-status');

let isRegisterMode = false;

// ================= MODAL & STAGE TRANSITIONS =================
function openAuthModal(registerMode = false) {
  isRegisterMode = registerMode;
  authStatus.textContent = '';
  authModal.classList.remove('hidden');

  if (isRegisterMode) {
    tabRegisterBtn.classList.add('active');
    tabLoginBtn.classList.remove('active');
    authNameGroup.classList.remove('hidden');
    modalTitle.textContent = 'Create Account';
    modalSubtitle.textContent = 'Sign up to build your profile and find internships';
    authSubmitBtn.innerHTML = '<span>Create Account</span>';
  } else {
    tabLoginBtn.classList.add('active');
    tabRegisterBtn.classList.remove('active');
    authNameGroup.classList.add('hidden');
    modalTitle.textContent = 'Welcome Back';
    modalSubtitle.textContent = 'Sign in to access your internship dashboard';
    authSubmitBtn.innerHTML = '<span>Sign In</span>';
  }
}

function closeAuthModal() {
  authModal.classList.add('hidden');
}

function enterDashboard(user) {
  currentUser = user;
  
  // Save session to localStorage
  localStorage.setItem('currentUser', JSON.stringify(user));
  localStorage.setItem('authToken', user.token || 'session_active');

  landingPage.classList.add('hidden');
  dashboardView.classList.remove('hidden');
  closeAuthModal();

  const name = user.full_name || 'Shaik Azra Anisha';
  const email = user.email || 'azrask24@gmail.com';
  
  document.getElementById('top-user-name').textContent = name;
  document.getElementById('top-user-email').textContent = email;
  
  // Set avatar initials
  const initials = name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  document.getElementById('top-user-avatar').textContent = initials || 'AZ';

  // Seed profile form
  document.getElementById('prof-name').value = name;
  document.getElementById('prof-email').value = email;
}

// Landing Page Event Listeners
document.getElementById('btn-open-login').addEventListener('click', () => openAuthModal(false));
document.getElementById('btn-open-register').addEventListener('click', () => openAuthModal(true));
document.getElementById('hero-get-started').addEventListener('click', () => openAuthModal(true));
document.getElementById('hero-guest-btn').addEventListener('click', () => {
  enterDashboard({ full_name: 'Guest User', email: 'guest@example.com' });
});

modalClose.addEventListener('click', closeAuthModal);
tabLoginBtn.addEventListener('click', () => openAuthModal(false));
tabRegisterBtn.addEventListener('click', () => openAuthModal(true));

// Auth Form Submit
authForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const email = document.getElementById('auth-email').value;
  const name = isRegisterMode ? document.getElementById('auth-name').value : (email.split('@')[0]);

  authStatus.className = 'status';
  authStatus.textContent = 'Authenticating...';

  setTimeout(() => {
    enterDashboard({ full_name: name || 'Applicant User', email: email });
  }, 400);
});

// Logout
document.getElementById('btn-logout').addEventListener('click', () => {
  currentUser = null;
  currentCandidate = null;
  localStorage.removeItem('currentUser');
  localStorage.removeItem('authToken');
  localStorage.removeItem('candidateProfile');
  localStorage.removeItem('userApplications');
  localStorage.removeItem('cachedAtsScore');
  dashboardView.classList.add('hidden');
  landingPage.classList.remove('hidden');
});

// ================= DASHBOARD TAB NAVIGATION =================
const navItems = document.querySelectorAll('.nav-item');
const tabPanes = document.querySelectorAll('.tab-pane');

navItems.forEach(item => {
  item.addEventListener('click', () => {
    navItems.forEach(n => n.classList.remove('active'));
    tabPanes.forEach(p => p.classList.remove('active'));
    item.classList.add('active');
    document.getElementById(item.getAttribute('data-tab')).classList.add('active');
  });
});

// Theme Switcher
const themeToggle = document.getElementById('theme-toggle');
const themeText = document.getElementById('theme-text');
themeToggle.addEventListener('click', () => {
  const root = document.documentElement;
  const isDark = root.getAttribute('data-theme') === 'dark';
  root.setAttribute('data-theme', isDark ? 'light' : 'dark');
  themeText.textContent = isDark ? 'Dark Mode' : 'Light Mode';
});

// ================= RESUME PARSING & MATCHING =================
const fileInput = document.getElementById('resume');
const dropzoneText = document.getElementById('dropzone-text');
const analyzeButton = document.getElementById('analyze');
const status = document.getElementById('status');
const matchesSection = document.getElementById('matches-section');
const matchesEl = document.getElementById('matches');
const explanationEl = document.getElementById('explanation');

fileInput.addEventListener('change', () => {
  if (fileInput.files.length > 0) {
    dropzoneText.innerHTML = `Selected: <strong>${fileInput.files[0].name}</strong>`;
  }
});

analyzeButton.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) {
    status.className = 'status error';
    status.textContent = 'Please choose a resume file (.pdf/.docx).';
    return;
  }
  const form = new FormData();
  form.append('file', file);
  status.className = 'status';
  status.textContent = 'Parsing profile and calculating vector matches...';
  analyzeButton.disabled = true;

  try {
    const res = await fetch('/internships/match-resume', { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Analysis failed');

    currentCandidate = data.candidate;
    currentMatches = data.matches;
    localStorage.setItem('candidateProfile', JSON.stringify(currentCandidate));

    populateProfileForm(data.candidate);
    renderMatches(data.matches);
    explanationEl.textContent = data.explanation || 'RAG explanation ready.';
    matchesSection.classList.remove('hidden');
    status.textContent = 'Analysis complete. Profile auto-populated!';
    
    // Auto-scan ATS Resume Score
    fetchATSScore(data.candidate);
  } catch (err) {
    status.className = 'status error';
    status.textContent = err.message;
  } finally {
    analyzeButton.disabled = false;
  }
});

// Auto-Populate Profile
function populateProfileForm(cand) {
  if (!cand) return;
  document.getElementById('prof-name').value = cand.full_name || '';
  document.getElementById('prof-email').value = cand.email || '';
  document.getElementById('prof-phone').value = cand.phone || '';
  document.getElementById('prof-edu').value = Array.isArray(cand.education) ? cand.education.map(e => typeof e === 'object' ? Object.values(e).join(', ') : e).join('; ') : (cand.education || '');
  
  const allSkills = [...new Set([...(cand.skills || []), ...(cand.technical_skills || [])])];
  document.getElementById('prof-skills').value = allSkills.join(', ');
  document.getElementById('prof-skills-chips').innerHTML = allSkills.map(s => `<span class="chip">${s}</span>`).join('');
  
  document.getElementById('prof-exp').value = Array.isArray(cand.internships) ? cand.internships.map(i => typeof i === 'object' ? `${i.role || i.title} at ${i.company}` : i).join('; ') : '';
  document.getElementById('prof-projects').value = Array.isArray(cand.projects) ? cand.projects.map(p => typeof p === 'object' ? `${p.name || p.title}: ${p.description || ''}` : p).join('\n') : '';

  if (cand.full_name) document.getElementById('top-user-name').textContent = cand.full_name;
  if (cand.email) document.getElementById('top-user-email').textContent = cand.email;
}

document.getElementById('profile-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const pStatus = document.getElementById('profile-status');
  const skillsArray = document.getElementById('prof-skills').value.split(',').map(s => s.trim()).filter(Boolean);
  
  currentCandidate = {
    full_name: document.getElementById('prof-name').value,
    email: document.getElementById('prof-email').value,
    phone: document.getElementById('prof-phone').value,
    education: document.getElementById('prof-edu').value,
    skills: skillsArray,
    experience: document.getElementById('prof-exp').value,
    projects: document.getElementById('prof-projects').value
  };

  localStorage.setItem('candidateProfile', JSON.stringify(currentCandidate));

  document.getElementById('prof-skills-chips').innerHTML = skillsArray.map(s => `<span class="chip">${s}</span>`).join('');
  pStatus.textContent = 'Profile successfully updated!';
});

// Render Match Cards
function renderMatches(matches) {
  matchesEl.innerHTML = matches.map((m, i) => `
    <article class="match">
      <div class="match-head">
        <div>
          <h3 class="match-title">${i + 1}. ${m.title}</h3>
          <span class="match-company">${m.company}</span>
        </div>
        <div class="score-badge">${(m.similarity_score * 100).toFixed(1)}% match</div>
      </div>
      <p style="font-size: 0.92rem; color: var(--text-secondary); margin-bottom: 12px;">${m.description || ''}</p>
      <div class="chip-container">
        ${(m.required_skills || []).map(s => `<span class="chip">${s}</span>`).join('')}
      </div>
      <div class="match-actions">
        <button class="btn-primary btn-sm" onclick="applyToInternship('${m.title}', '${m.company}', ${JSON.stringify(m.required_skills || []).replace(/"/g, '&quot;')})">Apply Now</button>
        <button class="btn-secondary btn-sm" onclick="openCoverLetterPrep('${m.title}', '${m.company}')">Generate Cover Letter</button>
      </div>
    </article>
  `).join('');
}

// Toast helper
function showToast(message) {
  let toast = document.getElementById('toast-notification');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast-notification';
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.background = '#10b981';
    toast.style.color = '#ffffff';
    toast.style.padding = '12px 24px';
    toast.style.borderRadius = '8px';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    toast.style.zIndex = '9999';
    toast.style.fontWeight = '600';
    toast.style.fontSize = '0.9rem';
    toast.style.transition = 'opacity 0.3s ease';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.style.opacity = '1';
  toast.style.display = 'block';
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => { toast.style.display = 'none'; }, 300);
  }, 3000);
}

// Apply Action
window.applyToInternship = async function(title, company, requiredSkills) {
  const candidateSkills = currentCandidate ? currentCandidate.skills : ['Python', 'SQL', 'NumPy', 'Pandas'];
  const userEmail = currentUser ? currentUser.email : 'azrask24@gmail.com';

  try {
    const res = await fetch('/internships/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_email: userEmail,
        internship_id: title.replace(/\s+/g, '-').toLowerCase(),
        internship_title: title,
        company: company,
        required_skills: requiredSkills,
        candidate_skills: candidateSkills
      })
    });
    if (!res.ok) throw new Error('Failed to submit application');
    await res.json();
    showToast('Application submitted successfully!');
    loadApplications();
  } catch (err) {
    showToast(`Error: ${err.message}`);
  }
};

// Render applications and skill gaps on frontend
function renderApplicationsAndGaps(apps) {
  document.getElementById('app-count-badge').textContent = `${apps.length} Applications`;

  const appContainer = document.getElementById('applications-list');
  const gapContainer = document.getElementById('skillgap-container');

  if (apps.length === 0) {
    appContainer.innerHTML = `<p style="color: var(--text-muted);">No applications submitted yet.</p>`;
    gapContainer.innerHTML = `<p style="color: var(--text-muted);">Apply to an internship to view skill gap breakdown.</p>`;
    return;
  }

  // 1. RENDER APPLIED JOBS
  appContainer.innerHTML = apps.map(a => {
    return `
    <div class="match dashboard-card" style="margin-bottom: 20px; padding: 20px; border-radius: 12px; border: 1px solid var(--border-subtle); background: var(--bg-card-elevated); width: 100%; box-sizing: border-box;">
      <div class="match-head" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
        <div>
          <h3 class="match-title" style="margin: 0; font-size: 1.15rem; font-weight: 700;">${a.internship_title}</h3>
          <span class="match-company" style="font-size: 0.9rem; color: var(--text-secondary);">${a.company}</span>
          <div style="margin-top: 6px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
            <span class="badge" style="font-size: 0.75rem; background: var(--bg-subtle); padding: 2px 8px; border-radius: 4px;">ID: ${a.id}</span>
            <span class="badge" style="font-size: 0.75rem; background: rgba(59, 130, 246, 0.15); color: #3b82f6; padding: 2px 8px; border-radius: 4px;">Applied: ${a.applied_date}</span>
            <span class="badge" style="font-size: 0.75rem; background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald); padding: 2px 8px; border-radius: 4px;">Status: ${a.status}</span>
          </div>
        </div>
        <div class="readiness-gauge" style="background: rgba(16, 185, 129, 0.1); color: var(--accent-emerald); border: 1px solid rgba(16, 185, 129, 0.2); padding: 6px 12px; border-radius: 20px; font-weight: 700; font-size: 0.85rem; white-space: nowrap;">
          ${Number(a.readiness_score).toFixed(0)}% Match Readiness
        </div>
      </div>
      
      <div class="pipeline-step-row" style="display: flex; justify-content: space-between; margin: 20px 0; background: var(--bg-subtle); padding: 14px; border-radius: 10px;">
        ${a.application_stages.map(s => {
          let dotClass = 'upcoming';
          if (s.status === 'Completed') dotClass = 'completed';
          else if (s.status === 'In Progress') dotClass = 'in-progress';
          return `
            <div class="pipeline-step" style="display: flex; flex-direction: column; align-items: center; text-align: center; flex: 1;">
              <div class="step-dot ${dotClass}" style="margin-bottom: 6px;"></div>
              <span style="font-size: 0.75rem; font-weight: 600;">${s.stage}</span>
              <small style="font-size: 0.68rem; color: var(--text-muted);">${s.status}</small>
            </div>
          `;
        }).join('')}
      </div>

      <div class="card-actions" style="display: flex; gap: 10px; margin-top: 14px;">
        <button class="btn-secondary btn-sm" onclick="viewSkillGap('${a.internship_title.replace(/'/g, "\\'")}', '${a.company.replace(/'/g, "\\'")}')">View Skill Gap Breakdown</button>
        <button class="btn-primary btn-sm" onclick="openCoverLetterPrep('${a.internship_title.replace(/'/g, "\\'")}', '${a.company.replace(/'/g, "\\'")}')">Generate Custom Cover Letter</button>
      </div>
    </div>
    `;
  }).join('');

  // 2. RENDER SKILL GAPS
  gapContainer.innerHTML = apps.map(a => {
    const cardId = `gap-card-${a.internship_title.replace(/\s+/g, '-').toLowerCase()}-${a.company.replace(/\s+/g, '-').toLowerCase()}`;
    return `
    <div id="${cardId}" class="match skill-gap-card" style="margin-bottom: 20px; padding: 20px; border-radius: 12px; border: 1px solid var(--border-subtle); background: var(--bg-card-elevated); width: 100%; box-sizing: border-box; transition: all 0.3s ease;">
      <div class="gap-card-header" style="margin-bottom: 16px;">
        <h3 class="match-title" style="margin: 0; font-size: 1.15rem; font-weight: 700;">${a.internship_title}</h3>
        <span class="match-company" style="font-size: 0.9rem; color: var(--text-secondary);">${a.company}</span>
        
        <div class="readiness-bar-container" style="margin-top: 12px;">
          <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600; margin-bottom: 4px;">
            <span>Overall Readiness Score</span>
            <span>${Number(a.readiness_score).toFixed(0)}%</span>
          </div>
          <div class="progress-bar-bg" style="width: 100%; height: 8px; background: rgba(255, 255, 255, 0.1); border-radius: 4px; overflow: hidden;">
            <div class="progress-bar-fill" style="width: ${a.readiness_score}%; height: 100%; background: var(--accent-emerald); border-radius: 4px;"></div>
          </div>
        </div>
      </div>

      <div style="margin: 14px 0;">
        <strong style="font-size: 0.88rem; color: var(--text-secondary);">Matched Skills (${a.matched_skills.length})</strong>
        <div class="chip-container" style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 8px;">
          ${a.matched_skills.map(s => `<span class="chip-matched" style="background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald); padding: 4px 10px; border-radius: 6px; font-size: 0.82rem; font-weight: 600;">✓ ${s}</span>`).join('') || '<span style="color: var(--text-muted); font-size: 0.85rem;">None matched</span>'}
        </div>
      </div>

      <div style="margin: 14px 0;">
        <strong style="font-size: 0.88rem; color: var(--text-secondary);">Skill Gaps & Missing Requirements (${a.missing_skills.length})</strong>
        <div class="chip-container" style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 8px;">
          ${a.missing_skills.map(s => `<span class="chip-gap" style="background: rgba(239, 68, 68, 0.15); color: var(--error); padding: 4px 10px; border-radius: 6px; font-size: 0.82rem; font-weight: 600;">✕ ${s}</span>`).join('') || '<span class="chip-matched" style="background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald); padding: 4px 10px; border-radius: 6px; font-size: 0.82rem; font-weight: 600;">✓ All Required Skills Met!</span>'}
        </div>
      </div>

      <div class="learning-plan" style="margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--border-subtle);">
        <strong style="font-size: 0.88rem; color: var(--text-secondary); display: block; margin-bottom: 8px;">Actionable Learning Plan</strong>
        <ul style="margin: 0; padding-left: 20px; font-size: 0.85rem; line-height: 1.6; color: var(--text-secondary);">
          ${a.learning_recommendations.map(rec => `<li style="margin-bottom: 6px;">${rec}</li>`).join('')}
        </ul>
      </div>
    </div>
    `;
  }).join('');
}

// Load Applications & Skill Gaps from Backend
async function loadApplications() {
  const email = currentUser ? currentUser.email : 'azrask24@gmail.com';
  try {
    const res = await fetch(`/internships/applications?email=${encodeURIComponent(email)}`);
    const apps = await res.json();
    if (!res.ok) throw new Error(apps.detail || 'Failed to fetch applications');
    
    // Save to localStorage
    localStorage.setItem('userApplications', JSON.stringify(apps));
    
    renderApplicationsAndGaps(apps);
  } catch (err) {
    console.error('Failed to load applications:', err);
  }
}

// View Skill Gap Breakdown Action
window.viewSkillGap = function(title, company) {
  const tabItem = document.querySelector('[data-tab="tab-skillgap"]');
  if (tabItem) tabItem.click();
  
  const cardId = `gap-card-${title.replace(/\s+/g, '-').toLowerCase()}-${company.replace(/\s+/g, '-').toLowerCase()}`;
  setTimeout(() => {
    const card = document.getElementById(cardId);
    if (card) {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Temporary highlight pulse
      card.style.borderColor = '#10b981';
      card.style.boxShadow = '0 0 15px rgba(16, 185, 129, 0.3)';
      setTimeout(() => {
        card.style.borderColor = 'var(--border-subtle)';
        card.style.boxShadow = 'none';
      }, 2000);
    }
  }, 150);
};

// ATS Scorer Client Handlers
async function fetchATSScore(candidate) {
  const statusEl = document.getElementById('ats-scan-status');
  if (statusEl) {
    statusEl.className = 'status';
    statusEl.textContent = 'Analyzing resume with Gemini ATS Audit...';
  }

  try {
    const res = await fetch('/internships/ats-score', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        candidate: candidate || currentCandidate || { full_name: 'Applicant', skills: [] }
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'ATS scoring failed');

    localStorage.setItem('cachedAtsScore', JSON.stringify(data));
    renderATSScore(data);
    if (statusEl) {
      statusEl.textContent = 'ATS review completed!';
    }
  } catch (err) {
    console.error(err);
    if (statusEl) {
      statusEl.className = 'status error';
      statusEl.textContent = `Error: ${err.message}`;
    }
  }
}

function renderATSScore(scoreData) {
  if (!scoreData) return;

  const score = scoreData.overall_score || 0;
  const grade = scoreData.grade || 'Needs Optimization';
  const breakdown = scoreData.breakdown || {};

  // Update gauge text
  const scoreEl = document.getElementById('ats-gauge-score');
  if (scoreEl) scoreEl.textContent = score;

  // Update conic gradient background for gauge circle
  const gauge = document.querySelector('.ats-gauge-container');
  if (gauge) {
    gauge.style.setProperty('--score-pct', `${score}%`);
    gauge.style.background = `conic-gradient(var(--accent-emerald) ${score}%, rgba(255,255,255,0.08) ${score}%)`;
  }

  // Update status badge styling
  const gradeBadge = document.getElementById('ats-grade-badge');
  if (gradeBadge) {
    gradeBadge.textContent = grade;
    if (score >= 80) {
      gradeBadge.style.background = 'rgba(16, 185, 129, 0.15)';
      gradeBadge.style.color = 'var(--accent-emerald)';
    } else {
      gradeBadge.style.background = 'rgba(245, 158, 11, 0.15)';
      gradeBadge.style.color = 'var(--accent-amber)';
    }
  }

  // Update progress bars & scores text
  const categories = [
    { key: 'impact_metrics', textId: 'ats-breakdown-impact', fillId: 'ats-fill-impact', max: 25 },
    { key: 'action_verbs', textId: 'ats-breakdown-verbs', fillId: 'ats-fill-verbs', max: 20 },
    { key: 'section_completeness', textId: 'ats-breakdown-completeness', fillId: 'ats-fill-completeness', max: 20 },
    { key: 'technical_depth', textId: 'ats-breakdown-depth', fillId: 'ats-fill-depth', max: 20 },
    { key: 'formatting_clarity', textId: 'ats-breakdown-formatting', fillId: 'ats-fill-formatting', max: 15 }
  ];

  categories.forEach(c => {
    const val = breakdown[c.key] || 0;
    const textEl = document.getElementById(c.textId);
    const fillEl = document.getElementById(c.fillId);

    if (textEl) textEl.textContent = `${val} / ${c.max}`;
    if (fillEl) {
      const pct = (val / c.max) * 100;
      fillEl.style.width = `${pct}%`;
    }
  });

  // Update Strengths
  const strengthsList = document.getElementById('ats-strengths-list');
  if (strengthsList) {
    const strengths = scoreData.strengths || [];
    strengthsList.innerHTML = strengths.map(s => `<li style="margin-bottom: 6px;">✓ ${s}</li>`).join('') || '<li style="color: var(--text-muted);">None noted</li>';
  }

  // Update Improvements
  const improvementsList = document.getElementById('ats-improvements-list');
  if (improvementsList) {
    const improvements = scoreData.critical_improvements || [];
    improvementsList.innerHTML = improvements.map(s => `<li style="margin-bottom: 6px;">• ${s}</li>`).join('') || '<li style="color: var(--text-muted);">None noted</li>';
  }

  // Update Keywords suggestion chips
  const keywordsContainer = document.getElementById('ats-keywords-container');
  if (keywordsContainer) {
    const keywords = scoreData.keyword_suggestions || [];
    keywordsContainer.innerHTML = keywords.map(s => `<span class="chip" style="background: rgba(255,255,255,0.06); padding: 4px 10px; border-radius: 6px; font-size: 0.8rem;">${s}</span>`).join('') || '<span style="color: var(--text-muted); font-size: 0.85rem;">None suggested</span>';
  }
}

// Bind Re-scan click handler
const btnRescanAts = document.getElementById('btn-rescan-ats');
if (btnRescanAts) {
  btnRescanAts.addEventListener('click', () => {
    const cand = currentCandidate || { full_name: 'Applicant', skills: [] };
    fetchATSScore(cand);
  });
}

// Cover Letter Generator Trigger
window.openCoverLetterPrep = function(title, company) {
  document.getElementById('cl-title').value = title;
  document.getElementById('cl-company').value = company;
  document.querySelector('[data-tab="tab-coverletter"]').click();
};

document.getElementById('btn-gen-coverletter').addEventListener('click', async () => {
  const title = document.getElementById('cl-title').value;
  const company = document.getElementById('cl-company').value;
  const tone = document.getElementById('cl-tone').value;
  const emphasis = document.getElementById('cl-emphasis').value;
  const statusEl = document.getElementById('cl-status');

  if (!title || !company) {
    statusEl.className = 'status error';
    statusEl.textContent = 'Please provide the internship title and company.';
    return;
  }

  statusEl.className = 'status';
  statusEl.textContent = 'Drafting customized cover letter with Gemini...';

  try {
    const res = await fetch('/internships/generate-cover-letter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        candidate: currentCandidate || { full_name: 'Applicant', skills: ['Python', 'SQL'] },
        internship_title: title,
        company: company,
        tone: tone,
        emphasis: emphasis
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Cover letter generation failed');

    document.getElementById('cl-output').value = data.cover_letter;
    document.getElementById('coverletter-result-box').classList.remove('hidden');
    statusEl.textContent = 'Cover letter created!';
  } catch (err) {
    statusEl.className = 'status error';
    statusEl.textContent = err.message;
  }
});

// Copy to Clipboard Listener
const btnCopyCl = document.getElementById('btn-copy-cl');
if (btnCopyCl) {
  btnCopyCl.addEventListener('click', async () => {
    const clText = document.getElementById('cl-output').value;
    try {
      await navigator.clipboard.writeText(clText);
      const originalText = btnCopyCl.textContent;
      btnCopyCl.textContent = 'Copied!';
      setTimeout(() => {
        btnCopyCl.textContent = originalText;
      }, 2000);
    } catch (err) {
      console.error('Failed to copy cover letter: ', err);
      alert('Failed to copy to clipboard.');
    }
  });
}

// Session restoration on page load
function initSession() {
  const savedUser = localStorage.getItem('currentUser');
  if (savedUser) {
    try {
      const parsedUser = JSON.parse(savedUser);
      enterDashboard(parsedUser);
    } catch (e) {
      localStorage.removeItem('currentUser');
    }
  }
  
  const savedProfile = localStorage.getItem('candidateProfile');
  if (savedProfile) {
    try {
      currentCandidate = JSON.parse(savedProfile);
      populateProfileForm(currentCandidate);
    } catch (e) {
      localStorage.removeItem('candidateProfile');
    }
  }

  const savedApps = localStorage.getItem('userApplications');
  if (savedApps) {
    try {
      const parsedApps = JSON.parse(savedApps);
      renderApplicationsAndGaps(parsedApps);
    } catch (e) {
      localStorage.removeItem('userApplications');
    }
  }

  const savedAts = localStorage.getItem('cachedAtsScore');
  if (savedAts) {
    try {
      const parsedAts = JSON.parse(savedAts);
      renderATSScore(parsedAts);
    } catch (e) {
      localStorage.removeItem('cachedAtsScore');
    }
  }
}

document.addEventListener('DOMContentLoaded', initSession);

// ================= FLOATING CHATBOT COPILOT LOGIC =================
const chatToggleBtn = document.getElementById('chat-toggle-btn');
const chatWindow = document.getElementById('chat-window');
const chatCloseBtn = document.getElementById('chat-close-btn');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');

if (chatToggleBtn && chatWindow) {
  chatToggleBtn.addEventListener('click', () => {
    chatWindow.classList.toggle('hidden');
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });
}

if (chatCloseBtn && chatWindow) {
  chatCloseBtn.addEventListener('click', () => {
    chatWindow.classList.add('hidden');
  });
}

function appendChatMessage(sender, text) {
  const bubble = document.createElement('div');
  
  if (sender === 'user') {
    bubble.className = 'chat-bubble user';
    bubble.style.alignSelf = 'flex-end';
    bubble.style.maxWidth = '85%';
    bubble.style.padding = '10px 14px';
    bubble.style.borderRadius = '14px';
    bubble.style.borderTopRightRadius = '4px';
    bubble.style.background = 'linear-gradient(135deg, #a855f7 0%, #3b82f6 100%)';
    bubble.style.color = '#ffffff';
    bubble.style.fontSize = '0.85rem';
    bubble.style.lineHeight = '1.5';
  } else {
    bubble.className = 'chat-bubble ai';
    bubble.style.alignSelf = 'flex-start';
    bubble.style.maxWidth = '85%';
    bubble.style.padding = '10px 14px';
    bubble.style.borderRadius = '14px';
    bubble.style.borderTopLeftRadius = '4px';
    bubble.style.border = '1px solid var(--border-subtle)';
    bubble.style.background = 'var(--bg-subtle)';
    bubble.style.fontSize = '0.85rem';
    bubble.style.lineHeight = '1.5';
    bubble.style.color = 'var(--text-secondary)';
  }
  
  const formattedText = text
    .replace(/\n/g, '<br>')
    .replace(/\*\s(.*?)(\<br\>|$)/g, '<li style="margin-left: 10px; margin-bottom: 2px;">$1</li>');
    
  bubble.innerHTML = formattedText;
  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return bubble;
}

if (chatForm) {
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message) return;

    appendChatMessage('user', message);
    chatInput.value = '';

    const thinkingBubble = appendChatMessage('ai', 'Thinking...');

    try {
      const res = await fetch('/internships/chat-assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          candidate: currentCandidate,
          internships_context: currentMatches
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Chat assistant error');

      thinkingBubble.innerHTML = data.reply.replace(/\n/g, '<br>').replace(/\*\s(.*?)(\<br\>|$)/g, '<li style="margin-left: 10px; margin-bottom: 2px;">$1</li>');
    } catch (err) {
      thinkingBubble.textContent = `Error: ${err.message}`;
    }
  });
}

document.querySelectorAll('.quick-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const query = chip.getAttribute('data-query');
    if (query && chatInput) {
      chatInput.value = query;
      chatForm.dispatchEvent(new Event('submit'));
    }
  });
});

loadApplications();