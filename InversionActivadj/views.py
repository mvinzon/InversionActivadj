import datetime, decimal
from django.db.models import Q
import requests
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse, reverse_lazy
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
from collections import namedtuple
from django.core import serializers

from aplicaciones.main.models import CarteraInversion, PremiumUser, PerfilInversor, Asesor, Mensajes, \
    AnalisisEconomicos, CuentaAhorro, CategoriaMovimiento, CarteraAhorro
from .forms import SignUpForm, UpdateProfile
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

import pandas

API_KEY = '7N8QDLMUWNR7BH4B'
ER_API_KEY = '848d30c8c7c94343aa83977a'


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
        try:
            if self.request.user.premiumuser:
                return AnalisisEconomicos.objects.filter(
                    Q(asesor=self.request.user.premiumuser.asesor_id)
                ).order_by('-fecha')
        except Exception:
            if self.request.user.asesor:
                return AnalisisEconomicos.objects.filter(
                    Q(asesor=self.request.user.asesor)
                ).order_by('-fecha')


class AnalisisEconomicosCreate(CreateView):
    model = AnalisisEconomicos
    success_url = reverse_lazy('analisiseconomicos_list')
    fields = ['fecha', 'categoria', 'titulo', 'analisis']

    def form_valid(self, form):
        form.instance.asesor = self.request.user.asesor
        return super().form_valid(form)


class AnalisisEconomicosUpdate(UpdateView):
    model = AnalisisEconomicos
    success_url = reverse_lazy('analisiseconomicos_list')
    fields = ['fecha', 'categoria', 'titulo', 'analisis']


class AnalisisEconomicosDelete(DeleteView):
    model = AnalisisEconomicos
    success_url = reverse_lazy('analisiseconomicos_list')


def leer_analisiseconomicos(request, pk):
    print(request, pk)
    analisis_db = AnalisisEconomicos.objects.get(pk=pk)
    analisis = []
    analisis_data = []
    analisis_db_dict = model_to_dict(analisis_db)

    analisis.append(analisis_db_dict)
    if analisis is not None and bool(analisis[0]):
        for i in range(0, len(analisis)):
            AnalisisEc = namedtuple("AnalisisEc",
                                    ["id",
                                     "asesor",
                                     "categoria",
                                     "titulo",
                                     "analisis",
                                     "fecha"])

            record = AnalisisEc(analisis[i]["id"],
                                analisis[i]["asesor"],
                                analisis[i]["categoria"],
                                analisis[i]["titulo"],
                                analisis[i]["analisis"],
                                analisis[i]["fecha"])
            analisis_data.append(record)

    return render(request, 'leer_analisiseconomicos.html', {"analisis_data": analisis_data})


def visualizar_noticias(request):
    if request.method == 'POST':
        ticker = request.POST.get('smbl_news2')
        url = "https://newscatcher.p.rapidapi.com/v1/stocks"
        querystring = {"ticker": ticker, "lang": "es", "media": "True", "sort_by": "relevancy"}
        headers = {
            'x-rapidapi-host': "newscatcher.p.rapidapi.com",
            'x-rapidapi-key': "cf6361603dmsh38ad6751ae96265p117746jsne7c72722198b"
        }
        news_list = []
        news_data = []

        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            response_dict = {}
            response_dict = response.json()
            for news in response_dict['articles']:
                news_list.append(news)
        except Exception as e:
            response = None
            news_list = ''

        if news_list is not None and bool(news_list[0]):
            for i in range(0, len(news_list)):
                News = namedtuple("News",
                                  ["summary",
                                   "country",
                                   "author",
                                   "link",
                                   "language",
                                   "media",
                                   "title",
                                   "media_content",
                                   "clean_url",
                                   "rights",
                                   "rank",
                                   "topic",
                                   "published_date",
                                   "id"])

                record = News(news_list[i]["summary"],
                              news_list[i]["country"],
                              news_list[i]["author"],
                              news_list[i]["link"],
                              news_list[i]["language"],
                              news_list[i]["media"],
                              news_list[i]["title"],
                              news_list[i]["media_content"],
                              news_list[i]["clean_url"],
                              news_list[i]["rights"],
                              news_list[i]["rank"],
                              news_list[i]["topic"],
                              news_list[i]["published_date"],
                              news_list[i]["_id"])
                news_data.append(record)
    return render(request, 'visualizar_noticias.html', {"news_data": news_data})


def consultar_noticias_economicas(request):
    url = "https://bing-news-search1.p.rapidapi.com/news/search"
    querystring = {"q": "market OR economy OR investment OR stocks", "freshness": "Day", "textFormat": "Raw",
                   "safeSearch": "Off"}
    headers = {
        'x-bingapis-sdk': "true",
        'accept-language': "EN,ES",
        'x-rapidapi-host': "bing-news-search1.p.rapidapi.com",
        'x-rapidapi-key': "cf6361603dmsh38ad6751ae96265p117746jsne7c72722198b"
    }
    economic_news_list = []
    economic_news_data = []

    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
        response_dict = {}
        response_dict = response.json()

        for news in response_dict['value']:
            economic_news_list.append(news)
    except Exception as e:
        response = None
        economic_news_list = ''

    if economic_news_list is not None and bool(economic_news_list[0]):
        for i in range(0, len(economic_news_list)):
            Economic_News = namedtuple("Economic_News",
                                       ["type",
                                        "name",
                                        "url",
                                        "image",
                                        "description",
                                        "date"])

            if economic_news_list[i]["image"]:
                image = economic_news_list[i]["image"]["thumbnail"]["contentUrl"]
            else:
                image = ''
            record = Economic_News(economic_news_list[i]["_type"],
                                   economic_news_list[i]["name"],
                                   economic_news_list[i]["url"],
                                   image,
                                   economic_news_list[i]["description"],
                                   economic_news_list[i]["datePublished"])
            economic_news_data.append(record)

    return render(request, 'consultar_noticias_economicas.html', {"economic_news_data": economic_news_data})


