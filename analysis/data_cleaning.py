import pandas as pd
import numpy as np
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================
# CONFIGURATION
# ============================================
DATA_PATH = 'C:/Users/USER/OneDrive/Máy tính/Beauty data'
OUTPUT_PATH = f'{DATA_PATH}/cleaned'

# Ensure output directory exists
if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)
    print(f"✓ Created output directory: {OUTPUT_PATH}")

print("=" * 70)
print("DATA CLEANING PIPELINE - BEAUTY E-COMMERCE")
print("=" * 70)
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================
# STEP 1: Load All Datasets
# ============================================
print("[Step 1/8] Loading datasets...")
print("-" * 70)

try:
    customers = pd.read_csv(f'{DATA_PATH}/olist_customers_dataset.csv')
    print(f"  ✓ Customers: {len(customers):,} rows")
    
    orders = pd.read_csv(f'{DATA_PATH}/olist_orders_dataset.csv')
    print(f"  ✓ Orders: {len(orders):,} rows")
    
    order_items = pd.read_csv(f'{DATA_PATH}/olist_order_items_dataset.csv')
    print(f"  ✓ Order Items: {len(order_items):,} rows")
    
    products = pd.read_csv(f'{DATA_PATH}/olist_products_dataset.csv')
    print(f"  ✓ Products: {len(products):,} rows")
    
    reviews = pd.read_csv(f'{DATA_PATH}/olist_order_reviews_dataset.csv')
    print(f"  ✓ Reviews: {len(reviews):,} rows")
    
    payments = pd.read_csv(f'{DATA_PATH}/olist_order_payments_dataset.csv')
    print(f"  ✓ Payments: {len(payments):,} rows")
    
    category_translation = pd.read_csv(f'{DATA_PATH}/product_category_name_translation.csv')
    print(f"  ✓ Category Translation: {len(category_translation):,} rows")
    
    print("\n✓ All datasets loaded successfully!")
    
except Exception as e:
    print(f"\n❌ Error loading data: {e}")
    print("Please check file paths and try again.")
    exit()

# ============================================
# STEP 2: Translate Product Categories
# ============================================
print("\n[Step 2/8] Translating product categories to English...")
print("-" * 70)

products = products.merge(
    category_translation, 
    on='product_category_name', 
    how='left'
)

# Check for missing translations
missing_translations = products['product_category_name_english'].isna().sum()
if missing_translations > 0:
    print(f"  ⚠️  Warning: {missing_translations} products without English translation")
    # Fill missing with original Portuguese name
    products['product_category_name_english'].fillna(
        products['product_category_name'], 
        inplace=True
    )

print(f"  ✓ Translated {products['product_category_name_english'].nunique()} categories")

# ============================================
# STEP 3: Filter Beauty/Health Products
# ============================================
print("\n[Step 3/8] Filtering beauty/health products...")
print("-" * 70)

beauty_keywords = [
    'health_beauty', 
    'perfumery', 
    'fashion_cosmetics',
    'fashion_bags_accessories',  # Include bags/accessories (may contain makeup bags)
    'diapers_and_hygiene'  # Personal care items
]

beauty_products = products[
    products['product_category_name_english'].isin(beauty_keywords)
].copy()

print(f"  Initial beauty products: {len(beauty_products):,}")
print("\n  Breakdown by category:")
for keyword in beauty_keywords:
    count = len(beauty_products[beauty_products['product_category_name_english'] == keyword])
    if count > 0:
        pct = (count / len(beauty_products)) * 100
        print(f"    • {keyword:30s}: {count:,} ({pct:.1f}%)")

# ============================================
# STEP 4: Join All Tables
# ============================================
print("\n[Step 4/8] Joining tables...")
print("-" * 70)

# Start with order_items that contain beauty products
beauty_sales = order_items[
    order_items['product_id'].isin(beauty_products['product_id'])
].copy()

initial_rows = len(beauty_sales)
print(f"  Initial beauty order items: {initial_rows:,}")

# Add product details
beauty_sales = beauty_sales.merge(
    beauty_products[[
        'product_id', 
        'product_category_name_english', 
        'product_weight_g', 
        'product_length_cm', 
        'product_height_cm', 
        'product_width_cm'
    ]], 
    on='product_id', 
    how='left'
)
print(f"  ✓ Added product details")

# Add order details
beauty_sales = beauty_sales.merge(
    orders[[
        'order_id', 
        'customer_id', 
        'order_status', 
        'order_purchase_timestamp', 
        'order_delivered_customer_date'
    ]], 
    on='order_id', 
    how='left'
)
print(f"  ✓ Added order details")

