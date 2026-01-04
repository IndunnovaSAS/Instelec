"""
User views.
"""
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect

from .models import Usuario
from .forms import LoginForm, PerfilForm


class CustomLoginView(LoginView):
    """Custom login view."""
    template_name = 'usuarios/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('core:home')


class CustomLogoutView(LogoutView):
    """Custom logout view."""
    next_page = reverse_lazy('usuarios:login')


class PerfilView(LoginRequiredMixin, TemplateView):
    """User profile view."""
    template_name = 'usuarios/perfil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.request.user
        return context


class PerfilEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile."""
    model = Usuario
    form_class = PerfilForm
    template_name = 'usuarios/perfil_edit.html'
    success_url = reverse_lazy('usuarios:perfil')

    def get_object(self):
        return self.request.user
