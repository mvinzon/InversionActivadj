from django.contrib.auth import authenticate, login
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

from .forms import SignUpForm, UpdateProfile
from django.views.generic import CreateView


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
    return render(request, 'asesoria.html')