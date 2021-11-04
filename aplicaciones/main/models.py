from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Asesor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_asesor = models.BooleanField(default=False)
    numero_de_publicaciones = models.IntegerField(default=0)


class PremiumUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_premium = models.BooleanField(default=False)
    tarjeta = models.CharField(max_length=100)
    numero_tarjeta = models.BigIntegerField()
    asesor_id = models.ForeignKey(Asesor, on_delete=models.CASCADE, default=1)


class CarteraInversion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    simbolo = models.CharField(max_length=6)
    descripcion = models.CharField(max_length=150)
    precio_compra = models.DecimalField(max_digits=19, decimal_places=2)
    cantidad_compra = models.IntegerField()
    fecha_compra = models.DateField()
    cantidad_venta = models.IntegerField(blank=True, default=0)
    precio_ult_venta = models.DecimalField(blank=True, default=0, max_digits=19, decimal_places=2)
    ganancias_perdidas = models.DecimalField(blank=True, default=0, max_digits=19, decimal_places=2)


class PerfilInversor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    perfil = models.CharField(max_length=100, blank=True, default='')
    descripcion = models.CharField(max_length=1000, blank=True, default='')


class Mensajes(models.Model):
    remitente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='send')
    asunto = models.CharField(max_length=100)
    mensaje = models.CharField(max_length=1000)
    fecha = models.DateTimeField()
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receive')


class AnalisisEconomicos(models.Model):
    asesor = models.ForeignKey(Asesor, on_delete=models.CASCADE)
    categoria = models.CharField(max_length=100)
    titulo = models.CharField(max_length=100)
    analisis = models.TextField(max_length=2000)
    fecha = models.DateTimeField()


class CuentaAhorro(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=120)
    saldo = models.DecimalField(blank=True, default=0, max_digits=19, decimal_places=2)
    moneda = models.CharField(max_length=80)

    def __str__(self):
        return self.descripcion


class TipoMovimiento(models.Model):
    tipo = models.CharField(max_length=80)

    def __str__(self):
        return self.tipo


class CategoriaMovimiento(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=180)

    def __str__(self):
        return self.nombre


class CarteraAhorro(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cuenta = models.ForeignKey(CuentaAhorro, on_delete=models.DO_NOTHING)
    tipo_movimiento = models.ForeignKey(TipoMovimiento, on_delete=models.DO_NOTHING, blank=True)
    categoria_movimiento = models.ForeignKey(CategoriaMovimiento, on_delete=models.DO_NOTHING)
    importe = models.DecimalField(blank=True, default=0, max_digits=19, decimal_places=2)
    fecha_movimiento = models.DateTimeField()
    nota = models.CharField(max_length=300, blank=True)


class CodigoMoneda(models.Model):
    codigo = models.CharField(max_length=3)
    en_descr = models.CharField(max_length=100)
    sp_descr = models.CharField(max_length=100, blank=True)


class Presupuesto(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo_movimiento = models.ForeignKey(TipoMovimiento, on_delete=models.DO_NOTHING, blank=True)
    categoria_movimiento = models.ForeignKey(CategoriaMovimiento, on_delete=models.DO_NOTHING)
    importe = models.DecimalField(blank=True, default=0, max_digits=19, decimal_places=2)
    mes = models.IntegerField()
    anio = models.IntegerField()
