from django.contrib import admin

from .models import Book, Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "is_admin", "created_at")
    list_filter = ("is_admin",)
    search_fields = ("first_name", "last_name", "email")


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "accession_number", "subject", "locker_no", "added_by")
    list_filter = ("subject",)
    search_fields = ("title", "author", "accession_number", "locker_no", "subject")
    autocomplete_fields = ("added_by",)
