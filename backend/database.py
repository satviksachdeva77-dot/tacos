"""
database.py — All database access functions for TACOS.
Uses parameterized queries only. No raw string interpolation of user input.
"""

import sqlite3
from typing import List, Tuple, Optional
from config import DATABASE_PATH


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------

def get_available_employees() -> List[dict]:
    """Return all employees where availability = 1."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT employee_id, employee_name FROM employees WHERE availability = 1"
        ).fetchall()
    return [dict(r) for r in rows]


def get_employee(employee_id: int) -> Optional[dict]:
    """Return a single employee record."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT employee_id, employee_name, availability FROM employees WHERE employee_id = ?",
            (employee_id,)
        ).fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

def get_all_skills() -> List[dict]:
    """Return all skills ordered by skill_id."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT skill_id, skill_name FROM skills ORDER BY skill_id"
        ).fetchall()
    return [dict(r) for r in rows]


def get_skill_id(skill_name: str) -> Optional[int]:
    """Return skill_id for a given skill_name (case-insensitive match)."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT skill_id FROM skills WHERE LOWER(skill_name) = LOWER(?)",
            (skill_name,)
        ).fetchone()
    return row["skill_id"] if row else None


# ---------------------------------------------------------------------------
# Employee Skills
# ---------------------------------------------------------------------------

def get_employee_skill_score(employee_id: int, skill_id: int) -> Optional[int]:
    """Return the skill_score for an employee/skill pair, or None if not found."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT skill_score FROM employee_skills WHERE employee_id = ? AND skill_id = ?",
            (employee_id, skill_id)
        ).fetchone()
    return row["skill_score"] if row else None


def get_candidates_for_skill(skill_id: int, available_ids: List[int]) -> List[dict]:
    """
    Return all available employees who have a record for this skill.
    Returns list of {employee_id, employee_name, skill_score}.
    """
    if not available_ids:
        return []
    placeholders = ",".join("?" * len(available_ids))
    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT e.employee_id, e.employee_name, es.skill_score
            FROM employee_skills es
            JOIN employees e ON e.employee_id = es.employee_id
            WHERE es.skill_id = ?
              AND e.availability = 1
              AND e.employee_id IN ({placeholders})
            ORDER BY es.skill_score DESC, e.employee_id ASC
            """,
            [skill_id] + list(available_ids)
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Chemistry helpers
# ---------------------------------------------------------------------------

def get_common_projects(employee_a_id: int, employee_b_id: int) -> int:
    """
    Return the number of completed projects both employees participated in.
    Uses project_participants joined to completed_projects only.
    """
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM project_participants pp1
            JOIN project_participants pp2
              ON pp1.completed_project_id = pp2.completed_project_id
            WHERE pp1.employee_id = ?
              AND pp2.employee_id = ?
            """,
            (employee_a_id, employee_b_id)
        ).fetchone()
    return row["cnt"] if row else 0


def get_confirmed_report(employee_a_id: int, employee_b_id: int) -> bool:
    """
    Return True if there is a confirmed collaboration report between the two employees.
    The schema guarantees employee_1_id < employee_2_id.
    """
    lo, hi = sorted([employee_a_id, employee_b_id])
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM collaboration_reports
            WHERE employee_1_id = ?
              AND employee_2_id = ?
              AND report_status = 'confirmed'
            """,
            (lo, hi)
        ).fetchone()
    return row is not None
