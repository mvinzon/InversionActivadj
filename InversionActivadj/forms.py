from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from aplicaciones.main.models import Mensajes, PremiumUser


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=140, required=True, label="Nombre")
    last_name = forms.CharField(max_length=140, required=False, label="Apellido")
    email = forms.EmailField(required=True, label="Email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Repita su contraseña'

        self.fields['password1'].help_text = 'Tu password no puede ser común, sólo números ni contener menos de 8 caracteres.'
        self.fields['password2'].help_text = 'Ingrese el mismo password para su verificación.'

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2',
        )
        help_texts = {
            'username': 'Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.',
        }
        labels = {
            'username': _('Usuario'),
        }


class UpdateProfile(forms.ModelForm):
    username = forms.CharField(required=False, label="Usuario")
    email = forms.EmailField(required=False, label="Email")
    first_name = forms.CharField(required=False, label="Nombre")
    last_name = forms.CharField(required=False, label="Apellido")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_email(self):
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
    #
    #     if email and User.objects.filter(email=email).exclude(username=username).count():
    #         raise forms.ValidationError('This email address is already in use. Please supply a different email address.')
        return email

    def save(self, commit=True):
        user = super(ModelForm, self).save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user


# class MensajesForm(forms.ModelForm):
#     asunto = forms.CharField(required=True, label="Asunto")
#     mensaje = forms.CharField(required=True, label="Mensaje")
#     destinatario = forms.IntegerField(required=True, label="Destinatario")
#
#     class Meta:
#         model = Mensajes
#         fields = ('asunto', 'mensaje', 'destinatario')
#
#     def __init__(self, *args, **kwargs):
#        remitente = kwargs.pop('remitente')
#        super(MensajesForm, self).__init__(*args, **kwargs)
#        self.fields['destinatario'].queryset = PremiumUser.objects.filter(user=remitente)
#        print(self.fields['destinatario'].queryset)