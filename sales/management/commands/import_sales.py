import csv
from django.core.management.base import BaseCommand
from sales.models import Sale
from decimal import Decimal

class Command(BaseCommand):
    help = 'Imports sales data from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file')

    def handle(self, *args, **options):
        file_path = options['csv_file']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                sales_to_create = []
                
                for row in reader:
                    sale = Sale(
                        category=row.get('Category', ''),
                        subcategory=row.get('Subcategory', ''),
                        item=row.get('Item', ''),
                        store=row.get('Store', ''),
                        week=row.get('Week', ''),
                        season=row.get('Season', ''),
                        units_sold=int(row.get('Units Sold', 0) or 0),
                        gross_selling_price=Decimal(row.get('Gross Selling Price', 0.00) or 0.00),
                        net_sales_price=Decimal(row.get('Net Sales Price', 0.00) or 0.00),
                        markdown_percentage=Decimal(row.get('Markdown %', 0.00) or 0.00),
                        ending_stock=int(row.get('Ending Stock', 0) or 0)
                    )
                    sales_to_create.append(sale)
                
                Sale.objects.bulk_create(sales_to_create)
                self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(sales_to_create)} records'))
                
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File "{file_path}" not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
