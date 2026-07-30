-- Staging model: light cleaning/renaming of the raw customers table.
-- One staging model per raw source table — no joins or business logic here yet.

with source as (
    select * from {{ source('raw', 'olist_customers_dataset') }}
)

select
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix  as zip_code_prefix,
    customer_city             as city,
    customer_state            as state
from source
