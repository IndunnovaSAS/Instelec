"""
Views for transmission lines.
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import HTMXMixin, RoleRequiredMixin
from .models import Linea, Torre


class LineaListView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, ListView):
    """List all transmission lines."""
    model = Linea
    template_name = 'lineas/lista.html'
    partial_template_name = 'lineas/partials/lista_lineas.html'
    context_object_name = 'lineas'
    paginate_by = 20
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'ing_ambiental', 'supervisor', 'liniero']

    def get_queryset(self):
        qs = super().get_queryset().filter(activa=True)

        # Filters
        cliente = self.request.GET.get('cliente')
        if cliente:
            qs = qs.filter(cliente=cliente)

        buscar = self.request.GET.get('buscar')
        if buscar:
            qs = qs.filter(nombre__icontains=buscar) | qs.filter(codigo__icontains=buscar)

        return qs.prefetch_related('torres')


class LineaDetailView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, DetailView):
    """Detail view for a transmission line."""
    model = Linea
    template_name = 'lineas/detalle.html'
    partial_template_name = 'lineas/partials/detalle_linea.html'
    context_object_name = 'linea'
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'ing_ambiental', 'supervisor', 'liniero']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['torres'] = self.object.torres.all()[:50]
        context['total_torres'] = self.object.torres.count()
        return context


class LineaEditView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, DetailView):
    """View for editing a transmission line."""
    model = Linea
    template_name = 'lineas/editar.html'
    context_object_name = 'linea'
    allowed_roles = ['admin', 'director', 'coordinador']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Linea.Cliente.choices
        context['contratistas'] = Linea.Contratista.choices
        return context

    def post(self, request, *args, **kwargs):
        """Handle form submission to update a transmission line."""
        linea = self.get_object()

        codigo = request.POST.get('codigo', '').strip()
        nombre = request.POST.get('nombre', '').strip()

        if not codigo or not nombre:
            messages.error(request, 'Código y nombre son obligatorios.')
            return self.get(request, *args, **kwargs)

        # Check unique codigo (excluding current object)
        if Linea.objects.filter(codigo=codigo).exclude(pk=linea.pk).exists():
            messages.error(request, f'Ya existe otra línea con el código {codigo}.')
            return self.get(request, *args, **kwargs)

        try:
            linea.codigo = codigo
            linea.nombre = nombre
            linea.codigo_transelca = request.POST.get('codigo_transelca', '').strip()
            linea.circuito = request.POST.get('circuito', '').strip()
            cliente = request.POST.get('cliente', '').strip()
            linea.cliente = cliente if cliente in dict(Linea.Cliente.choices) else linea.cliente
            contratista = request.POST.get('contratista', '').strip()
            linea.contratista = contratista if contratista in dict(Linea.Contratista.choices) else ''
            linea.centro_emplazamiento = request.POST.get('centro_emplazamiento', '').strip()
            linea.puesto_trabajo = request.POST.get('puesto_trabajo', '').strip()
            tension_kv = request.POST.get('tension_kv') or None
            linea.tension_kv = int(tension_kv) if tension_kv else None
            longitud_km = request.POST.get('longitud_km') or None
            linea.longitud_km = float(longitud_km) if longitud_km else None
            linea.departamento = request.POST.get('departamento', '').strip()
            linea.municipios = request.POST.get('municipios', '').strip()
            linea.activa = request.POST.get('activa') == 'on'
            linea.observaciones = request.POST.get('observaciones', '').strip()
            linea.save()
            messages.success(request, f'Línea {linea.codigo} actualizada exitosamente.')
            return redirect('lineas:detalle', pk=linea.pk)
        except Exception as e:
            messages.error(request, f'Error al actualizar la línea: {str(e)}')
            return self.get(request, *args, **kwargs)


class TorresLineaView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, ListView):
    """List towers for a specific line."""
    model = Torre
    template_name = 'lineas/torres.html'
    partial_template_name = 'lineas/partials/lista_torres.html'
    context_object_name = 'torres'
    paginate_by = 50
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'ing_ambiental', 'supervisor', 'liniero']

    def get_queryset(self):
        return Torre.objects.filter(linea_id=self.kwargs['pk']).order_by('numero')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['linea'] = Linea.objects.get(pk=self.kwargs['pk'])
        return context


class TorreDetailView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, DetailView):
    """Detail view for a tower."""
    model = Torre
    template_name = 'lineas/torre_detalle.html'
    partial_template_name = 'lineas/partials/detalle_torre.html'
    context_object_name = 'torre'
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'ing_ambiental', 'supervisor', 'liniero']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['poligonos'] = self.object.poligonos.all()
        # Get recent activities for this tower
        context['actividades_recientes'] = self.object.actividades.order_by('-fecha_programada')[:5]
        return context


class MapaLineasView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """Map view showing all lines and towers."""
    template_name = 'lineas/mapa.html'
    allowed_roles = ['admin', 'director', 'coordinador', 'ing_residente', 'ing_ambiental', 'supervisor']

    def get_context_data(self, **kwargs):
        import json
        context = super().get_context_data(**kwargs)

        # Check if a specific line is requested
        linea_id = self.request.GET.get('linea')

        if linea_id:
            try:
                from uuid import UUID
                UUID(linea_id)
                linea = Linea.objects.prefetch_related('torres').get(pk=linea_id)
                context['linea'] = linea
                torres = list(linea.torres.all())
                context['torres'] = torres
            except (ValueError, Linea.DoesNotExist):
                linea = None
                torres = []
        else:
            # Get all active lines with their towers
            lineas = Linea.objects.filter(activa=True).prefetch_related('torres')
            context['lineas'] = lineas
            linea = lineas.first() if lineas.exists() else None
            context['linea'] = linea
            torres = list(linea.torres.all()) if linea else []
            context['torres'] = torres

        # Prepare JSON data for the map
        torres_data = []
        lats = []
        lons = []
        for torre in torres:
            if torre.latitud and torre.longitud:
                torres_data.append({
                    'id': str(torre.id),
                    'numero': torre.numero,
                    'linea': linea.codigo if linea else '',
                    'tipo': torre.tipo,
                    'estado': torre.estado,
                    'lat': float(torre.latitud),
                    'lon': float(torre.longitud),
                    'altitud': float(torre.altitud) if torre.altitud else None,
                })
                lats.append(float(torre.latitud))
                lons.append(float(torre.longitud))

        # Convert to JSON string for JavaScript
        context['torres_json'] = json.dumps(torres_data)

        # Calculate center of map
        if lats and lons:
            context['center_lat'] = sum(lats) / len(lats)
            context['center_lon'] = sum(lons) / len(lons)
        else:
            # Default to Colombia center
            context['center_lat'] = 4.5709
            context['center_lon'] = -74.2973

        return context


class LineaCreateView(LoginRequiredMixin, RoleRequiredMixin, HTMXMixin, TemplateView):
    """View for creating a new transmission line."""
    template_name = 'lineas/crear.html'
    partial_template_name = 'lineas/partials/form_linea.html'
    allowed_roles = ['admin', 'director', 'coordinador']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Linea.Cliente.choices
        return context

    def post(self, request, *args, **kwargs):
        """Handle form submission to create a new transmission line."""
        from django.shortcuts import redirect
        from django.contrib import messages

        codigo = request.POST.get('codigo', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        cliente = request.POST.get('cliente', '').strip()
        tension_kv = request.POST.get('voltaje') or None
        longitud_km = request.POST.get('longitud_km') or None
        observaciones = request.POST.get('descripcion', '').strip()

        # Validation
        if not codigo or not nombre:
            messages.error(request, 'Código y nombre son obligatorios.')
            return self.get(request, *args, **kwargs)

        if Linea.objects.filter(codigo=codigo).exists():
            messages.error(request, f'Ya existe una línea con el código {codigo}.')
            return self.get(request, *args, **kwargs)

        # Create the line
        try:
            linea = Linea.objects.create(
                codigo=codigo,
                nombre=nombre,
                cliente=cliente if cliente in dict(Linea.Cliente.choices) else Linea.Cliente.TRANSELCA,
                tension_kv=int(tension_kv) if tension_kv else None,
                longitud_km=float(longitud_km) if longitud_km else None,
                observaciones=observaciones,
            )
            messages.success(request, f'Línea {linea.codigo} creada exitosamente.')
            return redirect('lineas:detalle', pk=linea.pk)
        except Exception as e:
            messages.error(request, f'Error al crear la línea: {str(e)}')
            return self.get(request, *args, **kwargs)
