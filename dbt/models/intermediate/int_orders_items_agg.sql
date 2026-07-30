with items as (
    select * from {{ ref('stg_order_items') }}
)

select
    order_id,

    count(*)                          as item_count,
    count(distinct product_id)        as distinct_product_count,
    count(distinct seller_id)         as distinct_seller_count,

    sum(price)                        as revenue,
    sum(freight_value)                as freight_total,
    sum(price + freight_value)        as gmv,          -- Gross Merchandise Value

    min(shipping_limit_ts)            as earliest_shipping_limit_ts,
    max(shipping_limit_ts)            as latest_shipping_limit_ts

from items
group by order_id
