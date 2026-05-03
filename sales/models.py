from django.db import models
class DashboardData(models.Model):
    date = models.DateField()
    store_code = models.CharField(max_length=255)
    item_code = models.CharField(max_length=255)
    group = models.CharField(max_length=255, null=True, blank=True)
    department = models.CharField(max_length=255, null=True, blank=True)
    item_class = models.CharField(max_length=255, null=True, blank=True)
    style = models.CharField(max_length=255, null=True, blank=True)
    color = models.CharField(max_length=255, null=True, blank=True)
    size = models.CharField(max_length=255, null=True, blank=True)
    season = models.CharField(max_length=255, null=True, blank=True)
    sales_qty = models.IntegerField(default=0)
    net_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    gross_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    ending_on_hand_qty = models.IntegerField(default=0)

    class Meta:
        db_table = 'dashboard_data'
        indexes = [
            models.Index(fields=['store_code', 'item_code', 'date']),
        ]

    def __str__(self):
        return f"{self.store_code} - {self.item_code} - {self.date}"
