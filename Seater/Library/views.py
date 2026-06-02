from functools import wraps
import random

from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db.models.functions import Trim
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from openpyxl import Workbook
from openpyxl.styles import Font

from .forms import BookForm, EmployeeLoginForm, EmployeeRegistrationForm
from .models import Book, Employee


def current_employee(request):
    employee_id = request.session.get("library_employee_id")
    if not employee_id:
        return None
    try:
        return Employee.objects.get(pk=employee_id)
    except Employee.DoesNotExist:
        request.session.pop("library_employee_id", None)
        return None


def require_employee(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        employee = current_employee(request)
        if not employee:
            return redirect(f"{reverse('library_login')}?next={request.path}")
        request.library_employee = employee
        return view_func(request, *args, **kwargs)

    return wrapped


def require_admin(view_func):
    @wraps(view_func)
    @require_employee
    def wrapped(request, *args, **kwargs):
        if not request.library_employee.is_admin:
            messages.error(request, "Admin access is required.")
            return redirect("library_dashboard")
        return view_func(request, *args, **kwargs)

    return wrapped


def stats_payload(books=None):
    books = books if books is not None else Book.objects.all()
    return {
        "total_books": books.count(),
        "total_quantity": books.aggregate(total=Sum("quantity"))["total"] or 0,
    }


def admin_summary_payload():
    return {
        **stats_payload(),
        "employee_total": Employee.objects.count(),
        "subject_counts": (
            Book.objects.values("subject")
            .annotate(book_count=Count("id"), total_quantity=Sum("quantity"))
            .order_by("subject")
        ),
        "locker_counts": (
            Book.objects.values("locker_no")
            .annotate(book_count=Count("id"), total_quantity=Sum("quantity"))
            .order_by("locker_no")
        ),
        "employee_counts": (
            Employee.objects.annotate(book_count=Count("books"), total_quantity=Sum("books__quantity"))
            .order_by("first_name", "last_name")
        ),
    }


def filter_books(request):
    books = Book.objects.select_related("added_by")
    query = request.GET.get("q", "").strip()
    subject = request.GET.get("subject", "").strip()

    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(author__icontains=query)
            | Q(accession_number__icontains=query)
            | Q(locker_no__icontains=query)
            | Q(subject__icontains=query)
        )
    if subject:
        books = books.annotate(clean_subject=Trim("subject")).filter(clean_subject__iexact=subject)

    return books, query, subject


def landing(request):
    employee = current_employee(request)
    if employee:
        return redirect("library_dashboard")
    return render(request, "Library/auth.html", {
        "login_form": EmployeeLoginForm(),
        "registration_form": EmployeeRegistrationForm(),
        "next_url": request.GET.get("next", ""),
    })


def register(request):
    if request.method != "POST":
        return redirect("library_home")
    form = EmployeeRegistrationForm(request.POST)
    if form.is_valid():
        employee = form.save()
        request.session["library_employee_id"] = employee.id
        messages.success(request, "Registration completed. You can start adding books now.")
        return redirect("library_dashboard")
    return render(request, "Library/auth.html", {
        "login_form": EmployeeLoginForm(),
        "registration_form": form,
        "active_panel": "register",
    })


def login_view(request):
    if request.method != "POST":
        return render(request, "Library/auth.html", {
            "login_form": EmployeeLoginForm(),
            "registration_form": EmployeeRegistrationForm(),
            "next_url": request.GET.get("next", ""),
        })
    form = EmployeeLoginForm(request.POST)
    if form.is_valid():
        employee = Employee.objects.filter(email__iexact=form.cleaned_data["email"]).first()
        password = form.cleaned_data["password"]
        if employee and (employee.check_password(password) or not employee.password_hash):
            if not employee.password_hash:
                employee.set_password(password)
                employee.save(update_fields=["password_hash"])
            request.session["library_employee_id"] = employee.id
            messages.success(request, f"Welcome, {employee.full_name}.")
            next_url = request.POST.get("next", "")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect("library_dashboard")
        form.add_error(None, "Email address or password is incorrect.")
    return render(request, "Library/auth.html", {
        "login_form": form,
        "registration_form": EmployeeRegistrationForm(),
        "active_panel": "login",
        "next_url": request.POST.get("next", ""),
    })


def logout_view(request):
    request.session.pop("library_employee_id", None)
    messages.success(request, "You have been logged out.")
    return redirect("library_home")


