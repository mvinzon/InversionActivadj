import datetime
from decimal import Decimal
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
from django.utils.timezone import now

from aplicaciones.main.models import CarteraInversion, PremiumUser, PerfilInversor, Asesor, Mensajes, \
    AnalisisEconomicos, CuentaAhorro, CategoriaMovimiento, CarteraAhorro, Presupuesto
from .forms import SignUpForm, UpdateProfile
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
import json
import pandas
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset
from torch.utils.data import DataLoader

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from io import BytesIO
import base64

API_KEY = '7N8QDLMUWNR7BH4B'
ER_API_KEY = '848d30c8c7c94343aa83977a'
BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAAM8%2FVQEAAAAA2VyGVEAdDRX2J2dZb1DHbUp9BDg%3DXZrkrVtQP6tVEUEsxQZZh9J9ZdCAiJSeD0dLztnevb2Jre82ee'


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
    stock = []
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
        # ts = TimeSeries(key=API_KEY, output_format='json')
        # fd = FundamentalData(key=API_KEY, output_format='json')
        stock = []
        Stock = namedtuple("Stock", ["Simbolo", "Precio", "Variacion", "Volumen"])


        url = "https://yh-finance.p.rapidapi.com/stock/v2/get-summary"
        querystring = {"symbol": f"{ticker}"}
        headers = {
            'x-rapidapi-host': "yh-finance.p.rapidapi.com",
            'x-rapidapi-key': "cf6361603dmsh38ad6751ae96265p117746jsne7c72722198b"
        }

        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            data = {}
            data = response.json()
            # data = ts.get_quote_endpoint(ticker)
            # fdata = fd.get_company_overview(ticker)
            # print(data.keys())
            # print(data['symbol'],
            #       data['price']['regularMarketPrice']['fmt'],
            #       data['price']['regularMarketChangePercent']['fmt'],
            #       data['price']['regularMarketVolume']['longFmt'])
        except Exception as e:
            data = None
            stock = ''

        if data is not None and bool(data['symbol']):
            record = Stock(data['symbol'],
                           data['price']['regularMarketPrice']['fmt'],
                           data['price']['regularMarketChangePercent']['fmt'],
                           data['price']['regularMarketVolume']['longFmt'])
            stock.append(record)
        # if data is not None and bool(data[0]):
        #     record = Stock(data[0]["01. symbol"],
        #                    data[0]["05. price"],
        #                    data[0]["10. change percent"],
        #                    data[0]["06. volume"])
        #     stock.append(record)

    return render(request, 'buscar_activo.html', {"stock": stock})


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

        tweets = get_tweets(ticker)
        plots = predecir(ticker)

        pred_variacion = ((plots['precio_maniana'] - plots['precio_actual']) * 100) / plots['precio_actual']
        perfil = request.user.perfilinversor.perfil

        if perfil == 'Agresivo' and abs(pred_variacion) > 1:
            if pred_variacion > 0:
                recomendacion = 'Comprar'
            else:
                recomendacion = 'Vender'
        elif perfil == 'Moderado' and abs(pred_variacion) > 3:
            if pred_variacion > 0:
                recomendacion = 'Comprar'
            else:
                recomendacion = 'Vender'
        elif perfil == 'Conservador' and abs(pred_variacion) > 5:
            if pred_variacion > 0:
                recomendacion = 'Comprar'
            else:
                recomendacion = 'Vender'
        else:
            recomendacion = 'Mantener'

        plots['recomendacion'] = recomendacion

    return render(request, 'consultar_activo.html', {"stock_data": stock_data, "tweets": tweets, "plots": plots})


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {BEARER_TOKEN}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r


