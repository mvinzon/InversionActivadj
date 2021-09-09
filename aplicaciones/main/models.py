from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class PremiumUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_premium = models.BooleanField(default=False)
    tarjeta = models.CharField(max_length=100)
    numero_tarjeta = models.IntegerField()


class Asesor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_asesor = models.BooleanField(default=False)
    numero_de_publicaciones = models.IntegerField(default=0)
