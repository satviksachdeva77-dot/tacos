# 🌮 TACOS — Team Allocation & Candidate Optimization System

> A deterministic employee-to-project team allocation system. TACOS selects an **MVP** based on the project's key technical skill, then builds the rest of the team around the MVP using **skill eligibility**, **anti-overqualification preference**, and **historical collaboration chemistry**.

---

## 📌 Executive Summary

TACOS solves the corporate team allocation problem deterministically without relying on black-box AI, LLMs, embeddings, or heuristic randomness.

- **Anchor-Based Team Building:** Identifies a technical **MVP** first, who serves as the core anchor.
- **Growing-Team Chemistry:** Progressively evaluates candidates against all members already added to the team.
- **Anti-Overqualification Philosophy:** Rewards employees who comfortably meet requirements without wasting overqualified talent on low-threshold roles.
- **Direct Chemistry Modeling:** Uses historical co-project participation (+2 bonus) and confirmed negative reports (-2 penalty).

---

## ⚙️ Core Algorithm & Mathematical Formulas

### 1. Availability Filter
Before any scoring occurs:
$$\text{availability} = 1$$
Unavailable employees are strictly excluded from MVP selection, team selection, and alternatives.

---

### 2. Star-Based Importance Thresholds

| Importance Rating | MVP Skill Minimum Score | Candidate Minimum Score | Preferred Range ($+10$) |
| :--- | :---: | :---: | :---: |
| ⭐⭐⭐⭐⭐ (5 Stars) | **90** | **50** | $50 \text{ to } 60$ |
| ⭐⭐⭐⭐ (4 Stars) | **80** | **40** | $40 \text{ to } 50$ |
| ⭐⭐⭐ (3 Stars) | **60** | **30** | $30 \text{ to } 40$ |
| ⭐⭐ (2 Stars) | **50** | **25** | $25 \text{ to } 35$ |
| ⭐ (1 Star) | **40** | **10** | $10 \text{ to } 20$ |

---

### 3. MVP Selection Algorithm
1. Filter available employees with $\text{skill\_score} \ge \text{MVP\_minimum}$.
2. Sort candidates by $\text{skill\_score}$ descending.
3. Tie-break using lowest `employee_id` (deterministic).

$$\text{MVP} = \arg\max_{e \in \text{Available}} (\text{skill\_score}_{\text{MVP\_skill}}(e))$$

*Note: Chemistry and secondary skills are not considered during MVP selection.*

---

### 4. Skill Preference Score ($0 \text{ to } 100$)
Rewards candidates in the preferred range $[\text{threshold}, \text{threshold} + 10]$ and penalizes unnecessary overqualification.

$$\text{SkillPreferenceScore}(s, T) = 
\begin{cases} 
0 & \text{if } s < T \\
100 - 50 \times \left(\frac{s - T}{10}\right) & \text{if } T \le s \le T + 10 \\
\max\left(0, 50 - (s - (T + 10))\right) & \text{if } s > T + 10 
\end{cases}$$

---

### 5. Collaboration & Team Chemistry

#### Pair Chemistry $[-2, +10]$
$$\text{PairChemistry}(A, B) = \text{clamp}\Big( (2 \times \text{common\_projects}(A, B)) + \text{confirmed\_report\_penalty}(A, B), \; -2, \; +10 \Big)$$

- **Completed Shared Projects:** $+2$ per project.
- **Confirmed Negative Report:** $-2$ penalty.
- **Pending / Dismissed Reports:** $0$ effect.

#### Candidate Team Chemistry
Evaluates candidate $C$ against all current team members $M \in \text{Team}$:
$$\text{CandidateTeamChemistry}(C, \text{Team}) = \frac{1}{|\text{Team}|} \sum_{M \in \text{Team}} \text{PairChemistry}(C, M)$$

#### Chemistry Normalization ($0 \text{ to } 100$)
$$\text{NormalizedChemistry}(\text{raw}) = \text{clamp}\left( \frac{\text{raw} - (-2)}{10 - (-2)} \times 100, \; 0, \; 100 \right) = \left(\frac{\text{raw} + 2}{12}\right) \times 100$$