class CuentaAhorroList(ListView):
    model = CuentaAhorro

    def get_queryset(self):
        return CuentaAhorro.objects.filter(
            user=self.request.user
        ).order_by('descripcion')


class CuentaAhorroCreate(CreateView):
    model = CuentaAhorro
    success_url = reverse_lazy('cuentaahorro_list')
    fields = ['descripcion', 'saldo', 'moneda']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CuentaAhorroUpdate(UpdateView):
    model = CuentaAhorro
    success_url = reverse_lazy('cuentaahorro_list')
    fields = ['descripcion', 'saldo', 'moneda']


class CuentaAhorroDelete(DeleteView):
    model = CuentaAhorro
    success_url = reverse_lazy('cuentaahorro_list')


class CategoriaMovimientoList(ListView):
    model = CategoriaMovimiento

    def get_queryset(self):
        return CategoriaMovimiento.objects.filter(
            user=self.request.user
        ).order_by('nombre')


class CategoriaMovimientoCreate(CreateView):
    model = CategoriaMovimiento
    success_url = reverse_lazy('categoriamovimiento_list')
    fields = ['nombre']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CategoriaMovimientoUpdate(UpdateView):
    model = CategoriaMovimiento
    success_url = reverse_lazy('categoriamovimiento_list')
    fields = ['nombre']


class CategoriaMovimientoDelete(DeleteView):
    model = CategoriaMovimiento
    success_url = reverse_lazy('categoriamovimiento_list')


class CarteraAhorroList(ListView):
    model = CarteraAhorro

    def get_queryset(self):
        return CarteraAhorro.objects.filter(
            user=self.request.user
        ).order_by('-fecha_movimiento')


class CarteraAhorroCreate(CreateView):
    model = CarteraAhorro
    success_url = reverse_lazy('carteraahorro_list')
    fields = ['cuenta', 'tipo_movimiento', 'categoria_movimiento', 'importe', 'fecha_movimiento', 'nota']

    def form_valid(self, form):
        form.instance.user = self.request.user
        self.object = form.save()
        cuenta_db = CuentaAhorro.objects.get(pk=self.object.cuenta.id)

        if self.object.tipo_movimiento.tipo == "Ingreso":
            cuenta_db.saldo += self.object.importe
        elif self.object.tipo_movimiento.tipo == "Egreso":
            cuenta_db.saldo -= self.object.importe

        cuenta_db.save()
        return HttpResponseRedirect(self.get_success_url())


class CarteraAhorroUpdate(UpdateView):
    model = CarteraAhorro
    success_url = reverse_lazy('carteraahorro_list')
    fields = ['cuenta', 'tipo_movimiento', 'categoria_movimiento', 'importe', 'fecha_movimiento', 'nota']

    def form_valid(self, form):
        movimiento_db = CarteraAhorro.objects.get(pk=self.object.id)
        cuenta_db = CuentaAhorro.objects.get(pk=self.object.cuenta.id)
        self.object = form.save()

        if self.object.importe > movimiento_db.importe:
            cuenta_db.saldo -= (self.object.importe - movimiento_db.importe)
        elif self.object.importe < movimiento_db.importe:
            cuenta_db.saldo += (movimiento_db.importe - self.object.importe)

        cuenta_db.save()
        return HttpResponseRedirect(self.get_success_url())


class CarteraAhorroDelete(DeleteView):
    model = CarteraAhorro
    success_url = reverse_lazy('carteraahorro_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        movimiento_db = CarteraAhorro.objects.get(pk=self.object.id)
        cuenta_db = CuentaAhorro.objects.get(pk=self.object.cuenta.id)

        if movimiento_db.tipo_movimiento.tipo == "Ingreso":
            cuenta_db.saldo -= movimiento_db.importe
        elif movimiento_db.tipo_movimiento.tipo == "Egreso":
            cuenta_db.saldo += movimiento_db.importe

        cuenta_db.save()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


def conversor_moneda(request):
    return render(request, 'conversor_moneda.html')


def tipos_cambio(request):
    # url = f'https://v6.exchangerate-api.com/v6/{ER_API_KEY}/codes'
    # response = requests.get(url)
    # currency_codes_dict = {}
    # currency_codes_dict = response.json()
    # currency_list = []
    #
    # for currency in currency_codes_dict['supported_codes']:
    #     currency_list.append(currency)

    if request.method == 'POST':
        curr_code = request.POST.get('curr_code')
    else:
        curr_code = 'ARS'

    url = f'https://v6.exchangerate-api.com/v6/{ER_API_KEY}/latest/{curr_code}'
    response = requests.get(url)
    rates_dict = {}
    rates_dict = response.json()
    rates_ext_dict = {}
    rates_list = []
    exchange_rates = []

    for key, value in rates_dict['conversion_rates'].items():
        if key in ['ARS', 'USD', 'GBP', 'EUR', 'JPY', 'AUD', 'BRL', 'UYU', 'CNY', 'UYU']:
            rates_ext_dict[key] = value

    for key, value in rates_ext_dict.items():
        rates_list.append([key, value])

    if rates_list is not None and bool(rates_list[0]):
        for i in range(0, len(rates_list)):
            Exchange_Rates = namedtuple("Exchange_Rates",
                                        ["Codigo",
                                         "TC"])

            record = Exchange_Rates(rates_list[i][0],
                                    rates_list[i][1])
            exchange_rates.append(record)

    return render(request, 'tipos_cambio.html', {"exchange_rates": exchange_rates})
