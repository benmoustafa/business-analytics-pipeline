-- Staging model: light cleaning/renaming of the raw order_items table.
-- Composite PK: (order_id, order_item_id)

with source as (
    select * from {{ source('raw', 'olist_order_items_dataset') }}
)

select
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date::timestamp as shipping_limit_ts,
    price,
    freight_value
from source