---

### 6. Final Candidate Score
For non-MVP candidates:
$$\text{FinalCandidateScore} = 0.80 \times \text{SkillPreferenceScore} + 0.20 \times \text{NormalizedTeamChemistry}$$

---

## 📁 Architecture & File Structure

```text
mexican/
├── backend/
│   ├── config.py                 # Star thresholds, weights, and scoring caps
│   ├── database.py               # Parameterized SQLite query layer
│   ├── skill_rater.py            # SkillPreferenceScore & eligibility logic
│   ├── mvp_calculator.py         # Deterministic MVP selection engine
│   ├── chemistry_calculator.py   # Pair & Team chemistry calculations + normalization
│   ├── alternative_candidates.py # Post-cleanup alternative candidate ranking
│   ├── team_builder.py           # Core TACOS team builder orchestration
│   ├── main.py                   # Flask API server & static asset host (Port 9000)
│   └── tests/                    # Pytest test suite (53 passing tests)
│       ├── test_chemistry.py
│       ├── test_mvp.py
│       ├── test_skill_rater.py
│       └── test_team_builder.py
├── frontend/
│   ├── index.html                # Manager dashboard UI
│   ├── style.css                 # Dark theme styling
│   └── app.js                    # Dynamic frontend application
├── schema.sql                    # Database schema definition
└── tacos.db                      # SQLite database (100 employees, 20 skills, 40 projects)
```

---

## 🔌 API Documentation

### 1. `GET /api/skills`
Returns all available skills in the database.

**Response:**
```json
{
  "skills": ["Python", "Java", "SQL", "Machine Learning", "React", "Cybersecurity"]
}
```

### 2. `POST /api/build-team`
Generates the optimal team based on project criteria.

**Request Body:**
```json
{
  "project_name": "AI Platform",
  "team_size": 5,
  "importance": 5,
  "required_skills": ["Python", "React", "SQL", "Machine Learning"],
  "mvp_skill": "Python"
}
```

**Response Output:**
```json
{
  "project_summary": {
    "project_name": "AI Platform",
    "team_size": 5,
    "importance": 5,
    "required_skills": ["Python", "React", "SQL", "Machine Learning"],
    "mvp_skill": "Python",
    "thresholds": { "mvp_minimum": 90, "candidate_minimum": 50 }
  },
  "mvp": {
    "employee_id": 83,
    "employee_name": "Mohit Desai",
    "mvp_skill": "Python",
    "skill_score": 100
  },
  "selected_team": [
    {
      "employee_id": 83,
      "employee_name": "Mohit Desai",
      "role": "Python",
      "is_mvp": true,
      "skill_score": 100
    },
    {
      "employee_id": 45,
      "employee_name": "Harsh Trivedi",
      "role": "React",
      "is_mvp": false,
      "skill_score": 54,
      "skill_preference_score": 80.0,
      "raw_team_chemistry": 0.0,
      "normalized_team_chemistry": 16.6667,
      "final_candidate_score": 67.3333
    }
  ],
  "team_chemistry": {
    "raw": 0.4,
    "normalized": 20.0
  },
  "warnings": []
}
```

---

## 🧪 Testing & Verification

Run the full automated test suite using `pytest`:

```bash
python -m pytest backend/tests/ -v
```

**Test Coverage:**
- ✅ **MVP Tests:** Minimum threshold enforcement, availability filtering, tie-breaking.
- ✅ **Skill Rater Tests:** Preference score linear decay, overqualification penalties, eligibility boundaries.
- ✅ **Chemistry Tests:** $+2$ project bonus, $-2$ report penalty, min/max caps $[-2, +10]$, team averaging, normalization.
- ✅ **Team Builder Tests:** Duplicate prevention, growing-team evaluation, determinism, team size handling, alternatives exclusion.

---

## 🚀 Running the Local Demo

1. Start the backend server:
   ```bash
   python backend/main.py
   ```
2. Open your browser at:
   👉 **`http://localhost:9000`**

3. Fill out project details, select skills and an MVP skill, and click **🚀 BUILD TEAM**.
