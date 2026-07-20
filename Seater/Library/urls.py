from django.urls import path

from . import views


urlpatterns = [
    path("", views.landing, name="library_home"),
    path("register/", views.register, name="library_register"),
    path("login/", views.login_view, name="library_login"),
    path("logout/", views.logout_view, name="library_logout"),
    path("dashboard/", views.dashboard, name="library_dashboard"),
    path("books/", views.all_books, name="library_all_books"),
    path("books/<int:book_id>/delete/", views.delete_book, name="library_delete_book"),
    path("admin-dashboard/", views.admin_dashboard, name="library_admin_dashboard"),
    path("admin-dashboard/export/", views.export_books_excel, name="library_export_books_excel"),
    path("admin-dashboard/employees/<int:employee_id>/delete/", views.delete_employee, name="library_delete_employee"),
]
