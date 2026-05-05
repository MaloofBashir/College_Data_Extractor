import openpyxl
import pandas as pd
import PyPDF2
from docx import Document
import re
from collections import defaultdict

json_data={ }
centre_nos=[]

def populating_centre_nos():
     for key,value in json_data.items():
          if key not in centre_nos:
            centre_nos.append(key)

dictionary_of_subjects={}

def add_rollnos_to_dict(current_subjects,rollno,centre_number):
    for subject in current_subjects:
        if subject not in json_data[centre_number]:
            json_data[centre_number][subject]=[]
        json_data[centre_number][subject].append(rollno)
    populating_centre_nos


def add_to_global_dict(pdf_obj,page_no):
        page1=pdf_obj.pages[page_no].extract_text()
        current_subjects=[]
        

        if page1:
            lines=page1.split('\n')

            for lineno,line in enumerate(lines):

                if lineno==14:
                    rollno=line.split(".")[1]
                        
                if lineno==19:
                        subjects=line.split(" ")[0]
                        centre_number_string=line.split(" ")[1]
                        centre_number=re.findall(r'\d+',centre_number_string)
                        centre_number=centre_number[0]
                        subjects=subjects.split("-")
                        current_subjects=subjects
                        if centre_number not in json_data:
                            json_data[centre_number]={}
                        add_rollnos_to_dict(current_subjects,rollno,centre_number)





def getting_all_subs(file):
        pdf_obj=PyPDF2.PdfReader(file)
        num_pages=len(pdf_obj.pages)
        for pageno in range(num_pages):
                subs_of_current_candidate=add_to_global_dict(pdf_obj,pageno)

#running the code to get all roll no saved into dictionary

#merging roll numbers 
def merge_rolls(data):
    merged_subjects = defaultdict(set)  # Using a set to avoid duplicates

    # Loop through both centers
    for center in data.values():
        for subject, roll_numbers in center.items():
            merged_subjects[subject].update(roll_numbers)  # Add roll numbers to the set

    # Convert sets back to lists
    return {subject: sorted(list(rolls)) for subject, rolls in merged_subjects.items()}


def sorted_centres(data):
    return sorted(data.keys(), key=lambda value: int(value) if str(value).isdigit() else str(value))


def build_attendance_summary(data, selected_centre=None):
    centres = sorted_centres(data)
    active_centre = selected_centre if selected_centre in data else (centres[0] if centres else None)
    centre_data = data.get(active_centre, {}) if active_centre else {}
    all_rolls = set()

    subjects = []
    for subject, roll_numbers in sorted(centre_data.items()):
        subjects.append(
            {
                "subject": subject,
                "roll_numbers": sorted(roll_numbers),
                "count": len(roll_numbers),
                "centre_count": 1 if roll_numbers else 0,
            }
        )
        all_rolls.update(roll_numbers)

    return {
        "centres": centres,
        "centre_count": len(centres),
        "selected_centre": active_centre,
        "subjects": subjects,
        "subject_count": len(subjects),
        "total_unique_rolls": len(all_rolls),
    }


def build_filtered_attendance_summary(data, selected_centre=None, selected_subjects=None):
    summary = build_attendance_summary(data, selected_centre=selected_centre)
    selected_subjects = selected_subjects or []
    available_subjects = {item["subject"] for item in summary["subjects"]}
    valid_selected_subjects = [subject for subject in selected_subjects if subject in available_subjects]
    selected_set = set(valid_selected_subjects)

    if selected_set:
        filtered_subjects = [item for item in summary["subjects"] if item["subject"] in selected_set]
    else:
        filtered_subjects = summary["subjects"]

    selected_rolls = sorted({roll for item in filtered_subjects for roll in item["roll_numbers"]})

    return {
        **summary,
        "selected_subjects": valid_selected_subjects,
        "filtered_subjects": filtered_subjects,
        "selected_rolls": selected_rolls,
        "selected_roll_count": len(selected_rolls),
        "selected_subject_count": len(valid_selected_subjects),
    }
