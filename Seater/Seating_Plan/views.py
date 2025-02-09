from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, FileResponse
from .seating import getting_all_subs,dictionary_of_subjects
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.http import HttpResponse
import os
from datetime import datetime
from openpyxl import Workbook
from django.http import HttpResponse



new_dict={}


# Create your views here.
def index(request):
    return render(request, 'index.html')

def Table_rollno(request):

    global new_dict
    context = {}
    date_time=datetime.now()
    context["current_date_time"]=date_time
    if request.method == 'POST' and 'file' in request.FILES:
        uploaded_file = request.FILES['file'] 
        try:
           
            getting_all_subs(uploaded_file)
        except Exception:
            error_message = "Error in uploading the file, Please ensure you upload a Pdf-Attendance Sheet from KU"
            context["error"] = error_message
        new_dict=dictionary_of_subjects.copy()
        context["dictionary_of_subjects"] =new_dict
        dictionary_of_subjects.clear()
        
        
        
        # Render the response and clear the dictionary after rendering
        response = render(request, 'Table_rollno.html', context)

        # Clear dictionary after the response is rendered
        
        
        return response
    else:
        # Handle the case where the method is not POST or no file is uploaded
        return render(request, 'Table_rollno.html', context)

def export_excel(request):
    # print("dictionary is:",new_dict)
    try:
        wb=Workbook()
        ws=wb.active
        ws.title="Sheet1"
        col=1
        for key,values in new_dict.items():
            ws.cell(row=1,column=col,value=key)
            for row, value in enumerate(values,start=2):
                ws.cell(row=row,column=col,value=value)
            col+=1
        file_name="output.xlsx"
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        wb.save(file_path)
        file_url = os.path.join(settings.MEDIA_URL, file_name)
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse("Something went wrong", status=500)


