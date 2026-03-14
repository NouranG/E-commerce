use ecommerce;
-- customer behaviour analysis
-- 1 Evaluate cumulative spending behavior per customer over time. 
with customer_spending as (
select c.customer_id as customer_id,f.net_amount as net_amount,d.full_date as purchase_date
from fact f join customers c 
on f.customer_key=c.customer_key
join date d
on f.date_key=d.date_key
)
select customer_id,purchase_date,net_amount,
sum(net_amount) over(partition by customer_id order by purchase_date
rows between unbounded preceding and current row
) as cumulative_spending
from customer_spending
order by customer_id;

-- 2 Measure time intervals between consecutive purchases for each customer. 
with customer_purchase as (
select c.customer_id as customer_id,d.full_date as purchase_date,
lag(d.full_date)over(partition by customer_id order by d.full_date) as prev_purchase
from fact f join customers c 
on f.customer_key=c.customer_key
join date d
on f.date_key=d.date_key
)
select customer_id,purchase_date,
datediff(purchase_date,prev_purchase) as interval_between_purchases
from customer_purchase
order by interval_between_purchases desc;

-- 3 Rank customers based on recency of activity.
with customer_purchase as (
select c.customer_id as customer_id,max(d.full_date) as purchase_date
from fact f join customers c 
on f.customer_key=c.customer_key
join date d
on f.date_key=d.date_key
group by c.customer_id
)
select customer_id,purchase_date,dense_rank()over(order by purchase_date desc) as rnk
from customer_purchase;


-- 4 Segment customers into spending tiers (e.g., quartiles). 
with net_spending as(select c.customer_id as customer_id , sum(f.net_amount)  as total_spent
from fact f join customers c
on f.customer_key=c.customer_key
group by c.customer_id),
segments as(select customer_id,
ntile(4)over(order by total_spent) as segment
from net_spending)
select customer_id,
case
 when segment = 1 then 'infrequent_spender'
 when segment = 2 then 'frequent_spender'
 when segment = 3 then 'Loyal_customer'
 else 'VIP' end as customer_tier
from segments;

-- 5  Identify the top percentile of high-value customers. 
with net_spending as(select c.customer_id as customer_id , sum(f.net_amount)  as total_spent
from fact f join customers c
on f.customer_key=c.customer_key
group by c.customer_id),
percent as (select customer_id, ntile(10) over (order by total_spent) as percentile
from net_spending) 
select customer_id,percentile 
from percent
where percentile=10;









