-- Staging model: light cleaning/renaming of the raw orders table.
-- One staging model per raw source table — no joins or business logic here yet.

with source as (
    select * from {{ source('raw', 'olist_orders_dataset') }}
)

select
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp::timestamp as purchase_ts,
    order_approved_at::timestamp as approved_ts,
    order_delivered_carrier_date::timestamp as delivered_carrier_ts,
    order_delivered_customer_date::timestamp as delivered_customer_ts,
    order_estimated_delivery_date::timestamp as estimated_delivery_ts
from source
