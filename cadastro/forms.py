from django import forms
from .models import Cadastro
from django.contrib.auth.forms import AuthenticationForm

class CadastroForm(forms.ModelForm):
    senha = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'}))

    class Meta:
        model = Cadastro
        fields = ['nome', 'email', 'idade', 'senha']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'idade': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Idade'}),
        }

class UserLoginForm(AuthenticationForm):
    class Meta:
        model = Cadastro
        fields = ['nome', 'senha']
