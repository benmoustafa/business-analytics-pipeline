with source as (
    select * from {{ source('raw', 'product_category_name_translation') }}
)

select
    product_category_name,
    product_category_name_english as category_name_english
from source
