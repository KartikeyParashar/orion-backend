from django.contrib import admin
from .models import Sale

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('item', 'category', 'store', 'week', 'units_sold', 'net_sales_price')
    list_filter = ('category', 'store', 'season', 'week')
    search_fields = ('item', 'category', 'subcategory')
    ordering = ('-week',)
