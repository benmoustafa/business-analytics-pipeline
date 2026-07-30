with reviews as (
    select * from {{ ref('stg_order_reviews') }}
),

deduped as (
    select distinct on (order_id)
        order_id,
        review_id,
        review_score,
        review_comment_title,
        review_comment_message,
        review_created_ts,
        review_answered_ts
    from reviews
    order by order_id, review_answered_ts desc
)

select * from deduped