# Add customer details
beauty_sales = beauty_sales.merge(
    customers[[
        'customer_id', 
        'customer_city', 
        'customer_state',
        'customer_zip_code_prefix'
    ]], 
    on='customer_id', 
    how='left'
)
print(f"  ✓ Added customer details")

# Add review scores (left join - not all orders have reviews)
beauty_sales = beauty_sales.merge(
    reviews[[
        'order_id', 
        'review_score', 
        'review_comment_message'
    ]], 
    on='order_id', 
    how='left'
)
print(f"  ✓ Added review data")

# Add payment details (aggregate per order)
payment_summary = payments.groupby('order_id').agg({
    'payment_value': 'sum',
    'payment_installments': 'max',
    'payment_type': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'credit_card'
}).reset_index()

beauty_sales = beauty_sales.merge(
    payment_summary,
    on='order_id',
    how='left'
)
print(f"  ✓ Added payment details")

print(f"\n  Final joined dataset: {len(beauty_sales):,} rows × {len(beauty_sales.columns)} columns")

# ============================================
# STEP 5: Data Cleaning
# ============================================
print("\n[Step 5/8] Cleaning data...")
print("-" * 70)

cleaning_log = []

# Track initial count
current_rows = len(beauty_sales)
cleaning_log.append(f"Initial rows: {current_rows:,}")

# Convert dates
beauty_sales['order_purchase_timestamp'] = pd.to_datetime(
    beauty_sales['order_purchase_timestamp'], 
    errors='coerce'
)
beauty_sales['order_delivered_customer_date'] = pd.to_datetime(
    beauty_sales['order_delivered_customer_date'], 
    errors='coerce'
)

# 1. Filter only delivered orders
beauty_sales = beauty_sales[
    beauty_sales['order_status'] == 'delivered'
].copy()
removed = current_rows - len(beauty_sales)
cleaning_log.append(f"Removed {removed:,} non-delivered orders")
current_rows = len(beauty_sales)

# 2. Remove rows with missing critical data
critical_columns = ['customer_id', 'price', 'order_purchase_timestamp']
beauty_sales = beauty_sales.dropna(subset=critical_columns)
removed = current_rows - len(beauty_sales)
cleaning_log.append(f"Removed {removed:,} rows with missing critical data")
current_rows = len(beauty_sales)

# 3. Remove duplicates
duplicates = beauty_sales.duplicated().sum()
beauty_sales = beauty_sales.drop_duplicates()
cleaning_log.append(f"Removed {duplicates:,} duplicate rows")
current_rows = len(beauty_sales)

# 4. Remove price outliers (keep 1st to 99th percentile)
q1 = beauty_sales['price'].quantile(0.01)
q99 = beauty_sales['price'].quantile(0.99)
beauty_sales = beauty_sales[
    (beauty_sales['price'] >= q1) & (beauty_sales['price'] <= q99)
]
removed = current_rows - len(beauty_sales)
cleaning_log.append(f"Removed {removed:,} price outliers (< ${q1:.2f} or > ${q99:.2f})")
current_rows = len(beauty_sales)

# 5. Fill missing review scores with median
reviews_missing = beauty_sales['review_score'].isna().sum()
if reviews_missing > 0:
    median_score = beauty_sales['review_score'].median()
    beauty_sales['review_score'].fillna(median_score, inplace=True)
    cleaning_log.append(f"Filled {reviews_missing:,} missing review scores with median ({median_score})")

# 6. Fill missing payment values
payment_missing = beauty_sales['payment_value'].isna().sum()
if payment_missing > 0:
    # Use price + freight as fallback
    beauty_sales['payment_value'].fillna(
        beauty_sales['price'] + beauty_sales['freight_value'], 
        inplace=True
    )
    cleaning_log.append(f"Filled {payment_missing:,} missing payment values")

# Print cleaning summary
print("\n  Cleaning Summary:")
for log in cleaning_log:
    print(f"    • {log}")

retention_rate = (len(beauty_sales) / initial_rows) * 100
print(f"\n  📊 Data retention rate: {retention_rate:.1f}%")

# ============================================
# STEP 6: Feature Engineering
# ============================================
print("\n[Step 6/8] Creating new features...")
print("-" * 70)

features_created = []

# 1. Revenue calculation
beauty_sales['revenue'] = beauty_sales['price'] + beauty_sales['freight_value']
features_created.append('revenue')

# 2. Extract date components
beauty_sales['order_year'] = beauty_sales['order_purchase_timestamp'].dt.year
beauty_sales['order_month'] = beauty_sales['order_purchase_timestamp'].dt.month
beauty_sales['order_day'] = beauty_sales['order_purchase_timestamp'].dt.day
beauty_sales['order_dayofweek'] = beauty_sales['order_purchase_timestamp'].dt.dayofweek
beauty_sales['order_week'] = beauty_sales['order_purchase_timestamp'].dt.isocalendar().week
features_created.extend(['order_year', 'order_month', 'order_day', 'order_dayofweek', 'order_week'])

