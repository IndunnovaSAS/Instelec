"""
Core views.
"""
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(LoginRequiredMixin, TemplateView):
    """Home page / Dashboard."""
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Add dashboard data based on user role
        if user.rol in ['admin', 'director', 'coordinador']:
            context['show_full_dashboard'] = True
        else:
            context['show_full_dashboard'] = False

        return context


def health_check(request):
    """Health check endpoint for Cloud Run."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'transmaint',
    })
