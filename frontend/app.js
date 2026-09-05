/* ============================================================
   app.js — TACOS frontend logic
   ============================================================ */

"use strict";

// ---- State ----------------------------------------------------------------
let allSkills = [];      // fetched from /api/skills
let importance = 5;      // currently selected star rating

// ---- DOM refs -------------------------------------------------------------
const starRow         = document.getElementById("star-row");
const importanceInput = document.getElementById("importance");
const skillsContainer = document.getElementById("skills-container");
const addSkillBtn     = document.getElementById("add-skill-btn");
const mvpRow          = document.getElementById("mvp-row");
const mvpSelect       = document.getElementById("mvp-select");
const buildBtn        = document.getElementById("build-btn");
const loadingEl       = document.getElementById("loading");
const resultsPanel    = document.getElementById("results-panel");
const resultsContent  = document.getElementById("results-content");

// ---- Initialise -----------------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
  await loadSkills();
  setupStars();
  addSkillChip();          // start with one skill row
});

// ---- Load skills from backend --------------------------------------------
async function loadSkills() {
  try {
    const res = await fetch("/api/skills");
    const data = await res.json();
    allSkills = data.skills || [];
  } catch {
    allSkills = [];
    alert("Could not load skills from the backend. Is the server running?");
  }
}

// ---- Star rating ----------------------------------------------------------
function setupStars() {
  const stars = starRow.querySelectorAll(".star");
  stars.forEach(star => {
    star.addEventListener("click", () => {
      importance = parseInt(star.dataset.val, 10);
      importanceInput.value = importance;
      stars.forEach(s => {
        s.classList.toggle("active", parseInt(s.dataset.val, 10) <= importance);
      });
    });
  });
}

// ---- Skill chip management -----------------------------------------------
addSkillBtn.addEventListener("click", addSkillChip);

function addSkillChip() {
  const chip = document.createElement("div");
  chip.className = "skill-chip";

  const sel = document.createElement("select");
  sel.innerHTML = allSkills.map(s => `<option value="${s}">${s}</option>`).join("");
  sel.addEventListener("change", updateMvpOptions);

  const removeBtn = document.createElement("button");
  removeBtn.className = "chip-remove";
  removeBtn.title = "Remove";
  removeBtn.innerHTML = "✕";
  removeBtn.addEventListener("click", () => {
    chip.remove();
    updateMvpOptions();
  });

  chip.appendChild(sel);
  chip.appendChild(removeBtn);
  skillsContainer.appendChild(chip);
  updateMvpOptions();
}

function getSelectedSkills() {
  const chips = skillsContainer.querySelectorAll(".skill-chip select");
  return [...chips].map(s => s.value);
}

function updateMvpOptions() {
  const skills = getSelectedSkills();
  const current = mvpSelect.value;

  if (skills.length === 0) {
    mvpRow.style.display = "none";
    return;
  }

  mvpRow.style.display = "";
  mvpSelect.innerHTML = skills.map(s =>
    `<option value="${s}" ${s === current ? "selected" : ""}>${s}</option>`
  ).join("");
}

// ---- Build team -----------------------------------------------------------
buildBtn.addEventListener("click", buildTeam);

async function buildTeam() {
  const projectName    = document.getElementById("project-name").value.trim() || "Unnamed Project";
  const teamSize       = parseInt(document.getElementById("team-size").value, 10);
  const requiredSkills = getSelectedSkills();
  const mvpSkill       = mvpSelect.value;

  if (!requiredSkills.length) { alert("Please add at least one required skill."); return; }
  if (!mvpSkill)               { alert("Please select an MVP skill."); return; }
  if (!teamSize || teamSize < 1){ alert("Team size must be at least 1."); return; }

  // UI: loading state
  buildBtn.classList.add("hidden");
  loadingEl.classList.remove("hidden");
  resultsPanel.classList.add("hidden");

  try {
    const res = await fetch("/api/build-team", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_name: projectName,
        team_size: teamSize,
        importance: importance,
        required_skills: requiredSkills,
        mvp_skill: mvpSkill,
      }),
    });

    const data = await res.json();

    if (data.error && Object.keys(data).length === 1) {
      alert("Error: " + data.error);
      return;
    }

    renderResults(data);
    resultsPanel.classList.remove("hidden");
    resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });

  } catch (err) {
    alert("Network error: " + err.message);
  } finally {
    buildBtn.classList.remove("hidden");
    loadingEl.classList.add("hidden");
  }
}

