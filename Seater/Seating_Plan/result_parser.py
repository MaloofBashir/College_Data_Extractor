import re
from collections import defaultdict

from PyPDF2 import PdfReader


STUDENT_START_PATTERN = re.compile(r"^\d{6,}\s+\S+")
SUBJECT_CODE_PATTERN = re.compile(r"\b([A-Z]{3,}\d+[A-Z0-9]*)\(([^)]*)\)")
PASS_PATTERN = re.compile(r"\bPASS\s*/\s*SGPA", re.IGNORECASE)
FAIL_GRADES = {"F", "AB"}


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


def parse_subject_grades(student_block):
    parts = student_block.split("<br>")
    if len(parts) < 2:
        return {}

    grade_section = normalize_spaces(parts[1])
    subject_results = {}

    for subject_code, grade in SUBJECT_CODE_PATTERN.findall(grade_section):
        clean_grade = normalize_spaces(grade).upper()
        subject_results[subject_code] = "FAIL" if clean_grade in FAIL_GRADES else "PASS"

    return subject_results


def parse_overall_result(student_block):
    return "PASS" if PASS_PATTERN.search(student_block or "") else "FAIL"


def summarize_result_pdf(file_obj):
    reader = PdfReader(file_obj)
    subject_totals = defaultdict(lambda: {"appeared": 0, "passed": 0, "failed": 0})
    total_students = 0
    overall_passed = 0
    parsed_students = 0

    for page in reader.pages:
        text = page.extract_text() or ""
        student_blocks = split_student_blocks(text)

        for block in student_blocks:
            total_students += 1
            overall_result = parse_overall_result(block)
            if overall_result == "PASS":
                overall_passed += 1

            subject_results = parse_subject_grades(block)
            if not subject_results:
                continue

            parsed_students += 1
            for subject_code, status in subject_results.items():
                subject_totals[subject_code]["appeared"] += 1
                if status == "PASS":
                    subject_totals[subject_code]["passed"] += 1
                else:
                    subject_totals[subject_code]["failed"] += 1

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
                "appeared": appeared,
                "passed": passed,
                "failed": data["failed"],
                "pass_percentage": percentage,
            }
        )

    overall_pass_percentage = round((overall_passed / total_students) * 100, 2) if total_students else 0

    return {
        "total_students": total_students,
        "overall_passed": overall_passed,
        "overall_failed": total_students - overall_passed,
        "overall_pass_percentage": overall_pass_percentage,
        "parsed_pages": len(reader.pages),
        "parsed_students": parsed_students,
        "subjects": subjects,
    }
