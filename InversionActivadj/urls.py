"""InversionActivadj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from InversionActivadj.views import inicio, login2, contacto, registro, update_profile, asesoria, buscar_activo, \
    CarteraInversionList, CarteraInversionCreate, CarteraInversionUpdate, CarteraInversionDelete, consultar_activo, \
    PremiumUserCreate, gestionar_analisis

urlpatterns = [
    path('admin/', admin.site.urls),
    path('inicio/', inicio, name='inicio'),
    #path('login/', login),
    path('contacto/', contacto, name='contacto'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('enviado/', contacto, name='enviado'),
    path('registro/', registro, name='registro'),
    path(r'perfil/', update_profile, name='perfil'),
    path(r'asesoria/', asesoria, name='asesoria'),
    path(r'asesoria/nuevo/', PremiumUserCreate.as_view(template_name='premiumuser_form.html'), name='premiumuser'),
    path(r'buscar_activo/', buscar_activo, name='buscar_activo'),
    path(r'consultar_activo/', consultar_activo, name='consultar_activo'),
    path(r'cartera_inversion/listar/', CarteraInversionList.as_view(template_name='carterainversion_list.html'), name='inversion_list'),
    path(r'cartera_inversion/nuevo/', CarteraInversionCreate.as_view(template_name='carterainversion_form.html'), name='inversion_create'),
    path(r'cartera_inversion/modificar/<slug:pk>', CarteraInversionUpdate.as_view(template_name='carterainversion_form.html'), name='inversion_edit'),
    path(r'cartera_inversion/borrar/<slug:pk>', CarteraInversionDelete.as_view(template_name='carterainversionconfirmdelete.html'), name='inversion_delete'),
    path(r'gestionar_analisis/', gestionar_analisis, name='gestionar_analisis'),
]
