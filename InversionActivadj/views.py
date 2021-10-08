import datetime
from django.db.models import Q
import requests
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse, reverse_lazy
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
from collections import namedtuple

from aplicaciones.main.models import CarteraInversion, PremiumUser, PerfilInversor, Asesor, Mensajes, AnalisisEconomicos
from .forms import SignUpForm, UpdateProfile
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

import pandas

API_KEY = '7N8QDLMUWNR7BH4B'


def inicio(request):
    return render(request, "inicio.html")


def login2(request):
    return render(request, "login.html")


def contacto(request):
    if request.method == "POST":
        subject = "Contacto IA"
        message = request.POST["mensaje"] + " " + request.POST["email"]
        email_from = settings.EMAIL_HOST_USER
        recipient_list = ["maximiliano.vinzon@usal.edu.ar"]
        send_mail(subject, message, email_from, recipient_list)
        return render(request, "enviado.html")

    return render(request, "contacto.html")


class SignUpView(CreateView):
    form_class = SignUpForm

    def form_valid(self, form):
        '''
        En este parte, si el formulario es valido guardamos lo que se obtiene de él y usamos authenticate para que el usuario incie sesión luego de haberse registrado y lo redirigimos al index
        '''
        form.save()
        usuario = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        usuario = authenticate(username=usuario, password=password)
        login2(self.request)
        return redirect('/')


def registro(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('inicio')
    else:
        form = SignUpForm()
    return render(request, "registro.html", {'form': form})


@transaction.atomic
def update_profile(request):
    args = {}

    if request.method == 'POST':
        form = UpdateProfile(request.POST, instance=request.user)
        form.actual_user = request.user
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('perfil'))
    else:
        form = UpdateProfile(instance=request.user)

    args['form'] = form
    return render(request, 'perfil.html', {
        'form': form,
    })


def asesoria(request):
    if request.method == 'POST':
        if request.POST.get('mje_asesor'):
            print(request.user.premiumuser.asesor_id.user)
            mje = Mensajes(remitente=request.user,
                           asunto='Contacto asesor',
                           mensaje=request.POST.get('mje_asesor'),
                           fecha=datetime.datetime.now(),
                           destinatario=request.user.premiumuser.asesor_id.user)
            mje.save()
    return render(request, 'asesoria.html')


class MensajesCreate(CreateView):
    model = Mensajes
    success_url = reverse_lazy('mensajes_list')
    fields = ['asunto', 'mensaje', 'destinatario']

    def form_valid(self, form):
        form.instance.remitente = self.request.user
        form.instance.fecha = datetime.datetime.now()
        return super().form_valid(form)
    # template_name = 'mensajes_create.html'
    # form_class = MensajesForm
    #
    # def get_form_kwargs(self):
    #     kwargs = super(MensajesCreate, self).get_form_kwargs()
    #     kwargs['remitente'] = self.request.user
    #     return kwargs


class MensajesList(ListView):
    model = Mensajes

    def get_queryset(self):
        return Mensajes.objects.filter(
            Q(remitente=self.request.user) | Q(destinatario=self.request.user)
        ).order_by('-fecha')


def bandeja_entrada(request):
    return render(request, 'bandeja_entrada.html')


def buscar_activo(request):
    all_stocks = []
    # if 'term' in request.GET:
    #     # ts = TimeSeries(key=API_KEY, output_format='json')
    #     Items = namedtuple("Items", ["Simbolo"])
    #     tickers = list()
    #     # search = ts.get_symbol_search(request.GET.get('term'))
    #     # search = search_df.to_json()
    #
    #     term = request.GET.get('term')
    #     url = f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords="{term}"&apikey="{API_KEY}"'
    #     r = requests.get(url)
    #     search = r.json()
    #     print(search[0]["01. symbol"])
    #     if search is not None:
    #         for ticker in search:
    #             record = ticker
    #             # print(record)
    #             tickers.append(record)
    #
    #     return JsonResponse(tickers, safe=False)

    if request.method == 'POST':
        ticker = request.POST['buscar']
        ts = TimeSeries(key=API_KEY, output_format='json')
        fd = FundamentalData(key=API_KEY, output_format='json')
        Stock = namedtuple("Stock", ["Simbolo", "Precio", "Variacion", "Volumen"])
        try:
            data = ts.get_quote_endpoint(ticker)
            fdata = fd.get_company_overview(ticker)
        except Exception as e:
            data = None
            all_stocks = ''

        if data is not None and bool(data[0]):
            record = Stock(data[0]["01. symbol"],
                           data[0]["05. price"], data[0]["10. change percent"],
                           data[0]["06. volume"])
            all_stocks.append(record)

    return render(request, 'buscar_activo.html', {"all_stocks": all_stocks})


