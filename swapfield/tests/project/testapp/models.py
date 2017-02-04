from django.db import models
from swapfield.fields import SwapIntegerField


class Team(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        app_label = 'Testapp'


class Player(models.Model):
    name = models.CharField(max_length=30)
    team = models.ForeignKey(Team)
    number = SwapIntegerField(unique_for_fields=['team'])

    class Meta:
        app_label = 'Testapp'