// ---- Render results -------------------------------------------------------
function renderResults(data) {
  const { project_summary, mvp, selected_team, role_results, team_chemistry, warnings } = data;

  const stars = "★".repeat(project_summary.importance) + "☆".repeat(5 - project_summary.importance);

  let html = "";

  // -- Project summary strip
  html += `<div class="project-summary">
    <div class="summary-item">Project: <strong>${esc(project_summary.project_name)}</strong></div>
    <div class="summary-item">Team Size: <strong>${project_summary.team_size}</strong></div>
    <div class="summary-item">Importance: <strong style="color:var(--accent2)">${stars}</strong></div>
    <div class="summary-item">MVP Skill: <strong>${esc(project_summary.mvp_skill)}</strong></div>
    <div class="summary-item">Thresholds: <strong>MVP ≥ ${project_summary.thresholds.mvp_minimum} · Members ≥ ${project_summary.thresholds.candidate_minimum}</strong></div>
  </div>`;

  // -- MVP card
  html += `<div>
    <div class="results-section-title">⭐ MVP</div>
    <div class="mvp-card">
      <div class="mvp-badge">🏆</div>
      <div class="mvp-info">
        <h3>${esc(mvp.employee_name)}</h3>
        <div class="mvp-meta">ID #${mvp.employee_id} · ${esc(mvp.mvp_skill)}</div>
      </div>
      <div class="mvp-score">
        <div class="score-val">${mvp.skill_score}</div>
        <div class="score-label">/ 100</div>
      </div>
    </div>
  </div>`;

  // -- Team table
  const nonMvp = selected_team.filter(m => !m.is_mvp);
  if (nonMvp.length > 0) {
    html += `<div>
      <div class="results-section-title">Team Members</div>
      <table class="team-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Role</th>
            <th>Skill Score</th>
            <th>Preference</th>
            <th>Chemistry</th>
            <th>Final Score</th>
          </tr>
        </thead>
        <tbody>`;

    for (const m of nonMvp) {
      const pref  = fmt(m.skill_preference_score);
      const chem  = fmt(m.normalized_team_chemistry);
      const final = fmt(m.final_candidate_score);
      html += `<tr>
        <td><strong>${esc(m.employee_name)}</strong> <span style="color:var(--muted);font-size:.78rem">#${m.employee_id}</span></td>
        <td>${esc(m.role)}</td>
        <td><span class="score-pill ${pillClass(m.skill_score)}">${m.skill_score}</span></td>
        <td>${pref !== "—" ? pref : "—"}</td>
        <td>${chem !== "—" ? chem : "—"}</td>
        <td><strong>${final}</strong></td>
      </tr>`;
    }

    html += `</tbody></table></div>`;
  }

  // -- Alternatives
  const rolesWithAlts = role_results.filter(rr => !rr.error && rr.alternatives && rr.alternatives.length > 0);
  if (rolesWithAlts.length > 0) {
    html += `<div>
      <div class="results-section-title">Alternative Candidates</div>
      <div class="alt-grid">`;

    for (const rr of rolesWithAlts) {
      html += `<div class="alt-role-block">
        <div class="alt-role-name">${esc(rr.role)}</div>
        <div style="font-size:.78rem;color:var(--muted);margin-bottom:8px">
          Selected: <strong style="color:var(--text)">${esc(rr.selected.employee_name)}</strong>
          (Score: ${rr.selected.skill_score} · Final: ${fmt(rr.selected.final_candidate_score)})
        </div>
        <div class="alt-list">`;

      for (const alt of rr.alternatives) {
        html += `<div class="alt-item">
          <div class="alt-rank">${alt.rank}</div>
          <div class="alt-name">${esc(alt.employee_name)}</div>
          <div style="margin-left:auto">Skill: ${alt.skill_score} · Final: ${fmt(alt.final_candidate_score)}</div>
        </div>`;
      }

      html += `</div></div>`;
    }

    html += `</div></div>`;
  }

  // -- Team chemistry
  const chemNorm = team_chemistry.normalized ?? 0;
  const chemRaw  = team_chemistry.raw ?? 0;
  html += `<div class="chemistry-block">
    <div class="results-section-title">Overall Team Chemistry</div>
    <div class="chem-bar-wrap">
      <div class="chem-bar-fill" style="width:${chemNorm.toFixed(1)}%"></div>
      <div class="chem-bar-label">${chemNorm.toFixed(0)} / 100</div>
    </div>
    <div class="chem-numbers">
      <span>Raw: <strong>${chemRaw.toFixed(2)} / 10</strong></span>
      <span>Normalized: <strong>${chemNorm.toFixed(1)} / 100</strong></span>
    </div>
  </div>`;

  // -- Warnings
  const allWarnings = [
    ...(warnings || []),
    ...role_results.filter(rr => rr.error).map(rr => rr.error),
  ];
  if (allWarnings.length > 0) {
    html += `<div>
      <div class="results-section-title">Warnings</div>
      <div class="warnings">`;
    for (const w of allWarnings) {
      html += `<div class="warning-item">${esc(w)}</div>`;
    }
    html += `</div></div>`;
  }

  resultsContent.innerHTML = html;
}

// ---- Helpers --------------------------------------------------------------
function esc(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function fmt(val) {
  if (val == null) return "—";
  return Number(val).toFixed(1);
}

function pillClass(score) {
  if (score >= 70) return "good";
  if (score >= 40) return "ok";
  return "low";
}
