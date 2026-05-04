from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('Table_rollno/', views.Table_rollno, name='Table_rollno'),
    path('result_summary/', views.result_summary, name='result_summary'),
    path('export_excel/', views.export_excel, name='export_excel'),
]
