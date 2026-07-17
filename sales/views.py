from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Max, Count, Q
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
            sales=Sum('net_sales'),
            max_date_in_month=Max('date')
        ).order_by('month')
        
        chart_data = []
        cumulative_units = 0
        for item in chart_data_qs:
            month = item['month']
            units = item['units']
            sales = float(item['sales'] or 0)
            max_date = item['max_date_in_month']
            
            cumulative_units += units
            
            month_stock = 0
            if max_date:
                stock_agg = queryset.filter(date=max_date).aggregate(total_stock=Sum('ending_on_hand_qty'))
                month_stock = int(stock_agg['total_stock'] or 0)
                
            sell_thru = (cumulative_units / (cumulative_units + month_stock)) * 100 if (cumulative_units + month_stock) > 0 else 0
            
            chart_data.append({
                'date': month.strftime('%b %Y') if month else '',
                'units': units,
                'sales': sales,
                'sell_thru': round(sell_thru, 2)
            })
        
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

    @action(detail=False, methods=['get'])
    def style_performance(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        
        max_date = queryset.aggregate(max_date=Max('date'))['max_date']
        if not max_date:
            return Response([])
            
        styles_data = queryset.exclude(style='').values('style').annotate(
            launch_date=Max('launch_date'),
            total_stores=Count('store_code', distinct=True),
            total_sales_qty=Sum('sales_qty'),
            gross_revenue=Sum('gross_sales'),
            net_revenue=Sum('net_sales'),
            current_stock=Sum('ending_on_hand_qty', filter=Q(date=max_date)),
            last_sale_date=Max('date', filter=Q(sales_qty__gt=0))
        )
        
        results = []
        for item in styles_data:
            style = item['style']
            launch_date = item['launch_date']
            total_stores = item['total_stores'] or 0
            total_sales_qty = int(item['total_sales_qty'] or 0)
            gross_revenue = float(item['gross_revenue'] or 0)
            net_revenue = float(item['net_revenue'] or 0)
            current_stock = int(item['current_stock'] or 0)
            last_sale_date = item['last_sale_date']
            
            total_buy_qty = total_sales_qty + current_stock
            sell_thru_pct = (total_sales_qty / total_buy_qty * 100) if total_buy_qty > 0 else 0
            
            markdown_dollar = gross_revenue - net_revenue
            markdown_pct = (markdown_dollar / gross_revenue * 100) if gross_revenue > 0 else 0
            
            asp = (net_revenue / total_sales_qty) if total_sales_qty > 0 else 0
            
            weeks_since_last_sale = 0
            if last_sale_date:
                days_diff = (max_date - last_sale_date).days
                weeks_since_last_sale = max(0, days_diff / 7.0)
            
            ros_weeks = 0
            weeks_since_launch = 1
            if launch_date:
                days_since_launch = (max_date - launch_date).days
                weeks_since_launch = max(1, days_since_launch / 7.0)
                ros_weeks = total_sales_qty / weeks_since_launch
                
            sell_thru_per_week = sell_thru_pct / weeks_since_launch
                
            results.append({
                'style': style,
                'launch_date': launch_date.strftime('%Y-%m-%d') if launch_date else None,
                'total_stores': total_stores,
                'total_sales': total_sales_qty,
                'total_buy_qty': total_buy_qty,
                'sell_thru_pct': round(sell_thru_pct, 2),
                'sell_thru_per_week': round(sell_thru_per_week, 2),
                'weeks_since_launch': round(weeks_since_launch, 1),
                'ros_weeks': round(ros_weeks, 2),
                'gross_revenue': round(gross_revenue, 2),
                'net_revenue': round(net_revenue, 2),
                'markdown_dollar': round(markdown_dollar, 2),
                'markdown_pct': round(markdown_pct, 2),
                'asp': round(asp, 2),
                'weeks_since_last_sale': round(weeks_since_last_sale, 1)
            })
            
        return Response(results)
