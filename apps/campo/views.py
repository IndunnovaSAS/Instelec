"""
Views for field records.
"""
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import HTMXMixin
from .models import RegistroCampo, Evidencia


class RegistroListView(LoginRequiredMixin, HTMXMixin, ListView):
    """List field records."""
    model = RegistroCampo
    template_name = 'campo/lista.html'
    partial_template_name = 'campo/partials/lista_registros.html'
    context_object_name = 'registros'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'actividad__linea',
            'actividad__torre',
            'actividad__tipo_actividad',
            'usuario'
        )

        # Filters
        linea = self.request.GET.get('linea')
        if linea:
            qs = qs.filter(actividad__linea_id=linea)

        sincronizado = self.request.GET.get('sincronizado')
        if sincronizado:
            qs = qs.filter(sincronizado=sincronizado == 'true')

        return qs


class RegistroDetailView(LoginRequiredMixin, HTMXMixin, DetailView):
    """Detail view for a field record."""
    model = RegistroCampo
    template_name = 'campo/detalle.html'
    context_object_name = 'registro'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evidencias_antes'] = self.object.evidencias.filter(tipo='ANTES')
        context['evidencias_durante'] = self.object.evidencias.filter(tipo='DURANTE')
        context['evidencias_despues'] = self.object.evidencias.filter(tipo='DESPUES')
        return context


class EvidenciasView(LoginRequiredMixin, ListView):
    """View for listing evidence photos."""
    model = Evidencia
    template_name = 'campo/evidencias.html'
    context_object_name = 'evidencias'

    def get_queryset(self):
        return Evidencia.objects.filter(
            registro_campo_id=self.kwargs['pk']
        ).order_by('tipo', 'fecha_captura')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['registro'] = RegistroCampo.objects.get(pk=self.kwargs['pk'])
        return context
