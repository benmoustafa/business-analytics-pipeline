with orders as (
    select * from {{ ref('stg_orders') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

items_agg as (
    select * from {{ ref('int_orders_items_agg') }}
),

payments_agg as (
    select * from {{ ref('int_orders_payments_agg') }}
),

reviews as (
    select * from {{ ref('int_orders_reviews_dedup') }}
)

select
    -- Keys
    o.order_id,
    c.customer_unique_id                                            as customer_key,
    o.purchase_ts::date                                             as purchase_date_key,
    o.delivered_customer_ts::date                                   as delivered_date_key,

    -- Order status & timestamps
    o.order_status,
    o.purchase_ts,
    o.approved_ts,
    o.delivered_carrier_ts,
    o.delivered_customer_ts,
    o.estimated_delivery_ts,

    -- Delivery performance
    case
        when o.delivered_customer_ts is not null
             and o.estimated_delivery_ts is not null
        then (o.delivered_customer_ts - o.estimated_delivery_ts) < interval '0'
    end                                                             as delivered_on_time,

    case
        when o.delivered_customer_ts is not null
             and o.delivered_carrier_ts is not null
        then extract(
                epoch from (o.delivered_customer_ts - o.delivered_carrier_ts)
             ) / 86400.0
    end                                                             as carrier_to_customer_days,

    case
        when o.delivered_customer_ts is not null
             and o.purchase_ts is not null
        then extract(
                epoch from (o.delivered_customer_ts - o.purchase_ts)
             ) / 86400.0
    end                                                             as order_to_delivery_days,

    -- Item & revenue metrics (from intermediate)
    i.item_count,
    i.distinct_product_count,
    i.distinct_seller_count,
    i.revenue,
    i.freight_total,
    i.gmv,

    -- Payment metrics (from intermediate)
    p.total_payment_value,
    p.max_installments,
    p.primary_payment_type,
    p.has_credit_card,
    p.has_boleto,
    p.has_voucher,
    p.has_debit_card,

    -- Review metrics (from intermediate — may be null for unreviewed orders)
    r.review_score,
    r.review_created_ts,
    r.review_answered_ts

from orders o

left join customers c
    on o.customer_id = c.customer_id

left join items_agg i
    on o.order_id = i.order_id

left join payments_agg p
    on o.order_id = p.order_id

left join reviews r
    on o.order_id = r.order_id
