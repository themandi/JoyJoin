from django.db import models
from common.models import User
from django.core.exceptions import ValidationError


class ReportCategory(models.Model):
    """
    Klasa reprezentująca kategorie zgłoszenia.

    Pola:
        name: nazwa kategorii (str)
    """
    name = models.TextField(null=False, blank=False)

    def __str__(self):
        return 'kategoria zgłoszenia: {}'.format(
            self.name,
        )

    def save(self, *args, **kwargs):
        """
        Zapisuje model kategorii zgłoszenia upewniając się że jest poprawna.
        """
        if not self.name:
            raise ValidationError(
                'Kategoria zgłoszenia nie może zostać zapisana: brak nazwy.')

        super().save(args, kwargs)


class Report(models.Model):
    """
    Klasa reprezentująca zgłoszenie.

    Pola:
        text: treść zgłoszenia (str)
        category: kategoria zgłoszenia (report.models.ReportCategory)
        user: autor zgłoszenia (common.models.User)
            lub None jeśli autor został usunięty
            lub jeśli zgłoszenie jest od niezalogowanego użytkownika
    """
    text = models.TextField(null=False, blank=False)
    category = models.ForeignKey(
        ReportCategory, on_delete=models.CASCADE, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        if self.user:
            return 'zgłoszenie o treści "{}" dotyczace "{}" użytkownika "{}"'.format(
                self.text,
                self.category.name,
                self.user.login
            )
        else:
            return 'zgłoszenie o treści "{}" dotyczace "{}" niezalogowanego użytkownika'.format(
                self.text,
                self.category.name,
            )

    def save(self, *args, **kwargs):
        """
        Zapisuje model zgłoszenia upewniając się że jest poprawny.
        """
        if not self.text:
            raise ValidationError(
                'Zgłoszenie nie może zostać zapisane: brak treści.')

        try:
            self.category
        except(ReportCategory.DoesNotExist):
            raise ValidationError(
                'Zgłoszenie nie może zostać zapisane: brak kategorii zgłoszenia.')

        super().save(args, kwargs)
