from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Employee",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("first_name", models.CharField(max_length=80)),
                ("last_name", models.CharField(max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["first_name", "last_name"],
            },
        ),
        migrations.CreateModel(
            name="Book",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("author", models.CharField(max_length=180)),
                ("isbn", models.CharField(blank=True, max_length=40, verbose_name="ISBN / Book number")),
                ("locker_no", models.CharField(max_length=50)),
                ("subject", models.CharField(max_length=120)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("publisher", models.CharField(blank=True, max_length=160)),
                ("edition", models.CharField(blank=True, max_length=80)),
                ("publication_year", models.PositiveIntegerField(blank=True, null=True)),
                ("rack_no", models.CharField(blank=True, max_length=60, verbose_name="Rack / shelf no")),
                ("language", models.CharField(blank=True, max_length=80)),
                ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("source", models.CharField(blank=True, max_length=160, verbose_name="Purchase / donation source")),
                ("status", models.CharField(choices=[("available", "Available"), ("reference", "Reference only"), ("repair", "Under repair"), ("lost", "Lost")], default="available", max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("added_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="books", to="Library.employee")),
            ],
            options={
                "ordering": ["-created_at", "title"],
            },
        ),
        migrations.AddIndex(
            model_name="book",
            index=models.Index(fields=["title"], name="Library_boo_title_a5ed17_idx"),
        ),
        migrations.AddIndex(
            model_name="book",
            index=models.Index(fields=["author"], name="Library_boo_author_06dddf_idx"),
        ),
        migrations.AddIndex(
            model_name="book",
            index=models.Index(fields=["isbn"], name="Library_boo_isbn_65df74_idx"),
        ),
        migrations.AddIndex(
            model_name="book",
            index=models.Index(fields=["subject"], name="Library_boo_subject_7475e9_idx"),
        ),
    ]
