from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from .models import Sale
from .serializers import SaleSerializer

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'subcategory', 'item', 'store', 'week', 'season']

    @action(detail=False, methods=['get'])
    def filters(self, request):
        categories = self.queryset.values_list('category', flat=True).distinct()
        stores = self.queryset.values_list('store', flat=True).distinct()
        seasons = self.queryset.values_list('season', flat=True).distinct()
        import re
        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

        return Response({
            'categories': sorted(list(categories), key=natural_sort_key),
            'stores': sorted(list(stores), key=natural_sort_key),
            'seasons': sorted(list(seasons), key=natural_sort_key)
        })

    @action(detail=False, methods=['get'])
    def dashboard_metrics(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        
        aggregates = queryset.aggregate(
            total_sales=Sum('net_sales_price'),
            total_units=Sum('units_sold'),
            total_gross_sales=Sum('gross_selling_price'),
            total_stock=Sum('ending_stock')
        )
        
        total_sales = float(aggregates['total_sales'] or 0)
        total_units = int(aggregates['total_units'] or 0)
        total_gross_sales = float(aggregates['total_gross_sales'] or 0)
        total_stock = int(aggregates['total_stock'] or 0)
        
        total_markdown = (1 - (total_sales / total_gross_sales)) * 100 if total_gross_sales > 0 else 0
        sell_thru = (total_units / (total_units + total_stock)) * 100 if (total_units + total_stock) > 0 else 0
        avg_unit_price = total_sales / total_units if total_units > 0 else 0
        total_cogs = total_sales * 0.65
        net_margin = total_sales - total_cogs
        net_margin_percent = (net_margin / total_sales) * 100 if total_sales > 0 else 0
        
        chart_data_qs = queryset.values('week').annotate(
            units=Sum('units_sold'),
            sales=Sum('net_sales_price')
        ).order_by('week')
        
        chart_data = [{
            'date': item['week'],
            'units': item['units'],
            'sales': float(item['sales'] or 0)
        } for item in chart_data_qs]
        
        chart_data.sort(key=lambda x: int(x['date']))
        
        # Calculate active categories for insight
        unique_categories_count = queryset.values('category').distinct().count()

        return Response({
            'totalSales': total_sales,
            'totalUnits': total_units,
            'totalGrossSales': total_gross_sales,
            'totalMarkdown': total_markdown,
            'avgUnitPrice': avg_unit_price,
            'totalStock': total_stock,
            'sellThru': sell_thru,
            'totalCogs': total_cogs,
            'netMargin': net_margin,
            'netMarginPercent': net_margin_percent,
            'chartData': chart_data,
            'activeCategories': unique_categories_count
        })
