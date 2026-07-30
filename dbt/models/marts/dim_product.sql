-- Mart: dim_product
-- One row per product_id.
-- Joins to the category translation table so we always have the English name.

with products as (
    select * from {{ ref('stg_products') }}
),

translations as (
    select * from {{ ref('stg_category_translation') }}
)

select
    p.product_id                                        as product_key,
    p.product_category_name,
    coalesce(t.category_name_english, 'unknown')        as category_name_english,
    p.product_name_length,
    p.product_description_length,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,

    -- Derived: volumetric weight in kg (L × W × H / 5000 — standard e-commerce formula)
    round(
        (p.product_length_cm * p.product_width_cm * p.product_height_cm)::numeric
        / 5000,
        2
    )                                                   as volumetric_weight_kg

from products p
left join translations t
    on p.product_category_name = t.product_category_name
