from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Max
from django.db.models.functions import TruncMonth
from django_filters.rest_framework import DjangoFilterBackend
from .models import DashboardData
from .serializers import DashboardDataSerializer

class SaleViewSet(viewsets.ModelViewSet):
    queryset = DashboardData.objects.all()
    serializer_class = DashboardDataSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group', 'department', 'item_class', 'item_code', 'store_code', 'date', 'season']

    @action(detail=False, methods=['get'])
    def filters(self, request):
        categories = self.queryset.exclude(department__isnull=True).values_list('department', flat=True).distinct()
        stores = self.queryset.exclude(store_code__isnull=True).values_list('store_code', flat=True).distinct()
        seasons = self.queryset.exclude(season__isnull=True).values_list('season', flat=True).distinct()
        
        import re
        def natural_sort_key(s):
            return [int(text) if text.isdigit() else str(text).lower() for text in re.split(r'(\d+)', str(s))]

        return Response({
            'categories': sorted(list(categories), key=natural_sort_key),
            'stores': sorted(list(stores), key=natural_sort_key),
            'seasons': sorted(list(seasons), key=natural_sort_key)
        })

    @action(detail=False, methods=['get'])
    def dashboard_metrics(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        
        aggregates = queryset.aggregate(
            total_sales=Sum('net_sales'),
            total_units=Sum('sales_qty'),
            total_gross_sales=Sum('gross_sales')
        )
        
        total_sales = float(aggregates['total_sales'] or 0)
        total_units = int(aggregates['total_units'] or 0)
        total_gross_sales = float(aggregates['total_gross_sales'] or 0)
        
        max_date = queryset.aggregate(max_date=Max('date'))['max_date']
        total_stock = 0
        if max_date:
            total_stock_agg = queryset.filter(date=max_date).aggregate(total_stock=Sum('ending_on_hand_qty'))
            total_stock = int(total_stock_agg['total_stock'] or 0)
        
        total_markdown = (1 - (total_sales / total_gross_sales)) * 100 if total_gross_sales > 0 else 0
        sell_thru = (total_units / (total_units + total_stock)) * 100 if (total_units + total_stock) > 0 else 0
        avg_unit_price = total_sales / total_units if total_units > 0 else 0
        total_cogs = total_sales * 0.65
        net_margin = total_sales - total_cogs
        net_margin_percent = (net_margin / total_sales) * 100 if total_sales > 0 else 0
        
        chart_data_qs = queryset.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            units=Sum('sales_qty'),
            sales=Sum('net_sales')
        ).order_by('month')
        
        chart_data = [{
            'date': item['month'].strftime('%b %Y') if item['month'] else '',
            'units': item['units'],
            'sales': float(item['sales'] or 0)
        } for item in chart_data_qs]
        
        # Calculate active categories for insight
        unique_categories_count = queryset.values('department').distinct().count()

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