def connect_to_endpoint(url, params):
    response = requests.get(url, auth=bearer_oauth, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def get_tweets(ticker):
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    query_params = {'query': f'({ticker.lower()} OR 'f'{ticker.upper()}) -is:retweet -is:reply',
                    'tweet.fields': 'author_id,lang',
                    'max_results': '20',
                    'user.fields': 'username', }
    json_response = connect_to_endpoint(search_url, query_params)
    # print(json_response['data'])
    # print(json.dumps(json_response, indent=4, sort_keys=True))

    tweets_list = []
    tweets_data = []
    response_dict = {}
    # response_dict = json_response.json()
    for tweet in json_response['data']:
        if tweet['lang'] == 'es' or tweet['lang'] == 'en':
            tweets_list.append(tweet)

    # print(tweets_list)
    if tweets_list is not None and bool(tweets_list[0]):
        for i in range(0, len(tweets_list)):
            counter = i + 1
            Tweets = namedtuple("Tweets",
                                ["counter",
                                 "author_id",
                                 "id",
                                 "lang",
                                 "text"])

            record = Tweets(counter,
                            tweets_list[i]["author_id"],
                            tweets_list[i]["id"],
                            tweets_list[i]["lang"],
                            tweets_list[i]["text"])
            tweets_data.append(record)
    # print(tweets_data)
    return tweets_data


class CarteraInversionList(ListView):
    model = CarteraInversion

    def get_queryset(self):
        return CarteraInversion.objects.filter(
            user=self.request.user
        ).order_by('simbolo')


class CarteraInversionCreate(CreateView):
    model = CarteraInversion
    success_url = reverse_lazy('inversion_list')
    fields = ['simbolo', 'descripcion', 'precio_compra', 'cantidad_compra', 'fecha_compra']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CarteraInversionUpdate(UpdateView):
    model = CarteraInversion
    success_url = reverse_lazy('inversion_list')
    fields = ['simbolo', 'descripcion', 'precio_compra', 'cantidad_compra', 'fecha_compra', 'cantidad_venta',
              'precio_ult_venta']

    def form_valid(self, form):
        cartera_db = CarteraInversion.objects.get(pk=self.object.id)
        venta = 0
        importe_venta = 0
        self.object = form.save()

        if self.object.cantidad_venta != cartera_db.cantidad_venta:
            venta = (self.object.cantidad_venta - cartera_db.cantidad_venta)
            importe_venta = venta * self.object.precio_ult_venta
            cartera_db.ganancias_perdidas += (importe_venta - (venta * self.object.precio_compra))
            cartera_db.cantidad_compra -= venta

        cartera_db.save()
        return HttpResponseRedirect(self.get_success_url())


class CarteraInversionDelete(DeleteView):
    model = CarteraInversion
    success_url = reverse_lazy('inversion_list')


def cartera_inversion_rendimiento(request):
    movimientos_cartera_inversion = []
    simbolos_list = []
    simbolos = ''
    simbolos_dict = {}

    for movimiento in CarteraInversion.objects.filter(user=request.user):
        simbolos_list.append(movimiento.simbolo)
        simbolos += (movimiento.simbolo + ',')

    url = "https://yh-finance.p.rapidapi.com/market/v2/get-quotes"
    querystring = {"region": "US", "symbols": simbolos}
    headers = {
        'x-rapidapi-host': "yh-finance.p.rapidapi.com",
        'x-rapidapi-key': "cf6361603dmsh38ad6751ae96265p117746jsne7c72722198b"
    }

    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
        response_dict = response.json()
        for i in range(0, len(simbolos_list)):
            simbolos_dict[response_dict["quoteResponse"]["result"][i]["symbol"]] = \
                response_dict["quoteResponse"]["result"][i]["regularMarketPrice"]
    except Exception as e:
        response = None

    for movimiento in CarteraInversion.objects.filter(user=request.user):
        Tenencias = namedtuple("Tenencias",
                               ["simbolo",
                                "descripcion",
                                "precio_compra",
                                "cantidad_compra",
                                "fecha_compra",
                                "ganancias_perdidas",
                                "precio_actual",
                                "variacion",
                                "variacion_capital"])

        variacion = abs(Decimal.from_float(
            simbolos_dict[movimiento.simbolo]) - movimiento.precio_compra) * 100 / movimiento.precio_compra
        if Decimal.from_float(simbolos_dict[movimiento.simbolo]) < movimiento.precio_compra:
            variacion *= -1
        variacion_capital = (Decimal.from_float(
            simbolos_dict[movimiento.simbolo]) - movimiento.precio_compra) * movimiento.cantidad_compra
        record = Tenencias(movimiento.simbolo,
                           movimiento.descripcion,
                           movimiento.precio_compra,
                           movimiento.cantidad_compra,
                           movimiento.fecha_compra,
                           movimiento.ganancias_perdidas,
                           simbolos_dict[movimiento.simbolo],
                           round(variacion, 2),
                           round(variacion_capital, 2))
        movimientos_cartera_inversion.append(record)

    return render(request, 'cartera_inversion_rendimiento.html', {"movimientos": movimientos_cartera_inversion})


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
                                        # "image",
                                        "description",
                                        "date"])

            # if economic_news_list[i]["image"]:
            #     image = economic_news_list[i]["image"]["thumbnail"]["contentUrl"]
            # else:
            #     image = ''
            record = Economic_News(economic_news_list[i]["_type"],
                                   economic_news_list[i]["name"],
                                   economic_news_list[i]["url"],
                                   # image,
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
    url = f'https://v6.exchangerate-api.com/v6/{ER_API_KEY}/codes'
    response = requests.get(url)
    codes_dict = {}
    codes_dict = response.json()
    codes_list = codes_dict['supported_codes']
    supported_codes = []
    conversion_result = []
    # for key, value in codes_dict['supported_codes'].items():
    #     codes_list.append([key, value])

    if codes_list is not None and bool(codes_list[0]):
        for i in range(0, len(codes_list)):
            Supported_Codes = namedtuple("Supported_Codes",
                                         ["Codigo",
                                          "Descripcion"])

            record = Supported_Codes(codes_list[i][0],
                                     codes_list[i][1])
            supported_codes.append(record)

    if request.method == 'POST':
        base_code = request.POST.get('codes-from')
        target_code = request.POST.get('codes-to')
        if request.POST.get('value-from') != '':
            if float(request.POST.get('value-from')) > 1:
                amount = request.POST.get('value-from')
            else:
                amount = 1
        else:
            return render(request, 'conversor_moneda.html', context={'supported_codes': supported_codes})

        url = f'https://v6.exchangerate-api.com/v6/{ER_API_KEY}/pair/{base_code[:3]}/{target_code[:3]}/{amount}'
        response = requests.get(url)
        pair_response = response.json()
        result = str(pair_response['conversion_result'])

        Result = namedtuple("Result",
                            ["Base",
                             "Target",
                             "Amount",
                             "Result"])

        record = Result(base_code,
                        target_code,
                        amount,
                        result)
        conversion_result.append(record)

    return render(request, 'conversor_moneda.html',
                  context={'supported_codes': supported_codes, 'conversion_result': conversion_result})


def tipos_cambio(request):
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


def reportes_ahorro(request):
    gastos = 0
    ingresos = 0
    saldo = 0
    mes = now().month
    anio = now().year
    meses = []
    anios = []

    for x in CarteraAhorro.objects.filter(user=request.user):
        if x.fecha_movimiento.month not in meses:
            meses.append(x.fecha_movimiento.month)
        if x.fecha_movimiento.year not in anios:
            anios.append(x.fecha_movimiento.year)
    meses.sort(reverse=True)
    anios.sort(reverse=True)

    if request.method == 'POST':
        mes = request.POST.get('meses')
        anio = request.POST.get('anios')

    for movimiento in CarteraAhorro.objects.filter(user=request.user, fecha_movimiento__month=mes,
                                                   fecha_movimiento__year=anio):
        if movimiento.tipo_movimiento.tipo == 'Ingreso':
            ingresos += movimiento.importe
        elif movimiento.tipo_movimiento.tipo == 'Egreso':
            gastos += movimiento.importe

    saldo = ingresos - gastos

    return render(request, 'reportes_ahorro.html',
                  {"ingresos": ingresos, "gastos": gastos, "saldo": saldo, "meses": meses, "anios": anios})


def cotizaciones(request):
    cotizaciones_list = []
    cotizaciones_data = []
    url = "https://yh-finance.p.rapidapi.com/market/get-trending-tickers"
    querystring = {"region": "US"}
    headers = {
        'x-rapidapi-host': "yh-finance.p.rapidapi.com",
        'x-rapidapi-key': "cf6361603dmsh38ad6751ae96265p117746jsne7c72722198b"
    }

    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
        response_dict = {}
        response_dict = response.json()

        print(response_dict["finance"]["result"][0]["quotes"])

        for cotizacion in response_dict["finance"]["result"][0]["quotes"]:
            cotizaciones_list.append(cotizacion)

    except Exception as e:
        response = None
        cotizaciones_list = ''

    if cotizaciones_list is not None and bool(cotizaciones_list[0]):
        for i in range(0, len(cotizaciones_list)):
            Cotizaciones = namedtuple("Cotizaciones",
                                      ["Simbolo",
                                       "Descripcion",
                                       "Precio_Anterior",
                                       "Precio_Actual",
                                       "Variacion",
                                       "Variacion_Porcentual"])

            variacion = round(cotizaciones_list[i]["regularMarketChange"], 2)
            variacion_porcentual = round(cotizaciones_list[i]["regularMarketChangePercent"], 2)
            try:
                name = cotizaciones_list[i]["longName"]
            except Exception:
                name = cotizaciones_list[i]["shortName"]

            record = Cotizaciones(cotizaciones_list[i]["symbol"],
                                  name,
                                  cotizaciones_list[i]["regularMarketPreviousClose"],
                                  cotizaciones_list[i]["regularMarketPrice"],
                                  variacion,
                                  variacion_porcentual)
            cotizaciones_data.append(record)

    return render(request, "cotizaciones.html", {"cotizaciones": cotizaciones_data})


class PresupuestoList(ListView):
    model = Presupuesto

    def post(self, request, *args, **kwargs):

        gastos = 0
        ingresos = 0
        saldo = 0
        meses = []
        anios = []

        for x in Presupuesto.objects.filter(user=request.user):
            if x.mes not in meses:
                meses.append(x.mes)
            if x.anio not in anios:
                anios.append(x.anio)
        meses.sort(reverse=True)
        anios.sort(reverse=True)

        mes = request.POST.get('meses')
        anio = request.POST.get('anios')

        for movimiento in Presupuesto.objects.filter(user=request.user, mes=mes,
                                                     anio=anio):
            if movimiento.tipo_movimiento.tipo == 'Ingreso':
                ingresos += movimiento.importe
            elif movimiento.tipo_movimiento.tipo == 'Egreso':
                gastos += movimiento.importe

        saldo = ingresos - gastos

        object_list = Presupuesto.objects.filter(
            user=self.request.user,
            mes=mes,
            anio=anio
        ).order_by('-tipo_movimiento')

        return render(request, self.template_name,
                      {"object_list": object_list, "meses": meses, "anios": anios, "saldo": saldo})

    def get(self, request, *args, **kwargs):

        gastos = 0
        ingresos = 0
        saldo = 0
        mes = now().month
        anio = now().year
        meses = []
        anios = []

        for x in Presupuesto.objects.filter(user=request.user):
            if x.mes not in meses:
                meses.append(x.mes)
            if x.anio not in anios:
                anios.append(x.anio)
        meses.sort(reverse=True)
        anios.sort(reverse=True)

        for movimiento in Presupuesto.objects.filter(user=request.user, mes=mes,
                                                     anio=anio):
            if movimiento.tipo_movimiento.tipo == 'Ingreso':
                ingresos += movimiento.importe
            elif movimiento.tipo_movimiento.tipo == 'Egreso':
                gastos += movimiento.importe

        saldo = ingresos - gastos

        object_list = Presupuesto.objects.filter(
            user=self.request.user,
            mes=mes,
            anio=anio
        ).order_by('-tipo_movimiento')

        return render(request, self.template_name,
                      {"object_list": object_list, "meses": meses, "anios": anios, "saldo": saldo})


class PresupuestoCreate(CreateView):
    model = Presupuesto
    success_url = reverse_lazy('presupuesto_list')
    fields = ['mes', 'anio', 'tipo_movimiento', 'categoria_movimiento', 'importe']

    def form_valid(self, form):
        form.instance.user = self.request.user
        self.object = form.save()

        return HttpResponseRedirect(self.get_success_url())


class PresupuestoUpdate(UpdateView):
    model = Presupuesto
    success_url = reverse_lazy('presupuesto_list')
    fields = ['mes', 'anio', 'tipo_movimiento', 'categoria_movimiento', 'importe']


class PresupuestoDelete(DeleteView):
    model = Presupuesto
    success_url = reverse_lazy('presupuesto_list')


def download_data(config):
    ts = TimeSeries(key=config["alpha_vantage"]["key"])
    data, meta_data = ts.get_daily_adjusted(config["alpha_vantage"]["symbol"],
                                            outputsize=config["alpha_vantage"]["outputsize"])

    data_date = [date for date in data.keys()]
    data_date.reverse()

    data_close_price = [float(data[date][config["alpha_vantage"]["key_adjusted_close"]]) for date in data.keys()]
    data_close_price.reverse()
    data_close_price = np.array(data_close_price)

    num_data_points = len(data_date)
    display_date_range = "desde " + data_date[0] + " hasta " + data_date[num_data_points - 1]
    print("Número de puntos de datos ", num_data_points, display_date_range)

    return data_date, data_close_price, num_data_points, display_date_range


class Normalizer():
    def __init__(self):
        self.mu = None
        self.sd = None

    def fit_transform(self, x):
        self.mu = np.mean(x, axis=(0), keepdims=True)
        self.sd = np.std(x, axis=(0), keepdims=True)
        normalized_x = (x - self.mu) / self.sd
        return normalized_x

    def inverse_transform(self, x):
        return (x * self.sd) + self.mu


def prepare_data_x(x, window_size):
    # perform windowing
    n_row = x.shape[0] - window_size + 1
    output = np.lib.stride_tricks.as_strided(x, shape=(n_row, window_size), strides=(x.strides[0], x.strides[0]))
    return output[:-1], output[-1]


def prepare_data_y(x, window_size):
    # # perform simple moving average
    # output = np.convolve(x, np.ones(window_size), 'valid') / window_size

    # use the next day as label
    output = x[window_size:]
    return output


class TimeSeriesDataset(Dataset):
    def __init__(self, x, y):
        x = np.expand_dims(x,
                           2)  # in our case, we have only 1 feature, so we need to convert `x` into [batch, sequence, features] for LSTM
        self.x = x.astype(np.float32)
        self.y = y.astype(np.float32)

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):
        return (self.x[idx], self.y[idx])


