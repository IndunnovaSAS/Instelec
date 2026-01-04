"""
Core admin configuration.
"""
from django.contrib import admin


class BaseModelAdmin(admin.ModelAdmin):
    """Base admin class with common configuration."""
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 25
    date_hierarchy = 'created_at'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields
        return ('id', 'created_at', 'updated_at')
