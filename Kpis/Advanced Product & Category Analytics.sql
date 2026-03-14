use ecommerce;
-- 1  Assess revenue volatility for each product. :
with product_revenue as (select f.product_key,d.full_date,sum(f.net_amount) as daily_revenue
from fact f join date d
on f.date_key = d.date_key
group by f.product_key, d.full_date
)
select product_key,round(stddev(daily_revenue),2) as revenue_volatility
from product_revenue
group by product_key
order by revenue_volatility desc;

-- 2 Detect trending categories based on recent performance compared to historical behavior. 
with category_monthly_revenue as (select c.product_category,d.year,d.month,
sum(f.net_amount) as monthly_revenue
from fact f join date d
on f.date_key = d.date_key
join category c
on f.category_key = c.category_key
group by c.product_category, d.year, d.month
),
category_trends as (select product_category,year,month,monthly_revenue,
avg(monthly_revenue) over(partition by product_category) as historical_avg
from category_monthly_revenue)
select product_category,year,month,monthly_revenue,historical_avg,
(monthly_revenue - historical_avg) / historical_avg * 100 as trend_pct,
    case
        when monthly_revenue > historical_avg then 'Trending Up'
        when monthly_revenue < historical_avg then 'Trending Down'
        else 'Stable'end as trend_status
from category_trends
order by trend_pct desc;

-- 3 seasonality of products
with monthly_revenue as (select d.year,d.month,sum(f.net_amount) as revenue
from fact f join date d
on f.date_key = d.date_key
group by d.year, d.month
),

avg_rev as (select year,month,revenue,
avg(revenue) over(partition by month) as avg_month_revenue
from monthly_revenue
)
select year,month,revenue,avg_month_revenue,
revenue - avg_month_revenue as deviation,
    case 
        when revenue > avg_month_revenue then 'Peak Season'
        when revenue < avg_month_revenue then 'Low Season'
        else 'Normal' end as seasonal_flag
from avg_rev
order by month, year;

-- 4 Evaluate profit consistency across time periods. 
with monthly_profit as (select d.year,d.month,sum(f.profit_amount) as monthly_profit
from fact f join date d
on f.date_key = d.date_key
group by d.year, d.month
)
select year,month,monthly_profit,
avg(monthly_profit) over(partition by year) as avg_profit,
stddev(monthly_profit) over(partition by year) as profit_volatility
from monthly_profit
order by year, month;

-- 5  Identify products experiencing sustained decline across consecutive periods. 
with product_monthly_revenue as (select p.product_name,d.year,d.month,
sum(f.net_amount) as monthly_revenue
from fact f join products p
on f.product_key = p.product_key
join date d
on f.date_key = d.date_key
group by p.product_name, d.year, d.month
)
, revenue_trend as (select product_name,year,month,monthly_revenue,
lag(monthly_revenue,1) over(partition by product_name order by year,month) as prev_rev,
lag(monthly_revenue,2) over(partition by product_name order by year,month) as prev2_rev
from product_monthly_revenue
)
select product_name,year,month,monthly_revenue,prev_rev,prev2_rev
from revenue_trend
where monthly_revenue < prev_rev
and prev_rev < prev2_rev;