class LSTMModel(nn.Module):
    def __init__(self, input_size=1, hidden_layer_size=32, num_layers=2, output_size=1, dropout=0.2):
        super().__init__()
        self.hidden_layer_size = hidden_layer_size

        self.linear_1 = nn.Linear(input_size, hidden_layer_size)
        self.relu = nn.ReLU()
        self.lstm = nn.LSTM(hidden_layer_size, hidden_size=self.hidden_layer_size, num_layers=num_layers,
                            batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.linear_2 = nn.Linear(num_layers * hidden_layer_size, output_size)

        self.init_weights()

    def init_weights(self):
        for name, param in self.lstm.named_parameters():
            if 'bias' in name:
                nn.init.constant_(param, 0.0)
            elif 'weight_ih' in name:
                nn.init.kaiming_normal_(param)
            elif 'weight_hh' in name:
                nn.init.orthogonal_(param)

    def forward(self, x):
        batchsize = x.shape[0]

        # layer 1
        x = self.linear_1(x)
        x = self.relu(x)

        # LSTM layer
        lstm_out, (h_n, c_n) = self.lstm(x)

        # reshape output from hidden cell into [batch, features] for `linear_2`
        x = h_n.permute(1, 0, 2).reshape(batchsize, -1)

        # layer 2
        x = self.dropout(x)
        predictions = self.linear_2(x)
        return predictions[:, -1]


def predecir(ticker):
    config = {
        "alpha_vantage": {
            "key": f"{API_KEY}",  # Claim your free API key here: https://www.alphavantage.co/support/#api-key
            "symbol": f"{ticker}",
            "outputsize": "compact",
            "key_adjusted_close": "5. adjusted close",
        },
        "data": {
            "window_size": 20,
            "train_split_size": 0.80,
        },
        "plots": {
            "xticks_interval": 90,  # show a date every 90 days
            "color_actual": "#001f3f",
            "color_train": "#3D9970",
            "color_val": "#0074D9",
            "color_pred_train": "#3D9970",
            "color_pred_val": "#0074D9",
            "color_pred_test": "#FF4136",
        },
        "model": {
            "input_size": 1,  # since we are only using 1 feature, close price
            "num_lstm_layers": 2,
            "lstm_size": 32,
            "dropout": 0.2,
        },
        "training": {
            "device": "cpu",  # "cuda" or "cpu"
            "batch_size": 64,
            "num_epoch": 100,
            "learning_rate": 0.01,
            "scheduler_step_size": 40,
        }
    }

    def run_epoch(dataloader, is_training=False):
        epoch_loss = 0

        if is_training:
            model.train()
        else:
            model.eval()

        for idx, (x, y) in enumerate(dataloader):
            if is_training:
                optimizer.zero_grad()

            batchsize = x.shape[0]

            x = x.to(config["training"]["device"])
            y = y.to(config["training"]["device"])

            out = model(x)
            loss = criterion(out.contiguous(), y.contiguous())

            if is_training:
                loss.backward()
                optimizer.step()

            epoch_loss += (loss.detach().item() / batchsize)

        lr = scheduler.get_last_lr()[0]

        return epoch_loss, lr

    data_date, data_close_price, num_data_points, display_date_range = download_data(config)
    # plot

    fig = figure(figsize=(13, 4), dpi=90)
    fig.patch.set_facecolor((1.0, 1.0, 1.0))
    plt.plot(data_date, data_close_price, color=config["plots"]["color_actual"])
    xticks = [data_date[i] if ((i % config["plots"]["xticks_interval"] == 0 and (num_data_points - i) > config["plots"][
        "xticks_interval"]) or i == num_data_points - 1) else None for i in range(num_data_points)]  # make x ticks nice
    x = np.arange(0, len(xticks))
    plt.xticks(x, xticks, rotation='vertical')
    plt.title("Precios diarios al cierre de " + config["alpha_vantage"]["symbol"] + ", " + display_date_range)
    plt.grid(b=None, which='major', axis='y', linestyle='--')
    # plt.show()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic_one = base64.b64encode(image_png)
    graphic_one = graphic_one.decode('utf-8')
    #

    # normalize
    scaler = Normalizer()
    normalized_data_close_price = scaler.fit_transform(data_close_price)

    data_x, data_x_unseen = prepare_data_x(normalized_data_close_price, window_size=config["data"]["window_size"])
    data_y = prepare_data_y(normalized_data_close_price, window_size=config["data"]["window_size"])

    # split dataset

    split_index = int(data_y.shape[0] * config["data"]["train_split_size"])
    data_x_train = data_x[:split_index]
    data_x_val = data_x[split_index:]
    data_y_train = data_y[:split_index]
    data_y_val = data_y[split_index:]

    # prepare data for plotting

    to_plot_data_y_train = np.zeros(num_data_points)
    to_plot_data_y_val = np.zeros(num_data_points)

    to_plot_data_y_train[
    config["data"]["window_size"]:split_index + config["data"]["window_size"]] = scaler.inverse_transform(data_y_train)
    to_plot_data_y_val[split_index + config["data"]["window_size"]:] = scaler.inverse_transform(data_y_val)

    to_plot_data_y_train = np.where(to_plot_data_y_train == 0, None, to_plot_data_y_train)
    to_plot_data_y_val = np.where(to_plot_data_y_val == 0, None, to_plot_data_y_val)

    ## plots

    fig = figure(figsize=(13, 4), dpi=90)
    fig.patch.set_facecolor((1.0, 1.0, 1.0))
    plt.plot(data_date, to_plot_data_y_train, label="Precios (train)", color=config["plots"]["color_train"])
    plt.plot(data_date, to_plot_data_y_val, label="Precios (validation)", color=config["plots"]["color_val"])
    xticks = [data_date[i] if ((i % config["plots"]["xticks_interval"] == 0 and (num_data_points - i) > config["plots"][
        "xticks_interval"]) or i == num_data_points - 1) else None for i in range(num_data_points)]  # make x ticks nice
    x = np.arange(0, len(xticks))
    plt.xticks(x, xticks, rotation='vertical')
    plt.title("Precios diarios al cierre de " + config["alpha_vantage"][
        "symbol"] + " - mostrando datos de los sets de entrenamiento (train) y validación (validation)")
    plt.grid(b=None, which='major', axis='y', linestyle='--')
    plt.legend()
    # plt.show()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic_two = base64.b64encode(image_png)
    graphic_two = graphic_two.decode('utf-8')
    #

    dataset_train = TimeSeriesDataset(data_x_train, data_y_train)
    dataset_val = TimeSeriesDataset(data_x_val, data_y_val)

    print("Train data shape", dataset_train.x.shape, dataset_train.y.shape)
    print("Validation data shape", dataset_val.x.shape, dataset_val.y.shape)

    train_dataloader = DataLoader(dataset_train, batch_size=config["training"]["batch_size"], shuffle=True)
    val_dataloader = DataLoader(dataset_val, batch_size=config["training"]["batch_size"], shuffle=True)

    model = LSTMModel(input_size=config["model"]["input_size"], hidden_layer_size=config["model"]["lstm_size"],
                      num_layers=config["model"]["num_lstm_layers"], output_size=1, dropout=config["model"]["dropout"])
    model = model.to(config["training"]["device"])

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=config["training"]["learning_rate"], betas=(0.9, 0.98), eps=1e-9)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=config["training"]["scheduler_step_size"], gamma=0.1)

    for epoch in range(config["training"]["num_epoch"]):
        loss_train, lr_train = run_epoch(train_dataloader, is_training=True)
        loss_val, lr_val = run_epoch(val_dataloader)
        scheduler.step()

        print('Epoch[{}/{}] | loss train:{:.6f}, test:{:.6f} | lr:{:.6f}'
              .format(epoch + 1, config["training"]["num_epoch"], loss_train, loss_val, lr_train))

    # here we re-initialize dataloader so the data doesn't shuffled, so we can plot the values by date

    train_dataloader = DataLoader(dataset_train, batch_size=config["training"]["batch_size"], shuffle=False)
    val_dataloader = DataLoader(dataset_val, batch_size=config["training"]["batch_size"], shuffle=False)

    model.eval()

    # predict on the training data, to see how well the model managed to learn and memorize

    predicted_train = np.array([])

    for idx, (x, y) in enumerate(train_dataloader):
        x = x.to(config["training"]["device"])
        out = model(x)
        out = out.cpu().detach().numpy()
        predicted_train = np.concatenate((predicted_train, out))

    # predict on the validation data, to see how the model does

    predicted_val = np.array([])

    for idx, (x, y) in enumerate(val_dataloader):
        x = x.to(config["training"]["device"])
        out = model(x)
        out = out.cpu().detach().numpy()
        predicted_val = np.concatenate((predicted_val, out))

    # prepare data for plotting

    to_plot_data_y_train_pred = np.zeros(num_data_points)
    to_plot_data_y_val_pred = np.zeros(num_data_points)

    to_plot_data_y_train_pred[
    config["data"]["window_size"]:split_index + config["data"]["window_size"]] = scaler.inverse_transform(
        predicted_train)
    to_plot_data_y_val_pred[split_index + config["data"]["window_size"]:] = scaler.inverse_transform(predicted_val)

    to_plot_data_y_train_pred = np.where(to_plot_data_y_train_pred == 0, None, to_plot_data_y_train_pred)
    to_plot_data_y_val_pred = np.where(to_plot_data_y_val_pred == 0, None, to_plot_data_y_val_pred)

    # plots

    fig = figure(figsize=(13, 4), dpi=90)
    fig.patch.set_facecolor((1.0, 1.0, 1.0))
    plt.plot(data_date, data_close_price, label="Precios reales", color=config["plots"]["color_actual"])
    plt.plot(data_date, to_plot_data_y_train_pred, label="Precios predichos (train)",
             color=config["plots"]["color_pred_train"])
    plt.plot(data_date, to_plot_data_y_val_pred, label="Precios predichos (validation)",
             color=config["plots"]["color_pred_val"])
    plt.title("Comparación de precios reales vs. precios predichos por el modelo")
    xticks = [data_date[i] if ((i % config["plots"]["xticks_interval"] == 0 and (num_data_points - i) > config["plots"][
        "xticks_interval"]) or i == num_data_points - 1) else None for i in range(num_data_points)]  # make x ticks nice
    x = np.arange(0, len(xticks))
    plt.xticks(x, xticks, rotation='vertical')
    plt.grid(b=None, which='major', axis='y', linestyle='--')
    plt.legend()
    # plt.show()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic_three = base64.b64encode(image_png)
    graphic_three = graphic_three.decode('utf-8')
    #

    # prepare data for plotting the zoomed in view of the predicted prices (on validation set) vs. actual prices

    to_plot_data_y_val_subset = scaler.inverse_transform(data_y_val)
    to_plot_predicted_val = scaler.inverse_transform(predicted_val)
    to_plot_data_date = data_date[split_index + config["data"]["window_size"]:]

    # plots

    fig = figure(figsize=(13, 4), dpi=90)
    fig.patch.set_facecolor((1.0, 1.0, 1.0))
    plt.plot(to_plot_data_date, to_plot_data_y_val_subset, label="Precios reales",
             color=config["plots"]["color_actual"])
    plt.plot(to_plot_data_date, to_plot_predicted_val, label="Precios predichos (validation)",
             color=config["plots"]["color_pred_val"])
    plt.title("Precios predichos para el set de datos de validación")
    xticks = [to_plot_data_date[i] if ((i % int(config["plots"]["xticks_interval"] / 5) == 0 and (
            len(to_plot_data_date) - i) > config["plots"]["xticks_interval"] / 6) or i == len(
        to_plot_data_date) - 1) else None for i in range(len(to_plot_data_date))]  # make x ticks nice
    xs = np.arange(0, len(xticks))
    plt.xticks(xs, xticks, rotation='vertical')
    plt.grid(b=None, which='major', axis='y', linestyle='--')
    plt.legend()
    # plt.show()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic_four = base64.b64encode(image_png)
    graphic_four = graphic_four.decode('utf-8')
    #

    # predict the closing price of the next trading day

    model.eval()

    x = torch.tensor(data_x_unseen).float().to(config["training"]["device"]).unsqueeze(0).unsqueeze(
        2)  # this is the data type and shape required, [batch, sequence, feature]
    prediction = model(x)
    prediction = prediction.cpu().detach().numpy()

    # prepare plots

    plot_range = 10
    to_plot_data_y_val = np.zeros(plot_range)
    to_plot_data_y_val_pred = np.zeros(plot_range)
    to_plot_data_y_test_pred = np.zeros(plot_range)

    to_plot_data_y_val[:plot_range - 1] = scaler.inverse_transform(data_y_val)[-plot_range + 1:]
    to_plot_data_y_val_pred[:plot_range - 1] = scaler.inverse_transform(predicted_val)[-plot_range + 1:]

    to_plot_data_y_test_pred[plot_range - 1] = scaler.inverse_transform(prediction)

    to_plot_data_y_val = np.where(to_plot_data_y_val == 0, None, to_plot_data_y_val)
    to_plot_data_y_val_pred = np.where(to_plot_data_y_val_pred == 0, None, to_plot_data_y_val_pred)
    to_plot_data_y_test_pred = np.where(to_plot_data_y_test_pred == 0, None, to_plot_data_y_test_pred)

    # plot

    plot_date_test = data_date[-plot_range + 1:]
    plot_date_test.append("mañana")

    fig = figure(figsize=(13, 4), dpi=90)
    fig.patch.set_facecolor((1.0, 1.0, 1.0))
    plt.plot(plot_date_test, to_plot_data_y_val, label="Precios reales", marker=".", markersize=10,
             color=config["plots"]["color_actual"])
    plt.plot(plot_date_test, to_plot_data_y_val_pred, label="Precios predichos por el modelo", marker=".",
             markersize=10,
             color=config["plots"]["color_pred_val"])
    plt.plot(plot_date_test, to_plot_data_y_test_pred, label="Precio predicho para el próximo día", marker=".",
             markersize=20,
             color=config["plots"]["color_pred_test"])
    plt.title("Predicción de precio para el próximo día de mercado")
    plt.grid(b=None, which='major', axis='y', linestyle='--')
    plt.legend()
    # plt.show()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic_five = base64.b64encode(image_png)
    graphic_five = graphic_five.decode('utf-8')
    #

    print("Precio predicho para el próximo día de actividad del mercado:",
          round(to_plot_data_y_test_pred[plot_range - 1], 2),
          round(to_plot_data_y_val[plot_range - 2], 2))

    precio_actual = round(to_plot_data_y_val[plot_range - 2], 2)
    precio_maniana = round(to_plot_data_y_test_pred[plot_range - 1], 2)

    return {'graphic_one': graphic_one,
            'graphic_two': graphic_two,
            'graphic_three': graphic_three,
            'graphic_four': graphic_four,
            'graphic_five': graphic_five,
            'precio_actual': precio_actual,
            'precio_maniana': precio_maniana}
