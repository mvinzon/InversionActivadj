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
    PremiumUserCreate, perfil_inversor, bandeja_entrada, MensajesList, MensajesCreate, \
    AnalisisEconomicosList, visualizar_noticias, consultar_noticias_economicas, CuentaAhorroList, CuentaAhorroCreate, \
    CuentaAhorroUpdate, CuentaAhorroDelete, CategoriaMovimientoList, CategoriaMovimientoCreate, \
    CategoriaMovimientoUpdate, CategoriaMovimientoDelete, CarteraAhorroList, CarteraAhorroCreate, CarteraAhorroUpdate, \
    CarteraAhorroDelete, AnalisisEconomicosDelete, AnalisisEconomicosUpdate, AnalisisEconomicosCreate, \
    leer_analisiseconomicos, conversor_moneda, tipos_cambio, reportes_ahorro, cartera_inversion_rendimiento, \
    cotizaciones, PresupuestoList, PresupuestoCreate, PresupuestoUpdate, PresupuestoDelete

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
    path(r'perfil_inversor/', perfil_inversor, name='perfil_inversor'),
    path(r'bandeja_entrada/listar/', MensajesList.as_view(template_name='mensajes_list.html'), name='mensajes_list'),
    path(r'bandeja_entrada/nuevo/', MensajesCreate.as_view(template_name='mensajes_form.html'), name='mensajes_create'),
    path(r'analisis_economicos/listar/', AnalisisEconomicosList.as_view(template_name='analisiseconomicos_list.html'), name='analisiseconomicos_list'),
    path(r'analisis_economicos/nuevo/',
         AnalisisEconomicosCreate.as_view(template_name='analisiseconomicos_form.html'),
         name='analisiseconomicos_create'),
    path(r'analisis_economicos/modificar/<slug:pk>',
         AnalisisEconomicosUpdate.as_view(template_name='analisiseconomicos_form.html'),
         name='analisiseconomicos_edit'),
    path(r'analisis_economicos/borrar/<slug:pk>',
         AnalisisEconomicosDelete.as_view(template_name='analisiseconomicosconfirmdelete.html'),
         name='analisiseconomicos_delete'),
    path(r'analisis_economicos/leer/<slug:pk>', leer_analisiseconomicos, name='leer_analisiseconomicos'),
    path(r'consultar_activo/noticias/', visualizar_noticias, name='visualizar_noticias'),
    path(r'consultar_noticias_economicas/', consultar_noticias_economicas, name='consultar_noticias_economicas'),
    path(r'cartera_ahorro/cuentas/listar/', CuentaAhorroList.as_view(template_name='cuentaahorro_list.html'),
         name='cuentaahorro_list'),
    path(r'cartera_ahorro/cuentas/nuevo/', CuentaAhorroCreate.as_view(template_name='cuentaahorro_form.html'),
         name='cuentaahorro_create'),
    path(r'cartera_ahorro/cuentas/modificar/<slug:pk>',
         CuentaAhorroUpdate.as_view(template_name='cuentaahorro_form.html'), name='cuentaahorro_edit'),
    path(r'cartera_ahorro/cuentas/borrar/<slug:pk>',
         CuentaAhorroDelete.as_view(template_name='cuentaahorroconfirmdelete.html'), name='cuentaahorro_delete'),
    path(r'cartera_ahorro/categorias/listar/', CategoriaMovimientoList.as_view(template_name='categoriamovimiento_list.html'),
         name='categoriamovimiento_list'),
    path(r'cartera_ahorro/categorias/nuevo/', CategoriaMovimientoCreate.as_view(template_name='categoriamovimiento_form.html'),
         name='categoriamovimiento_create'),
    path(r'cartera_ahorro/categorias/modificar/<slug:pk>',
         CategoriaMovimientoUpdate.as_view(template_name='categoriamovimiento_form.html'), name='categoriamovimiento_edit'),
    path(r'cartera_ahorro/categorias/borrar/<slug:pk>',
         CategoriaMovimientoDelete.as_view(template_name='categoriamovimientoconfirmdelete.html'), name='categoriamovimiento_delete'),
    path(r'cartera_ahorro/listar/',
         CarteraAhorroList.as_view(template_name='carteraahorro_list.html'),
         name='carteraahorro_list'),
    path(r'cartera_ahorro/nuevo/',
         CarteraAhorroCreate.as_view(template_name='carteraahorro_form.html'),
         name='carteraahorro_create'),
    path(r'cartera_ahorro/modificar/<slug:pk>',
         CarteraAhorroUpdate.as_view(template_name='carteraahorro_form.html'),
         name='carteraahorro_edit'),
    path(r'cartera_ahorro/borrar/<slug:pk>',
         CarteraAhorroDelete.as_view(template_name='carteraahorroconfirmdelete.html'),
         name='carteraahorro_delete'),
    path(r'conversor_moneda/', conversor_moneda, name='conversor_moneda'),
    path(r'tipos_cambio/', tipos_cambio, name='tipos_cambio'),
    path(r'reportes_ahorro/', reportes_ahorro, name='reportes_ahorro'),
    path(r'cartera_inversion_rendimiento/', cartera_inversion_rendimiento, name='cartera_inversion_rendimiento'),
    path(r'cotizaciones/', cotizaciones, name='cotizaciones'),
    path(r'presupuesto/listar/',
         PresupuestoList.as_view(template_name='presupuesto_list.html'),
         name='presupuesto_list'),
    path(r'presupuesto/nuevo/',
         PresupuestoCreate.as_view(template_name='presupuesto_form.html'),
         name='presupuesto_create'),
    path(r'presupuesto/modificar/<slug:pk>',
         PresupuestoUpdate.as_view(template_name='presupuesto_form.html'),
         name='presupuesto_edit'),
    path(r'presupuesto/borrar/<slug:pk>',
         PresupuestoDelete.as_view(template_name='presupuestoconfirmdelete.html'),
         name='presupuesto_delete'),
]
