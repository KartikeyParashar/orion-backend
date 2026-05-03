import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from sales.models import DashboardData

class Command(BaseCommand):
    help = 'Runs the ETL pipeline to process Excel data and load it into DashboardData'

    def handle(self, *args, **options):
        # Setup File Paths (Using the new data folder we just created)
        base_dir = settings.BASE_DIR
        data_dir = os.path.join(base_dir, 'data')
        
        item_master_path = os.path.join(data_dir, 'Product_Master.xlsx')
        sales_data_path = os.path.join(data_dir, 'Sales_Data_Annual.xlsx')
        soh_data_path = os.path.join(data_dir, 'SOH_Data_Daily_Annual.xlsx')
        
        self.stdout.write("Step 0: Loading files into memory...")
        try:
            item_master = pd.read_excel(item_master_path)
            sales_data = pd.read_excel(sales_data_path)
            soh_data = pd.read_excel(soh_data_path)
        except FileNotFoundError as e:
            self.stderr.write(f"Error: {e}. Please ensure files are in the data directory.")
            return

        self.stdout.write("Step 1: Transforming data (Extracting unique combinations)...")
        # Ensure we have consistent column names
        # Based on your prompt, we use specific column names. 
        # If your actual files have slightly different names, we may need to adjust these.
        
        # We assume Sales Data has: 'Store Code', 'Item Code', 'Date'
        sales_unique = sales_data[['Store Code', 'Item Code', 'Date']].drop_duplicates()
        soh_unique = soh_data[['Store Code', 'Item Code', 'Date']].drop_duplicates()
        master_data = pd.concat([sales_unique, soh_unique]).drop_duplicates()

        self.stdout.write("Step 2: Left join Item Master...")
        cols_to_join = ['Item Code', 'Group', 'Department', 'Class', 'Style', 'Color', 'Size', 'Season']
        # If 'Item Code' has trailing spaces in excel, strip it
        master_data['Item Code'] = master_data['Item Code'].astype(str).str.strip()
        item_master['Item Code'] = item_master['Item Code'].astype(str).str.strip()
        
        master_data = pd.merge(master_data, item_master[cols_to_join], on='Item Code', how='left')

        self.stdout.write("Step 3: Aggregating Sales data...")
        sales_agg = sales_data.groupby(['Store Code', 'Item Code', 'Date']) \
                              [['Net Sales', 'Gross Sales', 'Discount Amount', 'Sales Qty']].sum().reset_index()

        self.stdout.write("Step 4: Left join aggregated sales...")
        master_data = pd.merge(master_data, sales_agg, on=['Store Code', 'Item Code', 'Date'], how='left')

        self.stdout.write("Step 5: Left join SOH data...")
        master_data = pd.merge(master_data, soh_data[['Store Code', 'Item Code', 'Date', 'Ending On Hand Quantity']], 
                               on=['Store Code', 'Item Code', 'Date'], how='left')

        # Clean up NaNs (Days with stock but no sales, or sales but no closing stock)
        master_data.fillna({
            'Sales Qty': 0, 'Net Sales': 0, 'Gross Sales': 0, 
            'Discount Amount': 0, 'Ending On Hand Quantity': 0
        }, inplace=True)

        self.stdout.write("Step 6: Running Validation checks...")
        sales_sum_original = round(sales_data['Net Sales'].sum(), 2)
        sales_sum_master = round(master_data['Net Sales'].sum(), 2)
        if sales_sum_original != sales_sum_master:
            self.stderr.write(f"Warning: Net Sales mismatch! Original: {sales_sum_original}, Master: {sales_sum_master}")
        else:
            self.stdout.write(self.style.SUCCESS("Validation passed: Net Sales sums match!"))

        self.stdout.write("Step 7: Loading data into Django Database...")
        
        # Clear old dashboard data
        DashboardData.objects.all().delete()
        
        # Convert DataFrame to list of dictionaries
        records = master_data.to_dict('records')
        instances = []
        
        for row in records:
            instances.append(DashboardData(
                date=row['Date'],
                store_code=row['Store Code'],
                item_code=row['Item Code'],
                group=row.get('Group'),
                department=row.get('Department'),
                item_class=row.get('Class'),
                style=row.get('Style'),
                color=row.get('Color'),
                size=row.get('Size'),
                season=row.get('Season'),
                sales_qty=row['Sales Qty'],
                net_sales=row['Net Sales'],
                gross_sales=row['Gross Sales'],
                discount=row['Discount Amount'],
                ending_on_hand_qty=row['Ending On Hand Quantity']
            ))

        # Use bulk_create for massive speed improvements
        DashboardData.objects.bulk_create(instances, batch_size=5000)
        
        self.stdout.write(self.style.SUCCESS(f"ETL Process Complete! Inserted {len(instances)} rows into DashboardData."))
