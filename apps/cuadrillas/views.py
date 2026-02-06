"""
Views for crew management.
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from apps.core.mixins import HTMXMixin, RoleRequiredMixin
from .models import Cuadrilla, Vehiculo, TrackingUbicacion


class CuadrillaListView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, ListView):
    """List all crews."""
    model = Cuadrilla
    template_name = 'cuadrillas/lista.html'
    partial_template_name = 'cuadrillas/partials/lista_cuadrillas.html'
    context_object_name = 'cuadrillas'
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'supervisor']

    def get_queryset(self):
        return Cuadrilla.objects.filter(activa=True).select_related(
            'supervisor', 'vehiculo', 'linea_asignada'
        ).prefetch_related('miembros__usuario')

    def get_context_data(self, **kwargs):
        import json
        context = super().get_context_data(**kwargs)

        # Get latest location for each active crew for the mini-map
        ubicaciones = []
        for cuadrilla in context['cuadrillas']:
            ultima = TrackingUbicacion.objects.filter(
                cuadrilla=cuadrilla
            ).order_by('-created_at').first()

            if ultima:
                ubicaciones.append({
                    'cuadrilla_id': str(cuadrilla.id),
                    'cuadrilla_codigo': cuadrilla.codigo,
                    'lat': float(ultima.latitud),
                    'lng': float(ultima.longitud),
                })

        context['cuadrillas_ubicaciones_json'] = json.dumps(ubicaciones)
        return context


class CuadrillaDetailView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, DetailView):
    """Detail view for a crew."""
    model = Cuadrilla
    template_name = 'cuadrillas/detalle.html'
    context_object_name = 'cuadrilla'
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'supervisor']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['miembros'] = self.object.miembros.filter(activo=True).select_related('usuario')

        # Last known location
        ultima_ubicacion = TrackingUbicacion.objects.filter(
            cuadrilla=self.object
        ).order_by('-created_at').first()
        context['ultima_ubicacion'] = ultima_ubicacion

        return context


class CuadrillaEditView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, DetailView):
    """View for editing a crew."""
    model = Cuadrilla
    template_name = 'cuadrillas/editar.html'
    context_object_name = 'cuadrilla'
    allowed_roles = ['admin', 'director', 'coordinador']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.usuarios.models import Usuario
        from apps.lineas.models import Linea
        context['supervisores'] = Usuario.objects.filter(rol='supervisor', is_active=True)
        context['lineas'] = Linea.objects.filter(activa=True)
        context['vehiculos'] = Vehiculo.objects.filter(activo=True)
        return context

    def post(self, request, *args, **kwargs):
        """Handle form submission to update a crew."""
        from apps.usuarios.models import Usuario
        from apps.lineas.models import Linea

        cuadrilla = self.get_object()

        codigo = request.POST.get('codigo', '').strip()
        nombre = request.POST.get('nombre', '').strip()

        if not codigo or not nombre:
            messages.error(request, 'Código y nombre son obligatorios.')
            return self.get(request, *args, **kwargs)

        if Cuadrilla.objects.filter(codigo=codigo).exclude(pk=cuadrilla.pk).exists():
            messages.error(request, f'Ya existe otra cuadrilla con el código {codigo}.')
            return self.get(request, *args, **kwargs)

        try:
            cuadrilla.codigo = codigo
            cuadrilla.nombre = nombre

            supervisor_id = request.POST.get('supervisor') or None
            cuadrilla.supervisor = Usuario.objects.get(pk=supervisor_id) if supervisor_id else None

            vehiculo_id = request.POST.get('vehiculo') or None
            cuadrilla.vehiculo = Vehiculo.objects.get(pk=vehiculo_id) if vehiculo_id else None

            linea_id = request.POST.get('linea_asignada') or None
            cuadrilla.linea_asignada = Linea.objects.get(pk=linea_id) if linea_id else None

            cuadrilla.activa = request.POST.get('activa') == 'on'
            cuadrilla.observaciones = request.POST.get('observaciones', '').strip()
            cuadrilla.save()
            messages.success(request, f'Cuadrilla {cuadrilla.codigo} actualizada exitosamente.')
            return redirect('cuadrillas:detalle', pk=cuadrilla.pk)
        except (Usuario.DoesNotExist, Linea.DoesNotExist, Vehiculo.DoesNotExist) as e:
            messages.error(request, f'Referencia inválida: {str(e)}')
            return self.get(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f'Error al actualizar la cuadrilla: {str(e)}')
            return self.get(request, *args, **kwargs)


class MapaCuadrillasView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """Real-time map of all crews."""
    template_name = 'cuadrillas/mapa.html'
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'supervisor']


class MapaCuadrillasPartialView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """Partial view for HTMX polling of crew locations."""
    template_name = 'cuadrillas/partials/mapa_cuadrillas.html'
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'supervisor']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get latest location for each active crew
        cuadrillas = Cuadrilla.objects.filter(activa=True)
        ubicaciones = []

        for cuadrilla in cuadrillas:
            ultima = TrackingUbicacion.objects.filter(
                cuadrilla=cuadrilla
            ).order_by('-created_at').first()

            if ultima:
                ubicaciones.append({
                    'cuadrilla_id': str(cuadrilla.id),
                    'cuadrilla_codigo': cuadrilla.codigo,
                    'cuadrilla_nombre': cuadrilla.nombre,
                    'lat': float(ultima.latitud),
                    'lng': float(ultima.longitud),
                    'precision': float(ultima.precision_metros) if ultima.precision_metros else None,
                    'timestamp': ultima.created_at.isoformat(),
                })

        context['ubicaciones'] = ubicaciones
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('Accept') == 'application/json':
            return JsonResponse({'ubicaciones': context['ubicaciones']})
        return super().render_to_response(context, **response_kwargs)


class CuadrillaCreateView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, TemplateView):
    """View for creating a new crew."""
    template_name = 'cuadrillas/crear.html'
    partial_template_name = 'cuadrillas/partials/form_cuadrilla.html'
    allowed_roles = ['admin', 'director', 'coordinador']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.usuarios.models import Usuario
        from apps.lineas.models import Linea
        context['supervisores'] = Usuario.objects.filter(rol='supervisor', is_active=True)
        context['lineas'] = Linea.objects.filter(activa=True)
        return context

    def post(self, request, *args, **kwargs):
        """Handle form submission to create a new crew."""
        from django.shortcuts import redirect
        from django.contrib import messages
        from apps.usuarios.models import Usuario
        from apps.lineas.models import Linea

        codigo = request.POST.get('codigo', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        supervisor_id = request.POST.get('supervisor') or None
        linea_id = request.POST.get('linea_asignada') or None

        # Validation
        if not codigo or not nombre:
            messages.error(request, 'Código y nombre son obligatorios.')
            return self.get(request, *args, **kwargs)

        if Cuadrilla.objects.filter(codigo=codigo).exists():
            messages.error(request, f'Ya existe una cuadrilla con el código {codigo}.')
            return self.get(request, *args, **kwargs)

        # Get related objects
        supervisor = None
        if supervisor_id:
            try:
                supervisor = Usuario.objects.get(pk=supervisor_id)
            except Usuario.DoesNotExist:
                pass

        linea_asignada = None
        if linea_id:
            try:
                linea_asignada = Linea.objects.get(pk=linea_id)
            except Linea.DoesNotExist:
                pass

        # Create the crew
        try:
            cuadrilla = Cuadrilla.objects.create(
                codigo=codigo,
                nombre=nombre,
                supervisor=supervisor,
                linea_asignada=linea_asignada,
            )
            messages.success(request, f'Cuadrilla {cuadrilla.codigo} creada exitosamente.')
            return redirect('cuadrillas:detalle', pk=cuadrilla.pk)
        except Exception as e:
            messages.error(request, f'Error al crear la cuadrilla: {str(e)}')
            return self.get(request, *args, **kwargs)
