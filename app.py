import streamlit as st
import pandas as pd
import altair as alt
alt.data_transformers.disable_max_rows()
from sqlalchemy import create_engine

# -------------------------
# Database connection
# -------------------------
engine = create_engine("mysql+pymysql://root:12345@localhost/ecommerce")

# -------------------------
# Caching SQL queries
# -------------------------
@st.cache_data
def run_query(query):
    return pd.read_sql(query, engine)

# -------------------------
# Dashboard Title
# -------------------------
st.title("E-Commerce Analytics Dashboard")

# -------------------------
# Core Business KPIs
# -------------------------
st.header("Core Business KPIs")

revenue_query = "SELECT SUM(net_amount) AS revenue FROM fact;"
profit_query = "SELECT SUM(profit_amount) AS profit FROM fact"
aov_query = "SELECT SUM(net_amount)/COUNT(DISTINCT fact_id) AS aov FROM fact;"
clv_quert="select customer_key,sum(net_amount) over(partition by customer_key) as CLV from fact;"
margin_query = "SELECT SUM(profit_amount)/SUM(net_amount)*100 AS profit_margin FROM fact;"
repeat_purchase_query = """
WITH customer_orders AS (
    SELECT customer_key, COUNT(*) AS purchase_count
    FROM fact
    GROUP BY customer_key
)
SELECT 
SUM(CASE WHEN purchase_count > 1 THEN 1 ELSE 0 END)/COUNT(*)*100 AS repeat_rate
FROM customer_orders;
"""

revenue = run_query(revenue_query).iloc[0,0]
profit = run_query(profit_query).iloc[0,0]
aov = run_query(aov_query).iloc[0,0]
margin = run_query(margin_query).iloc[0,0]
repeat_rate = run_query(repeat_purchase_query).iloc[0,0]

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Revenue", f"${revenue:,.0f}", delta=None)
    st.caption(f"Full value: ${revenue:,.0f}")
with col2:
    st.metric("Gross Profit", f"${profit:,.0f}", delta=None)
    st.caption(f"Full value: ${profit:,.0f}")
with col3:
    st.metric("AOV", f"${aov:,.2f}", delta=None)
    st.caption(f"Full value: ${aov:,.0f}")
with col4:
    st.metric("Profit Margin", f"{margin:.2f}%", delta=None)
    st.caption(f"Full value: ${margin:,.0f}")
with col5:
    st.metric("Repeat Purchase Rate", f"{repeat_rate:.2f}%", delta=None)
    st.caption(f"Full value: {repeat_rate:,.0f}")

# -------------------------
# Tabs
# -------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Time Analysis",
    "Customer Behavior",
    "Ranking",
    "Product Analytics"
])

