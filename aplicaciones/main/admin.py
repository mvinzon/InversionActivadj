from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Register your models here.
from aplicaciones.main.models import PremiumUser, Asesor, CarteraInversion, PerfilInversor


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class PremiumUserInline(admin.StackedInline):
    model = PremiumUser
    can_delete = False
    verbose_name_plural = 'Premium Users'


class AsesorInline(admin.StackedInline):
    model = Asesor
    can_delete = False
    verbose_name_plural = 'Asesores'


class PerfilInversorInline(admin.StackedInline):
    model = PerfilInversor
    can_delete = False
    verbose_name_plural = 'Perfil Inversores'


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = [PremiumUserInline, AsesorInline, PerfilInversorInline]
    #list_display = ('username', 'first_name', 'last_name', 'is_premium', 'tarjeta')


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(CarteraInversion)
