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
