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



