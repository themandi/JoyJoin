from django.contrib import admin

from .models import Report, ReportCategory


models = [
    Report,
    ReportCategory
]

for model in models:
    admin.site.register(model)