# 3. Month name for better visualization
beauty_sales['month_name'] = beauty_sales['order_purchase_timestamp'].dt.strftime('%B')
features_created.append('month_name')

# 4. Quarter
beauty_sales['quarter'] = beauty_sales['order_purchase_timestamp'].dt.quarter
features_created.append('quarter')

# 5. Brazilian seasons (adapted)
def get_season(month):
    if month in [12, 1, 2]:
        return 'Summer'
    elif month in [3, 4, 5]:
        return 'Fall'
    elif month in [6, 7, 8]:
        return 'Winter'
    else:
        return 'Spring'

beauty_sales['season'] = beauty_sales['order_month'].apply(get_season)
features_created.append('season')

# 6. Vietnam context seasons (for business recommendations)
def get_vn_season(month):
    if month in [12, 1, 2]:
        return 'Q1-TetSeason'
    elif month in [3, 4, 5]:
        return 'Q2-SummerPrep'
    elif month in [6, 7, 8]:
        return 'Q3-MidYear'
    else:
        return 'Q4-YearEnd'

beauty_sales['vn_season'] = beauty_sales['order_month'].apply(get_vn_season)
features_created.append('vn_season')

# 7. Price segments
beauty_sales['price_segment'] = pd.cut(
    beauty_sales['price'],
    bins=[0, 50, 150, 500, np.inf],
    labels=['Budget', 'Mid-range', 'Premium', 'Luxury']
)
features_created.append('price_segment')

# 8. Price in VND (approximate conversion: 1 USD = 23,000 VND)
beauty_sales['price_vnd'] = (beauty_sales['price'] * 23000).round(0)
beauty_sales['revenue_vnd'] = (beauty_sales['revenue'] * 23000).round(0)
features_created.extend(['price_vnd', 'revenue_vnd'])

# 9. Delivery time (days)
beauty_sales['delivery_days'] = (
    beauty_sales['order_delivered_customer_date'] - 
    beauty_sales['order_purchase_timestamp']
).dt.days
features_created.append('delivery_days')

# 10. Delivery performance category
def delivery_category(days):
    if pd.isna(days):
        return 'Unknown'
    elif days <= 7:
        return 'Fast'
    elif days <= 14:
        return 'Normal'
    elif days <= 21:
        return 'Slow'
    else:
        return 'Very Slow'

beauty_sales['delivery_category'] = beauty_sales['delivery_days'].apply(delivery_category)
features_created.append('delivery_category')

# 11. Satisfaction category
def satisfaction_category(score):
    if pd.isna(score):
        return 'No Review'
    elif score >= 4.5:
        return 'Excellent'
    elif score >= 4.0:
        return 'Good'
    elif score >= 3.0:
        return 'Average'
    else:
        return 'Poor'

beauty_sales['satisfaction'] = beauty_sales['review_score'].apply(satisfaction_category)
features_created.append('satisfaction')

# 12. Product size category (based on weight)
def size_category(weight):
    if pd.isna(weight):
        return 'Unknown'
    elif weight < 100:
        return 'Mini'
    elif weight < 500:
        return 'Regular'
    else:
        return 'Large'

beauty_sales['product_size'] = beauty_sales['product_weight_g'].apply(size_category)
features_created.append('product_size')

# 13. Weekend flag
beauty_sales['is_weekend'] = (beauty_sales['order_dayofweek'] >= 5).astype(int)
features_created.append('is_weekend')

# 14. Payment installments category
def installment_category(installments):
    if pd.isna(installments) or installments == 1:
        return 'Cash/Single'
    elif installments <= 3:
        return 'Short-term'
    elif installments <= 6:
        return 'Medium-term'
    else:
        return 'Long-term'

beauty_sales['installment_category'] = beauty_sales['payment_installments'].apply(installment_category)
features_created.append('installment_category')

print(f"  ✓ Created {len(features_created)} new features")
print(f"  New features: {', '.join(features_created[:5])}...")

# ============================================
# STEP 7: Data Quality Checks
# ============================================
print("\n[Step 7/8] Running data quality checks...")
print("-" * 70)

quality_checks = []

# Check 1: Missing values in key columns
key_columns = ['price', 'revenue', 'review_score', 'delivery_days']
for col in key_columns:
    missing = beauty_sales[col].isna().sum()
    missing_pct = (missing / len(beauty_sales)) * 100
    quality_checks.append(f"{col}: {missing:,} missing ({missing_pct:.1f}%)")

