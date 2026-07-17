import os
import django
import csv
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from sales.models import DashboardData

def load_data():
    DashboardData.objects.all().delete()
    with open('sample_sales.csv', 'r') as f:
        reader = csv.DictReader(f)
        instances = []
        for row in reader:
            instances.append(DashboardData(
                date=datetime.now().date(),  # Using today since CSV has 'Week' instead of 'Date'
                store_code=row['Store'],
                item_code=row['Item'],
                group=row['Category'],
                department=row['Subcategory'],
                item_class='',
                style='',
                color='',
                size='',
                season=row['Season'],
                sales_qty=int(row['Units Sold']),
                net_sales=float(row['Net Sales Price']),
                gross_sales=float(row['Gross Selling Price']),
                discount=float(row['Gross Selling Price']) - float(row['Net Sales Price']),
                ending_on_hand_qty=int(row['Ending Stock']),
                launch_date=None
            ))
        DashboardData.objects.bulk_create(instances)
        print(f"Successfully loaded {len(instances)} records into SQLite!")

if __name__ == '__main__':
    load_data()
