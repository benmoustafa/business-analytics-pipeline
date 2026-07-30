-- Mart: dim_customer
-- One row per customer_unique_id (true person).
-- customer_id is order-scoped; customer_unique_id is the real person.
-- We pick the most recent location data per unique customer.

with customers as (
    select * from {{ ref('stg_customers') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by customer_unique_id
            order by customer_id desc   -- proxy for recency: latest customer_id
        ) as rn
    from customers
)

select
    customer_unique_id                  as customer_key,
    customer_id                         as latest_customer_id,
    zip_code_prefix,
    city,
    state
from ranked
where rn = 1
