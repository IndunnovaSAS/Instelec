"""
Views for field records.
"""
from typing import Any

from django.db.models import QuerySet
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from apps.core.mixins import HTMXMixin, RoleRequiredMixin
from .models import RegistroCampo, Evidencia


class RegistroListView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, ListView):
    """List field records."""
    model = RegistroCampo
    template_name = 'campo/lista.html'
    partial_template_name = 'campo/partials/lista_registros.html'
    context_object_name = 'registros'
    paginate_by = 20
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'supervisor', 'liniero']

    def get_queryset(self) -> QuerySet[RegistroCampo]:
        qs = super().get_queryset().select_related(
            'actividad',
            'actividad__linea',
            'actividad__torre',
            'actividad__tipo_actividad',
            'usuario'
        ).prefetch_related('evidencias')

        # Filters
        linea = self.request.GET.get('linea')
        if linea:
            from uuid import UUID
            try:
                UUID(linea)
                qs = qs.filter(actividad__linea_id=linea)
            except ValueError:
                pass  # Invalid UUID, ignore filter

        sincronizado = self.request.GET.get('sincronizado')
        if sincronizado:
            qs = qs.filter(sincronizado=sincronizado == 'true')

        return qs


class RegistroDetailView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, DetailView):
    """Detail view for a field record."""
    model = RegistroCampo
    template_name = 'campo/detalle.html'
    context_object_name = 'registro'
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'supervisor', 'liniero']

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['evidencias_antes'] = self.object.evidencias.filter(tipo='ANTES')
        context['evidencias_durante'] = self.object.evidencias.filter(tipo='DURANTE')
        context['evidencias_despues'] = self.object.evidencias.filter(tipo='DESPUES')
        return context


class EvidenciasView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """View for listing evidence photos."""
    model = Evidencia
    template_name = 'campo/evidencias.html'
    context_object_name = 'evidencias'
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'supervisor', 'liniero']

    def get_queryset(self) -> QuerySet[Evidencia]:
        return Evidencia.objects.filter(
            registro_campo_id=self.kwargs['pk']
        ).order_by('tipo', 'fecha_captura')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['registro'] = RegistroCampo.objects.get(pk=self.kwargs['pk'])
        return context


class RegistroCreateView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, TemplateView):
    """View for creating a new field record."""
    template_name = 'campo/crear.html'
    partial_template_name = 'campo/partials/form_registro.html'
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'supervisor', 'liniero']

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        from apps.actividades.models import Actividad
        from apps.lineas.models import Linea

        # Get activities that can have records (not completed/cancelled)
        context['actividades'] = Actividad.objects.filter(
            estado__in=['PENDIENTE', 'PROGRAMADA', 'EN_CURSO']
        ).select_related('linea', 'torre', 'tipo_actividad')
        context['lineas'] = Linea.objects.filter(activa=True)

        # Pre-select activity if passed in URL
        actividad_id = self.request.GET.get('actividad')
        if actividad_id:
            context['actividad_seleccionada'] = actividad_id

        return context

    def post(self, request, *args, **kwargs):
        from django.http import HttpResponseRedirect
        from apps.actividades.models import Actividad

        actividad_id = request.POST.get('actividad')
        observaciones = request.POST.get('observaciones', '')

        try:
            actividad = Actividad.objects.get(pk=actividad_id)

            registro = RegistroCampo.objects.create(
                actividad=actividad,
                usuario=request.user,
                fecha_inicio=timezone.now(),
                observaciones=observaciones,
                sincronizado=True,
                fecha_sincronizacion=timezone.now()
            )

            # Update activity status to EN_CURSO if it was PENDIENTE
            if actividad.estado == 'PENDIENTE':
                actividad.estado = 'EN_CURSO'
                actividad.save(update_fields=['estado', 'updated_at'])

            return HttpResponseRedirect(reverse_lazy('campo:detalle', kwargs={'pk': registro.pk}))
        except Actividad.DoesNotExist:
            context = self.get_context_data(**kwargs)
            context['error'] = 'Actividad no encontrada'
            return self.render_to_response(context)
