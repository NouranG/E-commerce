use ecommerce;

-- Time based performace analysis

-- 1 cum rev over time
with cum_rev as (select 
f.date_key,
sum(f.net_amount) as revenue
from fact f
group by f.date_key)
select sum(revenue) over(order by d.full_date) as cum_rev,d.full_date as date
from cum_rev cr join date d
on cr.date_key=d.date_key;


-- 2 Month-to-Date performance
select d.full_date, d.month,sum(f.net_amount) over(partition by d.year, d.month
 order by d.full_date desc rows between 1 preceding and current row
) as month_to_date_perf 
from fact f join date d
on f.date_key=d.date_key
order by d.full_date;

-- Annual performance progression
select d.full_date,d.year,sum(f.profit_amount) over(partition by d.year
 order by d.full_date
) as year_to_date_perf 
from fact f join date d
on f.date_key=d.date_key
order by d.full_date;

-- Smooth short term volatility
-- 7 days
select d.full_date,
sum(f.net_amount) as daily_rev,
avg(sum(f.net_amount)) over(order by d.full_date rows between 6 preceding and current row) as moving_avg
from fact f join date d 
on f.date_key = d.date_key
group by d.full_date
order by d.full_date;

-- compare current with previous month performance
with cte as (
select d.year as year,d.month as month  ,
sum(f.net_amount) as rev
from fact f join date d
on f.date_key=d.date_key
group by year,month
)
select year,month,rev,lag(rev)over(order by year,month) as prev_rev,
case when rev>lag(rev)over(order by year,month) then 'Growth' else 'Decline' 
end as month_perf
from cte
order by year;

-- Acceleration or deceleration
with cte as (
select d.year as year,d.month as month  ,
sum(f.net_amount) as rev
from fact f join date d
on f.date_key=d.date_key
group by year,month
),
growth as (select year,month,rev,
rev-lag(rev)over(order by year,month) as growth_rate
from cte)
select year,month,rev,growth_rate,
growth_rate-lag(growth_rate)over(order by year,month) as Acceleration
from growth
order by year,month;


















 