# -------------------------
# Tab 1: Time Analysis
# -------------------------
with tab1:
    with st.expander("Show Time based analysis"):

        st.header("Time-Based Performance")

        # Cumulative Revenue
        st.subheader("Cumulative Revenue")
        cum_revenue_query = """
        WITH cum_rev AS (
            SELECT f.date_key, SUM(f.net_amount) AS revenue
            FROM fact f
            GROUP BY f.date_key
        )
        SELECT SUM(revenue) OVER(ORDER BY d.full_date) AS cum_rev, d.full_date AS date
        FROM cum_rev cr
        JOIN date d ON cr.date_key = d.date_key;
        """
        cum_df = run_query(cum_revenue_query)
        st.line_chart(cum_df.set_index("date")["cum_rev"])

        # Month-to-Date Revenue
        st.subheader("Month-to-Date Revenue")
        mtd_query = """
        SELECT d.full_date AS date, d.month,
        SUM(f.net_amount) OVER(PARTITION BY d.year, d.month ORDER BY d.full_date ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS mtd_revenue
        FROM fact f JOIN date d ON f.date_key = d.date_key
        ORDER BY date;
        """
        mtd_df = run_query(mtd_query)
        st.line_chart(mtd_df.set_index("date")["mtd_revenue"])

        # Year-to-Date Profit
        st.subheader("Year-to-Date Profit")
        ytd_query = """
        SELECT d.full_date, d.year,
        SUM(f.profit_amount) OVER(PARTITION BY d.year ORDER BY d.full_date) AS ytd_profit
        FROM fact f JOIN date d ON f.date_key = d.date_key
        ORDER BY d.full_date;
        """
        ytd_df = run_query(ytd_query)
        st.bar_chart(ytd_df.groupby("year")["ytd_profit"].max())

        # 7-Day Moving Average
        st.subheader("7-Day Revenue Moving Average")
        mov_avg_query = """
        SELECT d.full_date, SUM(f.net_amount) AS daily_rev,
        AVG(SUM(f.net_amount)) OVER(ORDER BY d.full_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS moving_avg
        FROM fact f JOIN date d ON f.date_key = d.date_key
        GROUP BY d.full_date
        ORDER BY d.full_date;
        """
        mov_avg_df = run_query(mov_avg_query)
        st.line_chart(mov_avg_df.set_index("full_date")[["daily_rev", "moving_avg"]])

        # Current vs Previous Month
        st.subheader("Month-over-Month Performance")
        curr_prev_query = """
        WITH cte AS (
            SELECT d.year, d.month, SUM(f.net_amount) AS rev
            FROM fact f JOIN date d ON f.date_key = d.date_key
            GROUP BY d.year, d.month
        )
        SELECT year, month, rev,
        LAG(rev) OVER(ORDER BY year, month) AS prev_rev,
        CASE WHEN rev > LAG(rev) OVER(ORDER BY year, month) THEN 'Growth' ELSE 'Decline' END AS month_perf
        FROM cte
        ORDER BY year, month;
        """
        month_perf_df = run_query(curr_prev_query)
        st.dataframe(month_perf_df)  # use dataframe for categorical comparison

        # Acceleration/Deceleration
        st.subheader("Acceleration / Deceleration in Revenue")
        acc_dec_query = """
        WITH cte AS (
            SELECT d.year, d.month, SUM(f.net_amount) AS rev
            FROM fact f JOIN date d ON f.date_key = d.date_key
            GROUP BY d.year, d.month
        ),
        growth AS (
            SELECT year, month, rev,
            rev - LAG(rev) OVER(ORDER BY year, month) AS growth_rate
            FROM cte
        )
        SELECT year, month, rev, growth_rate,
        growth_rate - LAG(growth_rate) OVER(ORDER BY year, month) AS acceleration
        FROM growth
        ORDER BY year, month;
        """
        acc_df = run_query(acc_dec_query)
        st.dataframe(acc_df)

# -------------------------
# Tab 2: Customer behavior
# -------------------------
with tab2:
        with st.expander("Show Customer analytics"):
            st.header("Customer behavior analytics")

            st.subheader("Cumulative spending for each customer over time")
            cum_spend_query="""
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
"""
            cum_spend_df = run_query(cum_spend_query)
            st.dataframe(cum_spend_df)

            
            #Recency of activity
            st.subheader("Recency of Activity")
            query = """
WITH last_purchase AS (
    SELECT c.customer_id,
           MAX(d.full_date) AS last_purchase
    FROM fact f
    JOIN customers c ON f.customer_key = c.customer_key
    JOIN date d ON f.date_key = d.date_key
    GROUP BY c.customer_id
)
SELECT customer_id,
       last_purchase,
       DENSE_RANK() OVER (ORDER BY last_purchase DESC) AS recency_rank
FROM last_purchase;
"""

            df = run_query(query)

# Ensure numeric
            df['recency_rank'] = pd.to_numeric(df['recency_rank'], errors='coerce')

            # Optional: show top 20 most recent
            df_top = df.sort_values('recency_rank').head(20)

            st.subheader("Top 20 Customers by Recency of Activity")

            # Altair bar chart
            chart = alt.Chart(df_top).mark_bar().encode(
                x=alt.X('customer_id:N', title='Customer ID'),
                y=alt.Y('recency_rank:Q', title='Recency Rank'),
                tooltip=['customer_id', 'last_purchase', 'recency_rank']
            ).properties(width=700, height=400)

            st.altair_chart(chart,use_container_width=True)

            #Segment customers into spending tiers
            st.subheader("Customers Tiers")
            tiers_query="""
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
            """
            tiers_df=run_query(tiers_query)
            st.dataframe(tiers_df)

            #Identify the top percentile of high-value customers
            st.subheader("Top Percentile")
            percentile_query="""
        with net_spending as(select c.customer_id as customer_id , sum(f.net_amount)  as total_spent
from fact f join customers c
on f.customer_key=c.customer_key
group by c.customer_id),
percent as (select customer_id, ntile(10) over (order by total_spent) as percentile
from net_spending) 
select customer_id,percentile 
from percent
where percentile=10;
            """
            percentile_df=run_query(percentile_query)
            st.dataframe(percentile_df)
