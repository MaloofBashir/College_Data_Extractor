import re
from collections import defaultdict

from PyPDF2 import PdfReader


STUDENT_START_PATTERN = re.compile(r"^\d{6,}\s+\S+")
SUBJECT_CODE_PATTERN = re.compile(r"\b([A-Z]{3,}\d+[A-Z0-9]*)\(([^)]*)\)")
PASS_PATTERN = re.compile(r"\bPASS\s*/\s*SGPA", re.IGNORECASE)
REAPPEAR_PATTERN = re.compile(r"\bREAPPEAR\b|\bR\s+[A-Z]{3,}\d+[A-Z0-9]*", re.IGNORECASE)
FAIL_PATTERN = re.compile(r"\bFAIL\b", re.IGNORECASE)
SGPA_PATTERN = re.compile(r"SGPA\s*(?:[-]+>\s*)?([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
FAIL_GRADES = {"F", "AB"}
SUBJECT_NAME_MAP = {
    "ANT": "Anthropology",
    "DMG": "Disaster Management",
    "DTS": "Digital Technology Solutions",
    "EDU": "Education",
    "ENL": "English Language",
    "ESE": "Environmental Science",
    "EVS": "Environmental Science Education",
    "GEN": "General English",
    "GLY": "Geology",
    "HST": "History",
    "HYS": "Health & Wellness",
    "PLS": "Political Science",
    "SOC": "Sociology",
    "UIN": "Understanding India",
    "URL": "Urdu Literature",
    "URM": "Urdu Language",
}


def normalize_spaces(value):
    return re.sub(r"\s+", " ", value or "").strip()


def is_student_start(line):
    return bool(STUDENT_START_PATTERN.match(line.strip()))


def split_student_blocks(page_text):
    blocks = []
    current_block = []

    for raw_line in (page_text or "").splitlines():
        line = normalize_spaces(raw_line)
        if not line or line.isdigit():
            continue
        if line.startswith("Roll No.Reg No. Name Subjects Result"):
            continue

        if is_student_start(line):
            if current_block:
                blocks.append(" ".join(current_block))
            current_block = [line]
        elif current_block:
            current_block.append(line)

    if current_block:
        blocks.append(" ".join(current_block))

    return blocks


def subject_name_from_code(subject_code):
    prefix = re.match(r"[A-Z]+", subject_code or "")
    if not prefix:
        return "Unknown Subject"
    return SUBJECT_NAME_MAP.get(prefix.group(0), "Unknown Subject")


def split_block_sections(student_block):
    parts = [normalize_spaces(part) for part in (student_block or "").split("<br>")]
    return [part for part in parts if part]


def extract_student_identity(student_block):
    sections = split_block_sections(student_block)
    header = sections[0] if sections else normalize_spaces(student_block)
    tokens = header.split()
    if len(tokens) < 2:
        return {"roll_no": "", "reg_no": "", "name": ""}

    roll_no = tokens[0]
    reg_no = tokens[1]
    name_parts = []

    for token in tokens[2:]:
        if SUBJECT_CODE_PATTERN.match(token):
            break
        name_parts.append(token)

    return {
        "roll_no": roll_no,
        "reg_no": reg_no,
        "name": " ".join(name_parts).strip(),
    }


def parse_subject_grade_details(student_block):
    parts = split_block_sections(student_block)
    if len(parts) < 2:
        return {}

    grade_section = normalize_spaces(parts[1])
    subject_results = {}

    for subject_code, grade in SUBJECT_CODE_PATTERN.findall(grade_section):
        clean_grade = normalize_spaces(grade).upper()
        subject_results[subject_code] = {
            "grade": clean_grade,
            "result": "FAIL" if clean_grade in FAIL_GRADES else "PASS",
        }

    return subject_results


def parse_subject_grades(student_block):
    detailed_results = parse_subject_grade_details(student_block)
    return {
        subject_code: result["result"]
        for subject_code, result in detailed_results.items()
    }


def parse_result_text(student_block):
    parts = split_block_sections(student_block)
    if len(parts) >= 3:
        return parts[2]
    if len(parts) >= 2:
        return parts[-1]
    return ""


def parse_issue_subjects(student_block):
    result_text = parse_result_text(student_block)
    cleaned_text = normalize_spaces(result_text)
    if not cleaned_text:
        return []

    if cleaned_text.upper().startswith("R "):
        cleaned_text = cleaned_text[2:].strip()
    elif cleaned_text.upper().startswith("REAPPEAR "):
        cleaned_text = cleaned_text[9:].strip()

    subjects = re.findall(r"\b[A-Z]{3,}\d+[A-Z0-9]*\b", cleaned_text)
    seen = []
    for subject in subjects:
        if subject not in seen:
            seen.append(subject)
    return seen


def parse_sgpa(student_block):
    match = SGPA_PATTERN.search(student_block or "")
    if not match:
        return None
    try:
        return round(float(match.group(1)), 2)
    except ValueError:
        return None


def parse_overall_result(student_block):
    block = student_block or ""
    if PASS_PATTERN.search(block):
        return "PASS"
    if REAPPEAR_PATTERN.search(block):
        return "REAPPEAR"
    if FAIL_PATTERN.search(block):
        return "FAIL"
    return "FAIL"


def parse_student_record(student_block):
    identity = extract_student_identity(student_block)
    overall_status = parse_overall_result(student_block)
    sgpa = parse_sgpa(student_block)
    issue_subjects = parse_issue_subjects(student_block)
    subject_grade_details = parse_subject_grade_details(student_block)

    return {
        **identity,
        "overall_status": overall_status,
        "sgpa": sgpa,
        "issue_subjects": issue_subjects,
        "result_text": parse_result_text(student_block),
        "subject_grades": [
            {
                "subject_code": subject_code,
                "subject_name": subject_name_from_code(subject_code),
                "grade": data["grade"],
                "result": data["result"],
            }
            for subject_code, data in subject_grade_details.items()
        ],
    }


def summarize_result_pdf(file_obj):
    reader = PdfReader(file_obj)
    subject_totals = defaultdict(
        lambda: {
            "appeared": 0,
            "passed": 0,
            "failed": 0,
            "absent": 0,
            "subject_name": "",
            "failed_students": [],
        }
    )
    total_students = 0
    overall_passed = 0
    overall_failed = 0
    overall_reappear = 0
    parsed_students = 0
    total_pass_sgpa = 0
    pass_sgpa_count = 0
    students = []

    for page in reader.pages:
        text = page.extract_text() or ""
        student_blocks = split_student_blocks(text)

        for block in student_blocks:
            total_students += 1
            student_record = parse_student_record(block)
            students.append(student_record)

            overall_result = student_record["overall_status"]
            if overall_result == "PASS":
                overall_passed += 1
                if student_record["sgpa"] is not None:
                    total_pass_sgpa += student_record["sgpa"]
                    pass_sgpa_count += 1
            elif overall_result == "REAPPEAR":
                overall_reappear += 1
            else:
                overall_failed += 1

            if not student_record["subject_grades"]:
                continue

            parsed_students += 1
            for subject_grade in student_record["subject_grades"]:
                subject_code = subject_grade["subject_code"]
                status = subject_grade["result"]
                subject_totals[subject_code]["appeared"] += 1
                subject_totals[subject_code]["subject_name"] = subject_grade["subject_name"]
                if status == "PASS":
                    subject_totals[subject_code]["passed"] += 1
                else:
                    subject_totals[subject_code]["failed"] += 1
                    if subject_grade["grade"] == "AB":
                        subject_totals[subject_code]["absent"] += 1
                    subject_totals[subject_code]["failed_students"].append(
                        {
                            "roll_no": student_record["roll_no"],
                            "name": student_record["name"],
                        }
                    )

    if not subject_totals:
        raise ValueError("No subject results could be extracted from this PDF.")

    subjects = []
    for subject_code in sorted(subject_totals):
        data = subject_totals[subject_code]
        appeared = data["appeared"]
        passed = data["passed"]
        percentage = round((passed / appeared) * 100, 2) if appeared else 0
        subjects.append(
            {
                "subject": subject_code,
                "subject_name": data["subject_name"] or subject_name_from_code(subject_code),
                "appeared": appeared,
                "passed": passed,
                "failed": data["failed"],
                "absent": data["absent"],
                "pass_percentage": percentage,
                "failed_students": data["failed_students"],
            }
        )

    overall_pass_percentage = round((overall_passed / total_students) * 100, 2) if total_students else 0
    average_sgpa = round((total_pass_sgpa / pass_sgpa_count), 2) if pass_sgpa_count else None
    status_summary = []

    for status, count in (
        ("PASS", overall_passed),
        ("REAPPEAR", overall_reappear),
        ("FAIL", overall_failed),
    ):
        status_summary.append(
            {
                "status": status,
                "count": count,
                "percentage": round((count / total_students) * 100, 2) if total_students else 0,
            }
        )

    ranked_subjects = sorted(
        subjects,
        key=lambda item: (-item["pass_percentage"], -item["passed"], item["subject"]),
    )
    pass_students = [
        student for student in students if student["overall_status"] == "PASS" and student["sgpa"] is not None
    ]
    pass_students.sort(key=lambda item: (-item["sgpa"], item["roll_no"]))

    return {
        "total_students": total_students,
        "overall_passed": overall_passed,
        "overall_failed": overall_failed,
        "overall_reappear": overall_reappear,
        "overall_not_passed": overall_failed + overall_reappear,
        "overall_pass_percentage": overall_pass_percentage,
        "average_sgpa_pass_only": average_sgpa,
        "parsed_pages": len(reader.pages),
        "parsed_students": parsed_students,
        "status_summary": status_summary,
        "top_subject": ranked_subjects[0] if ranked_subjects else None,
        "top_subjects": ranked_subjects[:8],
        "top_subject_max_passed": max((item["passed"] for item in ranked_subjects[:8]), default=1),
        "subjects": subjects,
        "students": students,
        "pass_students": pass_students,
    }
