CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    employee_name TEXT NOT NULL,
    availability BOOLEAN NOT NULL
);

CREATE TABLE skills (
    skill_id INTEGER PRIMARY KEY,
    skill_name TEXT NOT NULL UNIQUE
);

CREATE TABLE employee_skills (
    employee_id INTEGER NOT NULL REFERENCES employees(employee_id),
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id),
    skill_score INTEGER NOT NULL CHECK (skill_score BETWEEN 0 AND 100),
    PRIMARY KEY (employee_id, skill_id)
);

CREATE TABLE completed_projects (
    completed_project_id INTEGER PRIMARY KEY,
    project_name TEXT NOT NULL
);

CREATE TABLE project_participants (
    completed_project_id INTEGER NOT NULL REFERENCES completed_projects(completed_project_id),
    employee_id INTEGER NOT NULL REFERENCES employees(employee_id),
    PRIMARY KEY (completed_project_id, employee_id)
);

CREATE TABLE collaboration_reports (
    report_id INTEGER PRIMARY KEY,
    employee_1_id INTEGER NOT NULL REFERENCES employees(employee_id),
    employee_2_id INTEGER NOT NULL REFERENCES employees(employee_id),
    report_status TEXT NOT NULL CHECK (report_status IN ('pending','confirmed','dismissed')),
    CHECK (employee_1_id < employee_2_id),
    UNIQUE (employee_1_id, employee_2_id)
);