# -------------------------
# Tab 3: Ranking
# -------------------------
with tab3:
    with st.expander("Ranking and contribution analysis"):
        st.header("Ranking and contribution analysis")

        #Rank products within each category based on revenue performance
        st.subheader("Rank products within each category based on revenue performance")
        pro_rev_query="""
with rev as(select sum(f.net_amount) as rev,
product_name,product_category,product_id
from fact f join products p
on f.product_key=p.product_key
group by product_name,product_category,product_id)

select distinct(product_category),rev,product_name ,
dense_rank() over(partition by product_category order by rev desc) 
as rnk
from rev;
"""
        pro_rev_df=run_query(pro_rev_query)
        st.dataframe(pro_rev_df)

        #product contribution to category total revenue
        st.subheader("product contribution to category total revenue")
        pro_cont_query="""
with rev as (select p.product_id,p.product_name as product_name,p.product_category as category,
 sum(f.net_amount) over(partition by p.product_id) as product_rev,
sum(f.net_amount) over (partition by p.product_category) as category_rev
from fact f join products p
on f.product_key=p.product_key)
select product_name,category,product_rev,category_rev,
(product_rev/category_rev)*100 as contribution_pct
from rev
group by product_name, category, product_rev, category_rev;
"""
        pro_cont_df=run_query(pro_cont_query)
        st.dataframe(pro_cont_df)

        #Identify high-impact products contributing to the majority of revenue(pareto)
        st.subheader("Pareto analysis")

        pareto_query="""
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
"""
        pareto_df=run_query(pareto_query)
        pareto_df=pareto_df.head(30)
        bars = alt.Chart(pareto_df).mark_bar().encode(
    x=alt.X("product_name:N", sort="-y", title="Product"),
    y=alt.Y("revenue:Q", title="Revenue"),
    tooltip=["product_name","revenue","contribution_pct"]
)
        line = alt.Chart(pareto_df).mark_line(color="green").encode(
    x="product_name:N",
    y=alt.Y("cumulative_pct:Q", title="Cumulative %"),
    tooltip=["cumulative_pct"]
)

        chart = alt.layer(bars, line).resolve_scale(
    y='independent'
)

        st.subheader("Pareto Chart: Product Revenue Contribution")
        st.altair_chart(chart, use_container_width=True)
        # Rank regions according to profitability. 
        st.subheader("Regions according to profitability")
        reg_query="""
with total_profit as (select c.customer_state as state,
sum(f.profit_amount)as total_profit_in_state
from fact f join customers c
on f.customer_key=c.customer_key
group by c.customer_state)
select state,total_profit_in_state,
rank () over(order by total_profit_in_state desc) as rnk
from total_profit;
"""
        reg_df = run_query(reg_query)

        bars = alt.Chart(reg_df).mark_bar().encode(
        x=alt.X("state:N", sort="-y", title="State"),
        y=alt.Y("total_profit_in_state:Q", title="Profit"),
        tooltip=["state", "total_profit_in_state"]
    )

        st.altair_chart(bars, use_container_width=True)

        #Rank brands inside each category based on total profit generation.
        st.subheader("Brands rank")
        rnk_query="""
with total_profit as(select p.brand as brand ,p.product_category as category,
sum(f.profit_amount) as brand_total_profit
from fact f join products p
on f.product_key=p.product_key
group by p.product_category,p.brand)
select category,brand,
rank() over(partition by category order by brand_total_profit desc) as rnk
from total_profit;
"""

        rnk_df=run_query(rnk_query)
        st.dataframe(rnk_df)

# -------------------------
# Tab 4: Advanced analytics
# -------------------------
with tab4:
    with st.expander("Show Product Analytics"):
        st.header("Advanced Analytics")

        #Assess revenue volatility for each product
        st.subheader("Revenue volatility for each product")
        volatility_query="""
with product_revenue as (select f.product_key,d.full_date,sum(f.net_amount) as daily_revenue
from fact f join date d
on f.date_key = d.date_key
group by f.product_key, d.full_date
)
select product_key,round(stddev(daily_revenue),2) as revenue_volatility
from product_revenue
group by product_key
order by revenue_volatility desc;
"""
        volatility_df=run_query(volatility_query)
        volatility_df=volatility_df.head(30)
        st.bar_chart(volatility_df)

        #Detect trending categories based on recent performance compared to historical behavior
        st.subheader("Trending categories")
        trend_query="""
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
"""
        trend_df=run_query(trend_query)
        st.dataframe(trend_df)


