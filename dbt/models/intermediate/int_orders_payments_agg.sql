with payments as (
    select * from {{ ref('stg_order_payments') }}
)

select
    order_id,

    sum(payment_value)                                as total_payment_value,
    max(payment_installments)                         as max_installments,

    -- Payment type flags — useful for downstream analysis
    max(case when payment_type = 'credit_card' then 1 else 0 end) as has_credit_card,
    max(case when payment_type = 'boleto'      then 1 else 0 end) as has_boleto,
    max(case when payment_type = 'voucher'     then 1 else 0 end) as has_voucher,
    max(case when payment_type = 'debit_card'  then 1 else 0 end) as has_debit_card,

    -- Dominant payment type (highest value)
    (array_agg(payment_type order by payment_value desc))[1]       as primary_payment_type,

    count(*)                                          as payment_row_count

from payments
group by order_id
