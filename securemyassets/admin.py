from django.contrib import admin
from .models import Asset, ProbateGrant, VaultAccess

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'user', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'note', 'user__username')
    date_hierarchy = 'created_at'

@admin.register(ProbateGrant)
class ProbateGrantAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at', 'reviewed_at', 'reviewed_by')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'review_notes')
    date_hierarchy = 'created_at'

@admin.register(VaultAccess)
class VaultAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'granted', 'granted_at')
    list_filter = ('granted',)
    search_fields = ('user__username',)
