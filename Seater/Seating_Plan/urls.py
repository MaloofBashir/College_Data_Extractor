from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('Table_rollno/', views.Table_rollno, name='Table_rollno'),
    path('result_summary/', views.result_summary, name='result_summary'),
    path('result_summary/download/', views.download_result_summary_pdf, name='download_result_summary_pdf'),
    path('attendance_summary/download/', views.download_attendance_pdf, name='download_attendance_pdf'),
    path('export_excel/', views.export_excel, name='export_excel'),
]
