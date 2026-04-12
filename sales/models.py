from django.db import models

class Sale(models.Model):
    category = models.CharField(max_length=255)
    subcategory = models.CharField(max_length=255)
    item = models.CharField(max_length=255)
    store = models.CharField(max_length=255)
    week = models.CharField(max_length=50)
    season = models.CharField(max_length=100)
    units_sold = models.IntegerField(default=0)
    gross_selling_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    net_sales_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    markdown_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, db_column='markdown_percent')
    ending_stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.item} - {self.week}"

    class Meta:
        db_table = 'sales_data'
