from django.db import models
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone


class Employee(models.Model):
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=128, blank=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return bool(self.password_hash) and check_password(raw_password, self.password_hash)


class Book(models.Model):
    added_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="books")
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=180)
    accession_number = models.CharField(max_length=80, blank=True)
    isbn = models.CharField("ISBN / Book number", max_length=40, blank=True)
    locker_no = models.CharField(max_length=50)
    subject = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField(default=1)
    publisher = models.CharField(max_length=160, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "title"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["author"]),
            models.Index(fields=["accession_number"]),
            models.Index(fields=["isbn"]),
            models.Index(fields=["subject"]),
        ]

    def __str__(self):
        return self.title
