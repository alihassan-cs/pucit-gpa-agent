"""
tools.py — Tool functions for the PUCIT GPA/CGPA agent.

These are the ONLY things allowed to do arithmetic. agent.py never
computes a number itself; it only decides which tool to call and with
what arguments, then phrases the result. Every tool below:
  - has type hints on every parameter and the return (this is the schema
    the model reads to build its function-call arguments)
  - has a docstring that says WHEN to use it, not just what it does
  - returns a plain error string on invalid input instead of raising
"""

from pathlib import Path

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# 5.1  PUCIT grade bands  (marks -> grade point)
# ---------------------------------------------------------------------------
_GRADE_BANDS = [
    (85, 100, 4.0),  # A
    (80, 84, 3.7),   # A-
    (75, 79, 3.3),   # B+
    (70, 74, 3.0),   # B
    (65, 69, 2.7),   # B-
    (61, 64, 2.3),   # C+
    (58, 60, 2.0),   # C
    (55, 57, 1.7),   # C-
    (50, 54, 1.0),   # D
    (0, 49, 0.0),    # F
]

# ---------------------------------------------------------------------------
# 5.2  Scheme of studies — BS Computer Science
# Each row: (course_code, course_name, credit_hours)
# MD-001 / MD-002 (Math Deficiency) are deliberately absent: non-credit,
# pass/fail, never part of a GPA calculation.
# ---------------------------------------------------------------------------
COURSES: dict[int, list[tuple[str, str, float]]] = {
    1: [
        ("MS-251", "Probability & Statistics", 3.0),
        ("GE-160", "Applications of ICT", 3.0),
        ("GE-169", "Applied Physics", 3.0),
        ("GE-167", "Discrete Structures", 3.0),
        ("HQ-001", "Quran Translation - I", 0.5),
        ("GE-190", "Functional English", 3.0),
    ],
    2: [
        ("CC-112", "Programming Fundamentals", 3.0),
        ("CC-112-L", "Programming Fundamentals Lab", 1.0),
        ("CC-110", "Digital Logic Design", 2.0),
        ("CC-110-L", "Digital Logic Design Lab", 1.0),
        ("MS-252", "Linear Algebra", 3.0),
        ("GE-191", "Expository Writing", 3.0),
        ("GE-163", "Islamic Studies", 2.0),
        ("HQ-002", "Quran Translation - II", 0.5),
    ],
    3: [
        ("CC-211", "Object Oriented Programming", 3.0),
        ("CC-211-L", "Object Oriented Programming Lab", 1.0),
        ("CC-215", "Database Systems", 3.0),
        ("CC-215-L", "Database Systems Lab", 1.0),
        ("CC-210", "Computer Organization & Assembly Language", 3.0),
        ("GE-162", "Calculus & Analytical Geometry", 3.0),
        ("GE-192", "Introduction to Management", 2.0),
        ("HQ-003", "Quran Translation - III", 0.5),
    ],
    4: [
        ("CC-213", "Data Structures", 3.0),
        ("CC-213-L", "Data Structures Lab", 1.0),
        ("CC-312", "Information Security", 3.0),
        ("CC-214", "Computer Networks", 3.0),
        ("CC-212", "Software Engineering", 3.0),
        ("DC-220", "Advanced Database Management Systems", 3.0),
        ("HQ-004", "Quran Translation - IV", 0.5),
    ],
    5: [
        ("CC-313", "Analysis of Algorithms", 3.0),
        ("CC-310", "Artificial Intelligence", 3.0),
        ("DC-320", "Theory of Automata and Formal Languages", 3.0),
        ("DC-321", "Human Computer Interaction", 3.0),
        ("DC-322", "Computer Architecture", 3.0),
        ("EC-330", "Web Technologies / Elective", 3.0),
        ("HQ-005", "Quran Translation - V", 0.5),
    ],
    6: [
        ("CC-311", "Operating Systems", 3.0),
        ("EC-333", "Mobile Application Development / Elective", 3.0),
        ("EC-324", "Software Construction & Development / Elective", 3.0),
        ("EC-335", "Machine Learning / Elective", 3.0),
        ("EC-334", "Game Design and Development / Elective", 3.0),
        ("MS-253", "Multivariable Calculus", 3.0),
        ("HQ-006", "Quran Translation - VI", 0.5),
    ],
    7: [
        ("CC-411", "Final Year Project - I", 2.0),
        ("DC-328", "Parallel & Distributed Computing", 3.0),
        ("EC-345", "Computer Vision / Elective", 3.0),
        ("EC-425", "Software Quality Engineering / Elective", 3.0),
        ("MS-254", "Technical and Business Writing", 3.0),
        ("GE-263", "Entrepreneurship", 2.0),
        ("GE-262", "Professional Practices", 2.0),
        ("HQ-007", "Quran Translation - VII", 0.5),
    ],
    8: [
        ("CC-412", "Final Year Project - II", 4.0),
        ("DC-421", "Compiler Construction", 3.0),
        ("UE-272", "Introduction to Marketing", 3.0),
        ("GE-168", "Ideology and Constitution of Pakistan", 2.0),
        ("GE-363", "Civics and Community Engagement", 2.0),
        ("HQ-008", "Quran Translation - VIII", 0.5),
    ],
}

