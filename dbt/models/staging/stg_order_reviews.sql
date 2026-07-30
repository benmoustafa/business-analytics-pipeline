-- Staging model: light cleaning/renaming of the raw order_reviews table.
-- Note: review_id is not perfectly unique in the source (814 dupes detected in ingestion).

with source as (
    select * from {{ source('raw', 'olist_order_reviews_dataset') }}
)

select
    review_id,
    order_id,
    review_score,
    review_comment_title,
    review_comment_message,
    review_creation_date::timestamp    as review_created_ts,
    review_answer_timestamp::timestamp as review_answered_ts
from source
