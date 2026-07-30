-- Staging model: light cleaning/renaming of the raw products table.
-- product_category_name has ~610 nulls — handled later in the mart with a coalesce join
-- to product_category_name_translation.

with source as (
    select * from {{ source('raw', 'olist_products_dataset') }}
)

select
    product_id,
    product_category_name,
    product_name_lenght        as product_name_length,
    product_description_lenght as product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
from source
