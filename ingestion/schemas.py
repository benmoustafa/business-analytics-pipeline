"""
Expected schema definitions for the Olist Brazilian E-Commerce dataset.
Used by load.py to validate raw CSVs before converting to Parquet.
"""

# Maps each raw CSV filename to its expected columns and primary key(s).
# Used for schema validation and duplicate/null checks during ingestion.
DATASET_SCHEMAS = {
    "olist_orders_dataset.csv": {
        "primary_key": ["order_id"],
        "columns": [
            "order_id", "customer_id", "order_status",
            "order_purchase_timestamp", "order_approved_at",
            "order_delivered_carrier_date", "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    },
    "olist_order_items_dataset.csv": {
        "primary_key": ["order_id", "order_item_id"],
        "columns": [
            "order_id", "order_item_id", "product_id", "seller_id",
            "shipping_limit_date", "price", "freight_value",
        ],
    },
    "olist_customers_dataset.csv": {
        "primary_key": ["customer_id"],
        "columns": [
            "customer_id", "customer_unique_id", "customer_zip_code_prefix",
            "customer_city", "customer_state",
        ],
    },
    "olist_products_dataset.csv": {
        "primary_key": ["product_id"],
        "columns": [
            "product_id", "product_category_name", "product_name_lenght",
            "product_description_lenght", "product_photos_qty",
            "product_weight_g", "product_length_cm", "product_height_cm",
            "product_width_cm",
        ],
    },
    "olist_order_payments_dataset.csv": {
        "primary_key": ["order_id", "payment_sequential"],
        "columns": [
            "order_id", "payment_sequential", "payment_type",
            "payment_installments", "payment_value",
        ],
    },
    "olist_order_reviews_dataset.csv": {
        "primary_key": ["review_id"],
        "columns": [
            "review_id", "order_id", "review_score",
            "review_comment_title", "review_comment_message",
            "review_creation_date", "review_answer_timestamp",
        ],
    },
    "olist_sellers_dataset.csv": {
        "primary_key": ["seller_id"],
        "columns": [
            "seller_id", "seller_zip_code_prefix", "seller_city", "seller_state",
        ],
    },
    "olist_geolocation_dataset.csv": {
        "primary_key": [],  # not unique per row, no single-row PK
        "columns": [
            "geolocation_zip_code_prefix", "geolocation_lat",
            "geolocation_lng", "geolocation_city", "geolocation_state",
        ],
    },
    "product_category_name_translation.csv": {
        "primary_key": ["product_category_name"],
        "columns": ["product_category_name", "product_category_name_english"],
    },
}
