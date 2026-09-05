"""
main.py — Flask API server for TACOS, serving on port 8080.

Endpoints:
  GET  /api/skills          → list all skills
  POST /api/build-team      → run TACOS team builder
  GET  /                    → serve the frontend
"""

import os
import sys

# Make sure imports from the backend directory work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, send_from_directory
from database import get_all_skills
from team_builder import build_team

# ---------------------------------------------------------------------------
# Flask app setup
# ---------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route("/api/skills", methods=["GET"])
def api_skills():
    """Return all skill names from the database."""
    skills = get_all_skills()
    return jsonify({"skills": [s["skill_name"] for s in skills]})


@app.route("/api/build-team", methods=["POST"])
def api_build_team():
    """
    Accept JSON body:
    {
      "project_name": "...",
      "team_size": 5,
      "importance": 5,
      "required_skills": ["Python", "React", "SQL"],
      "mvp_skill": "Python"
    }
    Returns the TACOS structured result.
    """
    data = request.get_json(force=True)

    project_name   = data.get("project_name", "Unnamed Project")
    team_size      = data.get("team_size")
    importance     = data.get("importance")
    required_skills = data.get("required_skills", [])
    mvp_skill      = data.get("mvp_skill")

    # Basic input validation
    if not isinstance(team_size, int) or team_size < 1:
        return jsonify({"error": "team_size must be a positive integer."}), 400
    if not isinstance(importance, int) or importance not in range(1, 6):
        return jsonify({"error": "importance must be an integer from 1 to 5."}), 400
    if not required_skills:
        return jsonify({"error": "required_skills must be a non-empty list."}), 400
    if not mvp_skill:
        return jsonify({"error": "mvp_skill is required."}), 400

    result = build_team(
        project_name=project_name,
        team_size=int(team_size),
        importance=int(importance),
        required_skills=[s.strip() for s in required_skills],
        mvp_skill=mvp_skill.strip(),
    )

    if "error" in result and len(result) == 1:
        return jsonify(result), 400

    return jsonify(result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  TACOS — Team Allocation & Candidate Optimization System")
    print("  Running at http://localhost:9000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=9000, debug=False)
