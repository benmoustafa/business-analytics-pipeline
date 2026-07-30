-- Mart: dim_seller
-- One row per seller_id.

with sellers as (
    select * from {{ ref('stg_sellers') }}
)

select
    seller_id       as seller_key,
    zip_code_prefix,
    city,
    state
from sellers
