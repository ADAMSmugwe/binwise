from django.contrib import admin
from .models import WasteItem

# Register your models here.
@admin.register(WasteItem)
class WasteItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'rule_key', 'category', 'waste_bin', 'confidence','explanation', 'created_at']
    list_filter = ['category', 'waste_bin']