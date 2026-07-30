-- Intermediate: aggregate review scores to order-level.
-- review_id is not perfectly unique in the source (814 dupes) so we
-- de-duplicate by keeping the most recent answer per order.

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
