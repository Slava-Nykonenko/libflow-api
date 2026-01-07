from django.db import models
from django.utils.translation import gettext as _


# Create your models here.
class Book(models.Model):
    class CoverChoises(models.TextChoices):
        HARD = "HARD", _("Hard")
        SOFT = "SOFT", _("Soft")

    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    cover = models.CharField(
        max_length=100, choices=CoverChoises, default=CoverChoises.HARD
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=2, decimal_places=2)

    def __str__(self):
        return self.title + " - " + self.author
