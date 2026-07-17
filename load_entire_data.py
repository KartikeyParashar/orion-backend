import os
import django
import pandas as pd
import numpy as np

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from sales.models import DashboardData

def load_data():
    print("Loading datasets...")
    sales_df = pd.read_excel(r'C:\Users\Avinash parashar\Desktop\ORION\orion-backend\data\Sales_Data_Annual.xlsx')
    soh_df = pd.read_excel(r'C:\Users\Avinash parashar\Desktop\ORION\orion-backend\data\SOH_Data_Daily_Annual.xlsx')
    product_df = pd.read_excel(r'C:\Users\Avinash parashar\Desktop\ORION\orion-backend\data\Product_Master.xlsx')
    
    print("Processing and merging data...")
    # Convert dates to datetime to ensure consistency
    sales_df['Date'] = pd.to_datetime(sales_df['Date'])
    soh_df['Date'] = pd.to_datetime(soh_df['Date'])
    
    # Aggregate sales data to daily level per store/item to avoid duplicating SOH
    sales_daily = sales_df.groupby(['Date', 'Store Code', 'Item Code'], as_index=False).agg({
        'Sales Qty': 'sum',
        'Net Sales': 'sum',
        'Gross Sales': 'sum',
        'Discount Amount': 'sum'
    })
    
    # Outer join Sales and SOH on Date, Store Code, Item Code
    # This ensures we get all days where either sales happened or stock existed
    merged_df = pd.merge(sales_daily, soh_df, on=['Date', 'Store Code', 'Item Code'], how='outer')
    
    # Merge with Product Master to get categories
    merged_df = pd.merge(merged_df, product_df, on='Item Code', how='left')
    
    # Replace NaN with appropriate defaults
    merged_df['Sales Qty'] = merged_df['Sales Qty'].fillna(0)
    merged_df['Net Sales'] = merged_df['Net Sales'].fillna(0.0)
    merged_df['Gross Sales'] = merged_df['Gross Sales'].fillna(0.0)
    merged_df['Discount Amount'] = merged_df['Discount Amount'].fillna(0.0)
    merged_df['Ending On Hand Quantity'] = merged_df['Ending On Hand Quantity'].fillna(0)
    
    # Fill categorical missing values
    categorical_cols = ['Group', 'Department', 'Class', 'Style', 'Color', 'Size', 'Season']
    for col in categorical_cols:
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].fillna('')
            
    if 'Launch Date' in merged_df.columns:
        merged_df['Launch Date'] = pd.to_datetime(merged_df['Launch Date']).dt.date
    
    print(f"Preparing {len(merged_df)} records for database insertion...")
    
    # Delete existing data
    DashboardData.objects.all().delete()
    
    instances = []
    # Create instances in chunks to avoid memory overload
    for _, row in merged_df.iterrows():
        instances.append(DashboardData(
            date=row['Date'].date(),
            store_code=str(row['Store Code']),
            item_code=str(row['Item Code']),
            group=str(row.get('Group', '')),
            department=str(row.get('Department', '')),
            item_class=str(row.get('Class', '')),
            style=str(row.get('Style', '')),
            color=str(row.get('Color', '')),
            size=str(row.get('Size', '')),
            season=str(row.get('Season', '')),
            sales_qty=int(row['Sales Qty']),
            net_sales=float(row['Net Sales']),
            gross_sales=float(row['Gross Sales']),
            discount=float(row['Discount Amount']),
            ending_on_hand_qty=int(row['Ending On Hand Quantity']),
            launch_date=row['Launch Date'] if pd.notnull(row.get('Launch Date')) else None
        ))
    
    print("Bulk creating records in SQLite...")
    chunk_size = 5000
    for i in range(0, len(instances), chunk_size):
        DashboardData.objects.bulk_create(instances[i:i + chunk_size])
        print(f"Inserted {min(i + chunk_size, len(instances))} of {len(instances)} records...")
        
    print("Successfully loaded all data!")

if __name__ == '__main__':
    load_data()
