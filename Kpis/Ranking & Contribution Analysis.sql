use ecommerce;
-- Ranking & Contribution Analysis 

-- 1 Rank products within each category based on revenue performance. 
with rev as(select sum(f.net_amount) as rev,
product_name,product_category,product_id
from fact f join products p
on f.product_key=p.product_key
group by product_name,product_category,product_id)

select distinct(product_category),rev,product_name ,
rank() over(partition by product_category order by rev desc) 
as rnk
from rev;

-- 2 product contribution to category total revenue:
with rev as (select p.product_id,p.product_name as product_name,p.product_category as category,
 sum(f.net_amount) over(partition by p.product_id) as product_rev,
sum(f.net_amount) over (partition by p.product_category) as category_rev
from fact f join products p
on f.product_key=p.product_key)
select product_name,category,product_rev,category_rev,
(product_rev/category_rev)*100 as contribution_pct
from rev
group by product_name, category, product_rev, category_rev;


-- 3  Identify high-impact products contributing to the majority of revenue(pareto):
with product_rev as (select p.product_name,sum(f.net_amount) as revenue
from fact f 
join products p
on f.product_key = p.product_key
group by p.product_name
),
total_rev as (
select sum(revenue) as total_revenue
from product_rev
)
select product_name,revenue,
revenue/total_revenue*100 as contribution_pct,
sum(revenue) over(order by revenue desc) / total_revenue *100 as cumulative_pct
from product_rev,total_rev
order by revenue desc;

-- 4. Rank regions according to profitability. 
with total_profit as (select c.customer_state as state,
sum(f.profit_amount)as total_profit_in_state
from fact f join customers c
on f.customer_key=c.customer_key
group by c.customer_state)
select state,
rank () over(order by total_profit_in_state desc) as rnk
from total_profit;

-- 5 Rank brands inside each category based on total profit generation.
with total_profit as(select p.brand as brand ,p.product_category as category,
sum(f.profit_amount) as brand_total_profit
from fact f join products p
on f.product_key=p.product_key
group by p.product_category,p.brand)
select category,brand,
rank() over(partition by category order by brand_total_profit desc) as rnk
from total_profit;




 


 