@require_employee
def dashboard(request):
    employee = request.library_employee
    edit_book = None
    if request.GET.get("edit"):
        edit_book = get_object_or_404(Book, pk=request.GET["edit"], added_by=employee)

    if request.method == "POST":
        edit_id = request.POST.get("book_id")
        instance = get_object_or_404(Book, pk=edit_id, added_by=employee) if edit_id else None
        form = BookForm(request.POST, instance=instance)
        if form.is_valid():
            book = form.save(commit=False)
            book.added_by = employee
            book.save()
            messages.success(request, "Book updated." if instance else "Book added.")
            return redirect("library_dashboard")
    else:
        form = BookForm(instance=edit_book)

    author_suggestions = Book.objects.exclude(author="").values_list("author", flat=True).distinct().order_by("author")
    subjects = Book.objects.exclude(subject="").values_list("subject", flat=True).distinct().order_by("subject")
    own_books = employee.books.select_related("added_by").all()

    return render(request, "Library/dashboard.html", {
        "employee": employee,
        "form": form,
        "edit_book": edit_book,
        "subjects": subjects,
        "author_suggestions": author_suggestions,
        "visible_books": own_books[:10],
        "remaining_books": own_books[10:],
        **stats_payload(employee.books.all()),
    })


@require_employee
def delete_book(request, book_id):
    employee = request.library_employee
    books = Book.objects.all() if employee.is_admin else Book.objects.filter(added_by=employee)
    book = get_object_or_404(books, pk=book_id)
    session_key = f"delete_book_captcha_{book.id}"

    if request.method == "POST":
        expected_answer = request.session.get(session_key)
        entered_answer = request.POST.get("captcha_answer", "").strip()
        if expected_answer is not None and entered_answer == str(expected_answer):
            book.delete()
            request.session.pop(session_key, None)
            messages.success(request, "Book deleted.")
            return redirect("library_admin_dashboard" if employee.is_admin else "library_dashboard")
        messages.error(request, "Captcha answer was incorrect. Please try again.")

    first_number = random.randint(2, 9)
    second_number = random.randint(2, 9)
    request.session[session_key] = first_number + second_number
    return render(request, "Library/delete_book_confirm.html", {
        "employee": employee,
        "book": book,
        "first_number": first_number,
        "second_number": second_number,
    })


def all_books(request):
    query = request.GET.get("q", "").strip()
    selected_subject = request.GET.get("subject", "").strip()
    employee = current_employee(request)
    books = Book.objects.select_related("added_by")
    if employee and not employee.is_admin:
        books = books.filter(added_by=employee)
    subjects = books.exclude(subject="").values_list("subject", flat=True).distinct().order_by("subject")
    return render(request, "Library/all_books.html", {
        "employee": employee,
        "all_books": books,
        "query": query,
        "selected_subject": selected_subject,
        "subjects": subjects,
        "show_all_books": employee is None or employee.is_admin,
        **stats_payload(books),
    })


@require_admin
def admin_dashboard(request):
    return render(request, "Library/admin_dashboard.html", {
        "employee": request.library_employee,
        "all_books": Book.objects.select_related("added_by").all(),
        **admin_summary_payload(),
    })


@require_admin
def delete_employee(request, employee_id):
    employee_to_delete = get_object_or_404(Employee, pk=employee_id)
    if employee_to_delete.id == request.library_employee.id:
        messages.error(request, "You cannot delete your own admin account.")
        return redirect("library_admin_dashboard")

    if request.method == "POST":
        employee_name = employee_to_delete.full_name or employee_to_delete.email
        employee_to_delete.delete()
        messages.success(request, f"{employee_name} and their book records were deleted.")
        return redirect("library_admin_dashboard")

    return render(request, "Library/delete_employee_confirm.html", {
        "employee": request.library_employee,
        "employee_to_delete": employee_to_delete,
        "book_count": employee_to_delete.books.count(),
    })


def add_sheet(workbook, title, headers, rows):
    sheet = workbook.create_sheet(title)
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        sheet.append(row)
    sheet.freeze_panes = "A2"
    for column in sheet.columns:
        width = max(len(str(cell.value or "")) for cell in column) + 2
        sheet.column_dimensions[column[0].column_letter].width = min(width, 42)


@require_admin
def export_books_excel(request):
    workbook = Workbook()
    workbook.remove(workbook.active)
    books = Book.objects.select_related("added_by").order_by("subject", "locker_no", "title")
    add_sheet(workbook, "All Books", [
        "Title", "Author", "Accession Number", "Locker No", "Subject",
        "Remarks", "Entered By", "Employee Email", "Created At", "Updated At",
    ], [
        [
            book.title, book.author, book.accession_number, book.locker_no, book.subject,
            book.remarks, book.added_by.full_name, book.added_by.email,
            book.created_at.strftime("%Y-%m-%d %H:%M"), book.updated_at.strftime("%Y-%m-%d %H:%M"),
        ]
        for book in books
    ])
    summary = admin_summary_payload()
    add_sheet(workbook, "By Subject", ["Subject", "Book Records"], [
        [item["subject"], item["book_count"]] for item in summary["subject_counts"]
    ])
    add_sheet(workbook, "By Locker", ["Locker No", "Book Records"], [
        [item["locker_no"], item["book_count"]] for item in summary["locker_counts"]
    ])
    add_sheet(workbook, "By Employee", ["Employee", "Email", "Book Records"], [
        [item.full_name, item.email, item.book_count] for item in summary["employee_counts"]
    ])
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="library_books_report.xlsx"'
    workbook.save(response)
    return response
