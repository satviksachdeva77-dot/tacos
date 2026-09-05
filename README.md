# tacos
summary 
# EMP Insertion — Decision Log & Parameter Reference

Purpose: a single reference of every design decision made so far, with the specific parameters/formulas isolated so any of them can be swapped out or re-modeled independently without redesigning the whole system.

---

## 1. Employee Data Model (fields tracked per person)

- Name
- Role
- Skills / Skill type
- Languages
- Projects worked on
- Availability
- Type of experience
- Time (in role / on similar work — exact definition still to be operationalized)
- Degree of professionalism (derived, not raw input — see Section 4)

---

## 2. Candidate Scoring Formula

```
CandidateScore = 0.30 × TypeOfExpMatch
               + 0.30 × TimeMatch
               + 0.40 × ProfessionalismScore
```

| Parameter | Value | Swappable? |
|---|---|---|
| TypeOfExpMatch weight | 30% | Yes — isolated coefficient |
| TimeMatch weight | 30% | Yes — isolated coefficient |
| ProfessionalismScore weight | 40% | Yes — isolated coefficient |

---

## 3. Matching Pipeline (Retrieval Architecture)

**Decision:** Hybrid approach — not pure AI, not pure rules.

1. **SQL filter** — hard constraints only (availability, role, required language/cert). Filters, does not score.
2. **Vector/similarity search** — ranks the SQL-filtered candidate pool by skill/experience fit.
3. **Scoring engine** — applies the weighted formula (Section 2) to the ranked pool.
4. **Skill-fit vs. chemistry conflict rule:** resolved via **weighted combination** of individual CandidateScore and TeamChemistryScore (exact blend weight not yet finalized — see Section 8).

---

## 4. Professionalism / Integrity System

```
ProfessionalismScore = PerformanceScore
                       − IntegrityPenalty(severity, decayed over time)
                       [Background = tiebreaker ONLY, applied when scores are near-equal]
```

**Performance:** primary signal. Source = in-company project outcomes (tenured employees) or provisional profile (new hires — see Section 5).

**Integrity data source (decided):**
- Only in-company, on-record project issues
- OR a specific flag raised by a manager
- No external review platforms, no freelance-site data used

**Integrity flag rules (decided):**
- Penalty is **scaled by severity** (not flat, not disqualifying by default)
- Flags **decay over time** — older flags carry less weight
- Decay curve type: **not yet finalized** (step decay vs. linear/exponential — step was suggested as easier to audit/explain, but not locked in)

**Background (decided):**
- Used strictly as a **true tiebreaker** — only compared when two candidates' scores are within a near-equal threshold
- "Near-equal" threshold value: **not yet defined**
- Never applied as a standing weighted component

---

## 5. New Hire Onboarding (AI-Assisted Data Entry Only)

**Decision:** AI is used for exactly one purpose in the entire system — converting unstructured documents into structured data. It does not make matching, scoring, or chemistry decisions.

**Pipeline:**
```
Resume + Certificates/Degrees → OCR → Gemini feature extraction → structured PROVISIONAL profile
```

**Documents in scope (decided):** Resume/CV + Certificates/Degrees. (Reference letters explicitly excluded from this input set.)

**Provisional status (decided):**
- New-hire profile is kept **separate and clearly marked provisional**
- It is **not** blended into the same ProfessionalismScore field as tenured employees
- **Replacement trigger** (time window vs. project-count threshold vs. whichever comes first): **not yet finalized**

---

## 6. Chemistry System

**Core model:**
```
DirectEdgeWeight(A, B) = BaseScore(TimeCollaborated)
                        + Σ(PositiveEvents)     [visible to all]
                        − Σ(NegativeEvents)     [backend / manager-only visibility]

TransitiveAdjustment(A, B) = small_weight × avg(chemistry of A & B's shared collaborators)
                              — capped to a slight margin, 1-hop shared collaborators

FinalEdgeWeight(A, B) = DirectEdgeWeight(A, B) + TransitiveAdjustment(A, B)

TeamChemistryScore = average of all FinalEdgeWeight values among proposed team members
```

**Decided parameters:**
| Element | Decision |
|---|---|
| Team aggregation method | Average of all pairwise edge weights |
| Who can raise a chemistry review | Both peers and managers, **weighted differently** (exact split not yet finalized) |
| Positive event visibility | Visible to all |
| Negative event visibility | Backend / managers only — never shown to the flagged party or team |
| Time-decay of chemistry | **No direct time decay** — chemistry values are otherwise static; the *only* mechanism for chemistry to shift over time is the transitivity adjustment, and only by a slight margin |
| Transitivity scope | Shared (1-hop) collaborators — not multi-hop propagation |

**Open question (unresolved):** should negative events feed into the transitivity calculation, or should negative events stay fully contained to the direct pair (only positive events propagate)? Flagged as a privacy/inference-leak risk if negative events propagate, since it could indirectly reveal a private flag's existence through pattern inference. **Not yet decided.**

---

## 7. AI Scope (System-Wide Policy)

**Decided:** AI (Gemini) is used **only** for resume/certificate → structured data conversion during onboarding. All matching, scoring, filtering, and chemistry logic is deterministic — formulas and graph math over real data, not model inference.

---

## 8. Open / Unresolved Parameters (flagged throughout, not yet locked in)

These are the specific knobs still undecided — useful list if swapping models or finalizing the spec:

1. **Integrity flag decay curve** — step decay vs. linear/exponential decay
2. **New-hire provisional → real score transition trigger** — fixed time window, project-count threshold, or whichever comes first
3. **Peer vs. manager chemistry-review weighting split** — exact ratio not defined
4. **Negative-event transitivity propagation** — include or fully exclude from transitive adjustment
5. **"Near-equal" threshold** for background tiebreaker — no numeric value set yet
6. **Blend weight** between individual CandidateScore and TeamChemistryScore in FinalTeamScore
7. **Team assembly algorithm** for larger candidate pools — brute-force (small pools) vs. greedy/constraint-based selection (larger pools) suggested, not confirmed as a hard requirement
8. **Empty/insufficient-candidate-pool policy** — auto-relax SQL filters vs. flag to a human reviewer
9. **"Time" field definition** — time-in-role, time available, or time since last similar project (ambiguous, not resolved)