# Check 2: Data ranges
quality_checks.append(f"Price range: ${beauty_sales['price'].min():.2f} - ${beauty_sales['price'].max():.2f}")
quality_checks.append(f"Review score range: {beauty_sales['review_score'].min():.1f} - {beauty_sales['review_score'].max():.1f}")

# Check 3: Date range
min_date = beauty_sales['order_purchase_timestamp'].min()
max_date = beauty_sales['order_purchase_timestamp'].max()
quality_checks.append(f"Date range: {min_date.date()} to {max_date.date()}")

# Check 4: Unique counts
quality_checks.append(f"Unique customers: {beauty_sales['customer_id'].nunique():,}")
quality_checks.append(f"Unique products: {beauty_sales['product_id'].nunique():,}")
quality_checks.append(f"Unique orders: {beauty_sales['order_id'].nunique():,}")

print("\n  Quality Check Results:")
for check in quality_checks:
    print(f"    • {check}")

# ============================================
# STEP 8: Save Cleaned Data
# ============================================
print("\n[Step 8/8] Saving cleaned dataset...")
print("-" * 70)

# Save main cleaned dataset
output_file = f'{OUTPUT_PATH}/beauty_sales_cleaned.csv'
beauty_sales.to_csv(output_file, index=False)
print(f"  ✓ Saved main dataset: {output_file}")
print(f"    Size: {len(beauty_sales):,} rows × {len(beauty_sales.columns)} columns")

# Generate and save summary statistics
summary_stats = {
    'Metric': [
        'Total Orders',
        'Unique Customers',
        'Unique Products',
        'Date Range',
        'Total Revenue',
        'Average Order Value',
        'Average Review Score',
        'Most Popular Category',
        'Most Common Price Segment',
        'Data Retention Rate'
    ],
    'Value': [
        f"{beauty_sales['order_id'].nunique():,}",
        f"{beauty_sales['customer_id'].nunique():,}",
        f"{beauty_sales['product_id'].nunique():,}",
        f"{min_date.date()} to {max_date.date()}",
        f"${beauty_sales['revenue'].sum():,.2f}",
        f"${beauty_sales['revenue'].mean():.2f}",
        f"{beauty_sales['review_score'].mean():.2f}/5.0",
        beauty_sales['product_category_name_english'].mode()[0],
        beauty_sales['price_segment'].mode()[0],
        f"{retention_rate:.1f}%"
    ]
}

summary_df = pd.DataFrame(summary_stats)
summary_file = f'{OUTPUT_PATH}/summary_statistics.csv'
summary_df.to_csv(summary_file, index=False)
print(f"  ✓ Saved summary statistics: {summary_file}")

# Save category breakdown
category_summary = beauty_sales.groupby('product_category_name_english').agg({
    'order_id': 'count',
    'revenue': 'sum',
    'review_score': 'mean'
}).reset_index()
category_summary.columns = ['category', 'order_count', 'total_revenue', 'avg_rating']
category_summary = category_summary.sort_values('total_revenue', ascending=False)

category_file = f'{OUTPUT_PATH}/category_summary.csv'
category_summary.to_csv(category_file, index=False)
print(f"  ✓ Saved category summary: {category_file}")

# Save monthly trend data
monthly_trend = beauty_sales.groupby(['order_year', 'order_month']).agg({
    'order_id': 'nunique',
    'revenue': 'sum',
    'review_score': 'mean'
}).reset_index()
monthly_trend.columns = ['year', 'month', 'orders', 'revenue', 'avg_rating']

monthly_file = f'{OUTPUT_PATH}/monthly_trend.csv'
monthly_trend.to_csv(monthly_file, index=False)
print(f"  ✓ Saved monthly trend: {monthly_file}")

# ============================================
# FINAL SUMMARY
# ============================================
print("\n" + "=" * 70)
print("✅ DATA CLEANING COMPLETE!")
print("=" * 70)

print(f"""
📊 FINAL DATASET SUMMARY:
   • Total rows: {len(beauty_sales):,}
   • Total columns: {len(beauty_sales.columns)}
   • Date range: {(max_date - min_date).days} days
   • Data retention: {retention_rate:.1f}%
   • Total revenue: ${beauty_sales['revenue'].sum():,.2f}
   • Average order value: ${beauty_sales['revenue'].mean():.2f}

📁 OUTPUT FILES SAVED:
   1. {output_file}
   2. {summary_file}
   3. {category_file}
   4. {monthly_file}

🎯 NEXT STEPS:
   1. Review cleaned data in Excel/Power BI
   2. Run 02_analysis.py for deeper insights
   3. Create visualizations in Power BI

💡 READY FOR ANALYSIS!
""")

print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
