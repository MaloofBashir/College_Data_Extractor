from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, FileResponse
from .seating import getting_all_subs,json_data,merge_rolls
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.http import HttpResponse
import os
from datetime import datetime
from openpyxl import Workbook
from django.http import HttpResponse


merged_data={}
new_dict={}

center_nos=[]
filtered_data={}
current_data_of_centre=[]

filtered=False
# Create your views here.
def index(request):
    return render(request, 'index.html')

def Table_rollno(request):
    
    global new_dict,filtered_data,center_nos
    context = {}
    center_nos.clear()
    merged_data={}
    date_time=datetime.now()
    context["current_date_time"]=date_time
    # print("Request Headers:", request.headers)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        filtered=True
        current_data_of_centre=[]
        filtered_data={}
        print("hello ajax")
        filter_value = request.GET.get('filter', '')
        
        
        # Filter your data based on the filter_value
       
        if filter_value in new_dict.keys():
            filtered_data = new_dict[filter_value].copy()
        if(filter_value=="default"):
            filtered_data=merge_rolls(new_dict).copy()

        
        
        # Convert the filtered data to a list of dictionaries
        data = [{'subject': subject, 'roll_numbers': roll_numbers} for subject, roll_numbers in filtered_data.items()]
        current_data_of_centre=data
        
        return JsonResponse(data, safe=False)
    
    if request.method == 'POST' and 'file' in request.FILES:
        filtered=False
        filtered_data.clear()
        merged_data.clear()
        new_dict.clear()

        
        center_nos.clear()
        uploaded_file = request.FILES['file'] 
        try:
           
            getting_all_subs(uploaded_file)
        except Exception:
            error_message = "Error in uploading the file, Please ensure you upload a Pdf-Attendance Sheet from KU"
            context["error"] = error_message
        # new_dict.clear()  # Clear previous data
        new_dict.update(json_data.copy())
        merged_data=merge_rolls(new_dict)
        filtered_data.update(merged_data.copy())
        # print("is ifltered data getting popultated",filtered_data)
        context["dictionary_of_subjects"] =merged_data.copy()
        # print(new_dict)
        
        context["centre_nos"] = list(new_dict.keys())
        print("centre_number",center_nos)
        json_data.clear()
        
        
        
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
        
        print("filtered_data is",filtered_data)
        for key,values in filtered_data.items():
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


