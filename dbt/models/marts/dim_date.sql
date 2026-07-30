with date_spine as (
    select
        generate_series(
            '2016-01-01'::date,
            '2019-12-31'::date,
            '1 day'::interval
        )::date as date_day
)

select
    date_day                                        as date_key,
    date_day,

    -- Calendar fields
    extract(year  from date_day)::int               as year,
    extract(month from date_day)::int               as month,
    extract(day   from date_day)::int               as day,
    extract(dow   from date_day)::int               as day_of_week,   -- 0=Sun … 6=Sat
    extract(doy   from date_day)::int               as day_of_year,
    extract(week  from date_day)::int               as week_of_year,
    extract(quarter from date_day)::int             as quarter,

    -- Human-readable labels
    to_char(date_day, 'Month')                      as month_name,
    to_char(date_day, 'Mon')                        as month_name_short,
    to_char(date_day, 'Day')                        as day_name,
    to_char(date_day, 'YYYY-MM')                    as year_month,

    -- Boolean flags
    (extract(dow from date_day) in (0, 6))::boolean as is_weekend

from date_spine
