# ORION Backend: Data & ETL Architecture Flow

This document outlines the end-to-end flow of data from raw Excel files to the aggregated metrics displayed on the ORION frontend dashboard. 

---

## 1. Data Sources (Raw Input)
The system receives four core data files, which must be placed in the `orion-backend/data/` directory:
1. **`Product_Master.xlsx`**: Contains item metadata (Group, Department, Class, Style, Color, Size, Season).
2. **`Sales_Data_Annual.xlsx`**: Contains transactional sales data (Date, Store Code, Item Code, Sales Qty, Net Sales, Gross Sales, Discount).
3. **`SOH_Data_Daily_Annual.xlsx`**: Contains Daily Stock on Hand records (Date, Store Code, Item Code, Ending On Hand Quantity).
4. **`Store_Master.xlsx`**: Contains store metadata (Store ID, Address, City, Grade, Size). *(Currently available for future expansion, but not strictly required for the core dashboard metrics).*

---

## 2. The ETL Pipeline (`run_etl.py`)
To process these massive raw files, we created a custom Django Management Command powered by **Pandas** for high-performance data manipulation. 

**Command:** `python manage.py run_etl`
**Location:** `sales/management/commands/run_etl.py`

### ETL Execution Steps:
1. **Extract**: Pandas reads the Excel files into memory as DataFrames.
2. **Transform (Master Index)**: It extracts unique combinations of `(Store Code, Item Code, Date)` from both the Sales data and SOH data to create a comprehensive timeline matrix.
3. **Transform (Item Metadata Join)**: It performs a `Left Join` on the Item Master data using `Item Code` to attach Group, Department, Class, etc.
4. **Transform (Sales Aggregation)**: It groups the raw transactional Sales Data by `(Store Code, Item Code, Date)` and sums up all financial metrics (Net Sales, Gross Sales, Discount Amount, Sales Qty).
5. **Transform (Sales & SOH Join)**: It `Left Joins` the aggregated sales data and the SOH data onto the master timeline matrix. Any missing data points (e.g., a day with stock but zero sales) are filled with `0`s.
6. **Validate**: A safety check ensures that the sum of `Net Sales` in the final matrix perfectly matches the sum of `Net Sales` in the raw data source.
7. **Load**: The entire Pandas DataFrame is converted into Python dictionaries and inserted into the Postgres/SQLite database using Django's highly optimized `bulk_create` method (handling ~219,000 rows in seconds).

---

## 3. Database Layer (`DashboardData` Model)
The ETL pipeline populates the `DashboardData` model. 

**Location:** `sales/models.py`
This model acts as a highly denormalized, single source of truth. It contains pre-calculated fields and metadata, allowing the database to be queried extremely fast by the API without needing complex SQL joins on the fly. 

It is indexed on `['store_code', 'item_code', 'date']` to ensure blazingly fast filter queries.

---

## 4. The API Layer (`views.py` & `serializers.py`)
The ORION frontend communicates with the backend via Django REST Framework APIs. 

**Location:** `sales/views.py`
The primary controller is the `SaleViewSet` which serves two highly optimized custom endpoints:

### A. Filters API (`/api/sales/filters/`)
- Scans the `DashboardData` table to extract all unique `departments` (categories), `store_codes`, and `seasons`.
- Uses a "natural sort" algorithm so that items like "Store 2" appear before "Store 10".
- Returns this data to populate the frontend Dropdown Filters.

### B. Dashboard Metrics API (`/api/sales/dashboard_metrics/`)
- Receives filter query parameters (e.g., `?department=Menswear&season=Winter`) from the frontend.
- Uses Django ORM `aggregate` and `annotate` functions to dynamically sum up the filtered data directly at the database level.
- **Calculations performed backend-side include:**
  - Total Sales, Units, Gross Sales, and Stock.
  - *Total Markdown %*: `(1 - (Net Sales / Gross Sales)) * 100`
  - *Sell-Through %*: `(Units Sold / (Units Sold + Total Stock)) * 100`
  - *Average Unit Price*: `Total Sales / Units Sold`
  - *Net Margin & COGS*.
- It also aggregates a timeline array (`chartData`) for rendering the frontend line/bar charts.

---

## 5. Summary
By offloading all data manipulation to a scheduled **Pandas ETL script** and utilizing **Django ORM Aggregations** at the API level, the ORION Frontend remains completely lightweight. The browser never has to process hundreds of thousands of rows; it simply requests pre-calculated metrics from the backend and renders them instantly.
