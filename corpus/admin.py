""" Admin configuration for the Word model. """

from django.contrib import admin

from .loader import clear_engine
from .models import Word


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ("text", "normalized_text", "weight", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("text", "normalized_text")
    ordering = ("normalized_text",)
    actions = ("deactivate_selected", "activate_selected")

    def delete_queryset(self, request, queryset):
        # QuerySet.delete() bypasses post_delete signals; invalidate explicitly.
        queryset.delete()
        clear_engine()

    @admin.action(description="Mark selected words inactive")
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} word(s).")

    @admin.action(description="Mark selected words active")
    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} word(s).")
