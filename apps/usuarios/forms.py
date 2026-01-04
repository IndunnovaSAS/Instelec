"""
User forms.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm

from .models import Usuario


class LoginForm(AuthenticationForm):
    """Custom login form."""
    username = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-input w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'correo@ejemplo.com',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '••••••••',
        })
    )

    error_messages = {
        'invalid_login': 'Correo electrónico o contraseña incorrectos.',
        'inactive': 'Esta cuenta está inactiva.',
    }


class PerfilForm(forms.ModelForm):
    """Form for editing user profile."""

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'telefono', 'foto']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2 border rounded-lg'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2 border rounded-lg'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2 border rounded-lg'
            }),
        }


class UsuarioCreationForm(UserCreationForm):
    """Form for creating new users."""

    class Meta:
        model = Usuario
        fields = ('email', 'first_name', 'last_name', 'rol')


class UsuarioChangeForm(UserChangeForm):
    """Form for updating users."""

    class Meta:
        model = Usuario
        fields = ('email', 'first_name', 'last_name', 'rol', 'telefono', 'documento', 'cargo')