SEMESTER_TOTALS: dict[int, float] = {
    1: 15.5, 2: 15.5, 3: 16.5, 4: 16.5,
    5: 18.5, 6: 18.5, 7: 18.5, 8: 14.5,
}
TOTAL_DEGREE_CREDIT_HOURS = 134.0
MIN_SEMESTER, MAX_SEMESTER = 1, 8


@tool
def marks_to_grade_points(marks: int) -> float:
    """Convert one course's marks (0-100) into its PUCIT grade point.

    Use this whenever a student gives you marks for a course and you
    need the grade point before running a semester GPA calculation.
    Never work out the grade band yourself — always call this tool,
    once per course.

    Returns the grade point (e.g. 4.0, 3.7, 3.3, ...). If marks is
    outside 0-100, returns an error string instead of a number.
    """
    if not isinstance(marks, (int, float)) or marks < 0 or marks > 100:
        return "Error: marks must be between 0 and 100"
    for low, high, gp in _GRADE_BANDS:
        if low <= marks <= high:
            return float(gp)
    return "Error: marks must be between 0 and 100"  # unreachable, safety net


@tool
def calculate_semester_gpa(
    grade_points: list[float], credit_hours: list[float]
) -> float:
    """Calculate one semester's credit-weighted GPA.

    Use this once you have a grade point (from marks_to_grade_points)
    and the credit hours for every course in the semester. The two
    lists must be the same length and in the same course order.
    Exclude MD-001/MD-002 from both lists — they are non-credit
    pass/fail and never enter a GPA.

    Returns the semester GPA as a float. Returns an error string if
    the lists are empty, of different lengths, or credit hours sum to
    zero.
    """
    if not grade_points or not credit_hours:
        return "Error: grade_points and credit_hours must not be empty"
    if len(grade_points) != len(credit_hours):
        return "Error: grade_points and credit_hours must be the same length"
    total_ch = sum(credit_hours)
    if total_ch <= 0:
        return "Error: total credit hours must be greater than zero"
    weighted = sum(gp * ch for gp, ch in zip(grade_points, credit_hours))
    return round(weighted / total_ch, 3)


@tool
def calculate_new_cgpa(
    current_cgpa: float,
    completed_credit_hours: float,
    semester_gpa: float,
    semester_credit_hours: float,
) -> float:
    """Project the CGPA that results from adding one semester.

    Use this when the student asks what their CGPA will become after a
    semester — either a semester already completed, or a hypothetical
    "what if I get X this semester" question. Requires the CGPA and
    completed credit hours BEFORE this semester, plus this semester's
    GPA and credit hours.

    Returns the new CGPA as a float. Returns an error string if
    completed_credit_hours or semester_credit_hours is negative, or if
    both are zero.
    """
    if completed_credit_hours < 0 or semester_credit_hours < 0:
        return "Error: credit hours cannot be negative"
    total_ch = completed_credit_hours + semester_credit_hours
    if total_ch <= 0:
        return "Error: total credit hours must be greater than zero"
    new_cgpa = (
        current_cgpa * completed_credit_hours
        + semester_gpa * semester_credit_hours
    ) / total_ch
    return round(new_cgpa, 3)


