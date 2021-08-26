from django.http import HttpResponse
from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings


def inicio(request):
    return render(request, "inicio.html")


def login(request):
    return render(request, "login.html")


def contacto(request):
    if request.method=="POST":
        subject = "Contacto IA"
        message = request.POST["mensaje"] + " " + request.POST["email"]
        email_from = settings.EMAIL_HOST_USER
        recipient_list = ["maximiliano.vinzon@usal.edu.ar"]
        send_mail(subject, message, email_from, recipient_list)
        return render(request, "enviado.html")

    return render(request, "contacto.html")