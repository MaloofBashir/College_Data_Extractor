from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import Book, Employee


class EmployeeRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    class Meta:
        model = Employee
        fields = ["first_name", "last_name", "email", "password"]
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if Employee.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An employee is already registered with this email address.")
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self, commit=True):
        password = self.cleaned_data.pop("password")
        employee = super().save(commit=False)
        employee.set_password(password)
        if commit:
            employee.save()
        return employee


class EmployeeLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def clean_email(self):
        return self.cleaned_data["email"].lower()


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "accession_number",
            "locker_no",
            "subject",
            "remarks",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"autocomplete": "off", "autofocus": True}),
            "author": forms.TextInput(attrs={"list": "author-suggestions", "autocomplete": "off"}),
            "accession_number": forms.TextInput(attrs={"autocomplete": "off"}),
            "subject": forms.TextInput(attrs={"list": "subject-suggestions", "autocomplete": "off"}),
            "remarks": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_canonical_text(self, field_name):
        value = " ".join(self.cleaned_data[field_name].split())
        if not value:
            return value

        matches = Book.objects.filter(**{f"{field_name}__iexact": value})
        if self.instance.pk:
            matches = matches.exclude(pk=self.instance.pk)
        existing_value = matches.values_list(field_name, flat=True).first()
        return existing_value or value

    def clean_title(self):
        return self.clean_canonical_text("title")

    def clean_author(self):
        return self.clean_canonical_text("author")

    def clean_subject(self):
        return self.clean_canonical_text("subject")