@tool
def required_gpa_for_target(
    target_cgpa: float,
    current_cgpa: float,
    completed_credit_hours: float,
    remaining_credit_hours: float,
) -> float:
    """Calculate the GPA needed over the remaining credit hours to reach a target CGPA.

    Use this when the student names a target CGPA and asks what GPA
    they need going forward. The result CAN come back above 4.0 — that
    means the target is impossible over that many remaining credit
    hours, not that the tool failed. When that happens, do not present
    the number as an answer: call get_remaining_credit_hours for a
    wider horizon and call this tool again. See the unreachable-target
    procedure in the system prompt.

    Returns the required GPA as a float. Returns an error string if
    remaining_credit_hours is zero or negative.
    """
    if remaining_credit_hours <= 0:
        return "Error: remaining_credit_hours must be greater than zero"
    required = (
        target_cgpa * (completed_credit_hours + remaining_credit_hours)
        - current_cgpa * completed_credit_hours
    ) / remaining_credit_hours
    return round(required, 3)


@tool
def get_semester_courses(semester: int) -> str:
    """Return the course codes, names, and credit hours for a PUCIT semester.

    Use this when the student asks what courses are in a semester, or
    when you need a semester's course list/credit hours to help fill
    in a calculation and the student hasn't already given you the
    numbers. semester must be between 1 and 8.

    Returns a formatted multi-line string. Returns an error string if
    semester is out of range.
    """
    if semester not in COURSES:
        return f"Error: semester must be between {MIN_SEMESTER} and {MAX_SEMESTER}"
    lines = [f"Semester {semester} (total {SEMESTER_TOTALS[semester]} credit hours):"]
    for code, name, ch in COURSES[semester]:
        lines.append(f"  {code} — {name} ({ch} ch)")
    return "\n".join(lines)


@tool
def get_remaining_credit_hours(current_semester: int, through_semester: int = 8) -> float:
    """Total the graded credit hours from current_semester through a chosen semester.

    Use this for target-CGPA planning, and it is REQUIRED inside the
    unreachable-target procedure: it gives the remaining credit hours
    for each horizon. current_semester is the semester the student is
    in (or about to start). through_semester is the last semester the
    horizon includes (default 8 = the whole rest of the degree).
    Examples for a semester-5 student: (5, 5) = semester 5 only,
    (5, 6) = semesters 5-6, (5, 7) = semesters 5-7, (5, 8) = everything left.
    Never add semester totals yourself; call this tool for each horizon.

    Returns the total credit hours as a float. Returns an error string
    if either semester is outside 1-8 or through_semester is less than
    current_semester.
    """
    if current_semester not in SEMESTER_TOTALS:
        return f"Error: current_semester must be between {MIN_SEMESTER} and {MAX_SEMESTER}"
    if through_semester not in SEMESTER_TOTALS:
        return f"Error: through_semester must be between {MIN_SEMESTER} and {MAX_SEMESTER}"
    if through_semester < current_semester:
        return "Error: through_semester must not be before current_semester"
    return sum(
        ch for sem, ch in SEMESTER_TOTALS.items()
        if current_semester <= sem <= through_semester
    )


@tool
def save_report(filename: str, content: str) -> str:
    """Save a finished academic summary (GPA, projected CGPA, or target plan) to a file.

    Use this ONLY when the student explicitly asks to save or keep a
    result. Never call it after a clarifying question or a plain
    lookup, and never call it unprompted. filename should be a short
    descriptive name without a path (e.g. "semester5_gpa_report").

    Returns a confirmation string with the saved file's path. Returns
    an error string if filename is empty or contains path separators.
    """
    if not filename.strip():
        return "Error: filename must not be empty"
    if "/" in filename or "\\" in filename or ".." in filename:
        return "Error: filename must not contain path separators"

    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    safe_name = filename.strip()
    if not safe_name.endswith(".txt"):
        safe_name += ".txt"

    path = reports_dir / safe_name
    path.write_text(content, encoding="utf-8")
    return f"Saved report to {path}"
