from django.contrib import admin
from .models import DashboardData
@admin.register(DashboardData)
class DashboardDataAdmin(admin.ModelAdmin):
    list_display = ('date', 'store_code', 'item_code', 'department', 'sales_qty', 'net_sales')
    list_filter = ('department', 'store_code', 'season', 'date')
    search_fields = ('item_code', 'store_code', 'department', 'group')
    ordering = ('-date',)