def consultar_activo(request):
    stock_data = []
    if request.method == 'POST':
        ticker = request.POST["simbolo"]
        ts = TimeSeries(key=API_KEY, output_format='json')
        fd = FundamentalData(key=API_KEY, output_format='json')

        try:
            data = ts.get_quote_endpoint(ticker)
            fdata = fd.get_company_overview(ticker)
        except Exception as e:
            data = None
            stock_data = ''

        if data is not None and bool(data[0]):
            Datos = namedtuple("Datos", ["Simbolo",
                                         "TipoActivo",
                                         "Nombre",
                                         "Descripcion",
                                         "Mercado",
                                         "Moneda",
                                         "Pais",
                                         "Sector",
                                         "Industria",
                                         "Max52S",
                                         "Min52S",
                                         "Precio",
                                         "Variacion",
                                         "Volumen"])

            record = Datos(data[0]["01. symbol"],
                           fdata[0]["AssetType"],
                           fdata[0]["Name"],
                           fdata[0]["Description"],
                           fdata[0]["Exchange"],
                           fdata[0]["Currency"],
                           fdata[0]["Country"],
                           fdata[0]["Sector"],
                           fdata[0]["Industry"],
                           fdata[0]["52WeekHigh"],
                           fdata[0]["52WeekLow"],
                           data[0]["05. price"],
                           data[0]["10. change percent"],
                           data[0]["06. volume"])
            stock_data.append(record)

    return render(request, 'consultar_activo.html', {"stock_data": stock_data})


class CarteraInversionList(ListView):
    model = CarteraInversion

    def get_queryset(self):
        return CarteraInversion.objects.filter(
            user=self.request.user
        ).order_by('simbolo')


class CarteraInversionCreate(CreateView):
    model = CarteraInversion
    success_url = reverse_lazy('inversion_list')
    fields = ['simbolo', 'precio_compra', 'cantidad_compra', 'fecha_compra']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CarteraInversionUpdate(UpdateView):
    model = CarteraInversion
    success_url = reverse_lazy('inversion_list')
    fields = ['simbolo', 'precio_compra', 'cantidad_compra', 'fecha_compra', 'cantidad_venta', 'precio_ult_venta']


class CarteraInversionDelete(DeleteView):
    model = CarteraInversion
    success_url = reverse_lazy('inversion_list')


class PremiumUserCreate(CreateView):
    model = PremiumUser
    success_url = reverse_lazy('asesoria')
    fields = ['tarjeta', 'numero_tarjeta']
    asesor = Asesor.objects.order_by("?").first()

    def form_valid(self, form, asesor=asesor):
        form.instance.user = self.request.user
        form.instance.is_premium = True
        form.instance.asesor = asesor.id
        return super().form_valid(form)


def gestionar_analisis(request):
    return render(request, 'gestionar_analisis.html')


def perfil_inversor(request):
    if request.method == 'POST':
        respuestas = []
        conservador = 0
        moderado = 0
        agresivo = 0
        perfil = None
        descripcion = None
        respuestas.append(request.POST.get('conocimiento_financiero'))
        respuestas.append(request.POST.get('inversion_previa'))
        respuestas.append(request.POST.get('porcentaje_ahorros'))
        respuestas.append(request.POST.get('plazo_inversion'))
        respuestas.append(request.POST.get('inversion_pg'))
        respuestas.append(request.POST.get('disminucion_capital'))

        for respuesta in respuestas:
            if respuesta == '1':
                conservador += 1
            elif respuesta == '2':
                moderado += 1
            elif respuesta == '3':
                agresivo += 1

        if conservador > moderado and conservador > agresivo:
            perfil = 'Conservador'
            descripcion = 'Su principal objetivo es la preservaci[on del capital, o un crecimiento moderado sin ' \
                          'asumir importantes riesgos. Otorga valor a la liquidez o disponibilidad de sus ' \
                          'inversiones, y opta por instrumentos en los que pueda minimizar el impacto de las ' \
                          'fluctuaciones del mercado. '
        elif agresivo > conservador and agresivo > moderado:
            perfil = 'Agresivo'
            descripcion = 'Se caracteriza por realizar inversiones cuyo objetivo principal es maximizar el ' \
                          'rendimiento de su cartera, y está dispuesto a afrontar altos riesgos y volatilidad. No le ' \
                          'asigna un alto nivel de importancia a la disponibilidad inmediata de sus inversiones, ' \
                          'y soporta asumir pérdidas de capital. '
        else:
            perfil = 'Moderado'
            descripcion = 'Su objetivo busca un balance entre rendimiento y seguridad. Está dispuesto a asumir ' \
                          'ciertas oscilaciones y/o tolerar ciertos riesgos, con el objetivo de obtener una mayor ' \
                          'rentabilidad a mediano/largo plazo. Es un perfil intermedio entre el inversor conservador ' \
                          'y agresivo. '

        pi = PerfilInversor(user=request.user, perfil=perfil, descripcion=descripcion)
        pi.save()
    return render(request, 'perfil_inversor.html')


class AnalisisEconomicosList(ListView):
    model = AnalisisEconomicos

    def get_queryset(self):
        return AnalisisEconomicos.objects.filter(
            Q(asesor=self.request.user.premiumuser.asesor_id)
        ).order_by('-fecha')


def visualizar_noticias(request):
    if request.method == 'POST':
        print(request.POST.get('smbl_news2'))
    return render(request, 'visualizar_noticias.html')