from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class PremiumUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_premium = models.BooleanField(default=False)
    tarjeta = models.CharField(max_length=100)
    numero_tarjeta = models.BigIntegerField()


class Asesor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_asesor = models.BooleanField(default=False)
    numero_de_publicaciones = models.IntegerField(default=0)


class CarteraInversion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    simbolo = models.CharField(max_length=6)
    descripcion = models.CharField(max_length=150)
    precio_compra = models.FloatField()
    cantidad_compra = models.IntegerField()
    fecha_compra = models.DateField()
    cantidad_venta = models.IntegerField(blank=True, default=0)
    precio_ult_venta = models.FloatField(blank=True, default=0)
    ganancias_perdidas = models.FloatField(blank=True, default=0)
