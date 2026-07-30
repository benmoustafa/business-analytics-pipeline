-- Staging model: light cleaning/renaming of the raw order_payments table.
-- Composite PK: (order_id, payment_sequential)

with source as (
    select * from {{ source('raw', 'olist_order_payments_dataset') }}
)

select
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    payment_value
from source
