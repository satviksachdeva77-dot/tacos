# TACOS

## 1. Project Purpose

TACOS builds an optimized project team by combining skill eligibility, project importance, employee availability, and previous collaboration chemistry.

---

## 2. Manager Inputs

* Team size
* Required skills
* MVP skill
* Project importance (1–5 stars)

---

## 3. Employee Database

### `employees`

* `employee_id`
* `employee_name`
* `availability`

### `skills`

* `skill_id`
* `skill_name`

### `employee_skills`

* `employee_id`
* `skill_id`
* `skill_score` (0–100)

---

## 4. Project History

### `completed_projects`

* `completed_project_id`
* `project_name`

### `project_participants`

* `completed_project_id`
* `employee_id`

Only completed projects contribute to future chemistry calculations.

---

## 5. Collaboration Reports

### `collaboration_reports`

* `report_id`
* `employee_1_id`
* `employee_2_id`
* `report_status`

Only `confirmed` reports affect chemistry.

```text
pending   → 0
dismissed → 0
confirmed → -2
```

---

## 6. Star-Based Thresholds

| Importance | MVP Minimum | Normal Minimum |
| ---------- | ----------: | -------------: |
| ⭐⭐⭐⭐⭐      |          90 |             50 |
| ⭐⭐⭐⭐       |          80 |             40 |
| ⭐⭐⭐        |          60 |             30 |
| ⭐⭐         |          50 |             25 |
| ⭐          |          40 |             10 |

---

## 7. MVP Selection

The manager selects the MVP skill.

TACOS:

1. Filters unavailable employees.
2. Applies the MVP threshold.
3. Ranks eligible employees by `skill_score`.
4. Selects the highest-scoring employee.

```text
MVP = Highest available eligible employee
      in the selected MVP skill
```

The MVP is the anchor around which TACOS builds the team.

---

## 8. Role-Based Candidate Selection

Employees are selected for individual skills or roles.

They do not need to meet the requirements for every project skill.

```text
Candidate eligibility = score in assigned role/skill
```

---

## 9. Skill Preference

For non-MVP roles:

```text
Preferred Range =
Minimum Threshold
to
Minimum Threshold + 10
```

TACOS prefers the lowest sufficiently qualified employee within this range to avoid unnecessary overqualification.

Candidates above the preferred range are used only when suitable candidates are unavailable.

---

## 10. Pair Chemistry

```text
PairChemistry =
(common_projects × 2)
+
negative_report_penalty
```

```text
PairChemistry ∈ [-2, +10]
```

Where:

```text
common_projects = completed projects shared by two employees
confirmed report = -2
```

---

## 11. Team Chemistry

Candidates are evaluated against the growing team.

```text
CandidateTeamChemistry =
Sum of pair chemistry with current team members
──────────────────────────────────────────────
Number of current team members
```

The first candidate is compared with the MVP.

Every following candidate is compared with the entire team formed so far.

---

## 12. Final Candidate Score

```text
FinalCandidateScore =
0.80 × SkillPreferenceScore
+
0.20 × NormalizedTeamChemistry
```

Skill is prioritized over chemistry.

---

## 13. Team Formation

```text
Manager Inputs
      ↓
Availability Filter
      ↓
MVP Selection
      ↓
Role-Based Eligibility
      ↓
Preferred Skill Range
      ↓
Chemistry Evaluation
      ↓
Growing Team Selection
      ↓
Final Team
```

---

## 14. Alternative Candidates

All eligible candidates are ranked using the same selection logic.

```text
Rank #1 → Selected Candidate
Rank #2 → Best Alternative
Rank #3 → Second Alternative
```

---

## 15. Tech Stack Structure

```text
database.py
config.py
skill_rater.py
mvp_calculator.py
chemistry_calculator.py
team_builder.py
alternative_candidates.py
main.py
```

```text
Frontend
   ↓
TACOS Backend
   ↓
SQLite / SQL Database
   ↓
Recommended Team + Alternatives
```
