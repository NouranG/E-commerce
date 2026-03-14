use ecommerce;

-- Core business Kpis
-- 1 revenue 
select sum(net_amount) as revenue
from fact;

-- 2 Gross profit
select sum(profit_amount) as gross_profit
from fact;

-- Average Order Value (AOV): 
select sum(net_amount) /count(distinct fact_id) as AOV
from fact;

-- Customer Lifetime Value (CLV): 
select customer_key,sum(net_amount) over(partition by customer_key) as CLV
from fact;
-- Repeat Purchase Rate: 
with customer_orders AS (select customer_key,count(*) as purchase_count
from fact
group by customer_key
)
select 
round(sum(case when purchase_count > 1 THEN 1 ELSE 0 END) /
count(*) * 100 ,2)as repeat_purchase_rate
from customer_orders;

-- Profit margin
SELECT 
sum(profit_amount) / sum(net_amount) * 100 as profit_margin
from fact;








 