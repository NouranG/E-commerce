use ecommerce;
WITH product_pairs AS (
    -- Co-purchases for frequency and cross-product association
    SELECT f1.product_key AS base_product,
           f2.product_key AS recommended_product,
           COUNT(*) AS frequency,
           MAX(d.full_date) AS last_purchase_date
    FROM fact f1
    JOIN fact f2
      ON f1.customer_key = f2.customer_key
     AND f1.product_key <> f2.product_key
    JOIN date d ON f2.date_key = d.date_key
    GROUP BY f1.product_key, f2.product_key
),
frequency_score AS (
    -- Normalize frequency for each base product
    SELECT base_product,
           recommended_product,
           frequency / MAX(frequency) OVER (PARTITION BY base_product) AS freq_score,
           DATEDIFF(CURRENT_DATE, last_purchase_date) AS days_since_last_purchase,
           1 - (DATEDIFF(CURRENT_DATE, last_purchase_date) / MAX(DATEDIFF(CURRENT_DATE, last_purchase_date)) 
                OVER (PARTITION BY base_product)) AS recency_score
    FROM product_pairs
),
category_score AS (
    SELECT f1.product_key AS base_product,
           f2.product_key AS recommended_product,
           CASE WHEN p1.product_category = p2.product_category THEN 1 ELSE 0.5 END AS cat_score
    FROM fact f1
    JOIN fact f2
      ON f1.customer_key = f2.customer_key
     AND f1.product_key <> f2.product_key
    JOIN products p1 ON f1.product_key = p1.product_key
    JOIN products p2 ON f2.product_key = p2.product_key
),
profit_score AS (
    SELECT product_key,
           AVG(profit_amount/net_amount) AS prof_score
    FROM fact
    GROUP BY product_key
),
combined_scores AS (
    SELECT f.base_product,
           f.recommended_product,
           -- Weighted sum of all factors
           0.25*f.freq_score + 
           0.20*f.recency_score + 
           0.15*c.cat_score + 
           0.20*f.freq_score +  -- cross-product association approximated as co-purchase frequency
           0.20*p.prof_score AS recommendation_score,
           -- Reason: factor with highest contribution
           CASE
               WHEN GREATEST(f.freq_score, f.recency_score, c.cat_score, p.prof_score) = f.freq_score THEN 'Frequency'
               WHEN GREATEST(f.freq_score, f.recency_score, c.cat_score, p.prof_score) = f.recency_score THEN 'Recency'
               WHEN GREATEST(f.freq_score, f.recency_score, c.cat_score, p.prof_score) = c.cat_score THEN 'Category similarity'
               ELSE 'Profitability'
           END AS reason
    FROM frequency_score f
    JOIN category_score c
      ON f.base_product = c.base_product
     AND f.recommended_product = c.recommended_product
    JOIN profit_score p
      ON f.recommended_product = p.product_key
),
ranked_recs AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY base_product ORDER BY recommendation_score DESC) AS rnk
    FROM combined_scores
)
SELECT 
    p.product_name AS base_product_name,
    GROUP_CONCAT(CONCAT(r.recommended_product, ' (', r.reason, ':', ROUND(r.recommendation_score,2), ')') 
                 ORDER BY r.recommendation_score DESC 
                 SEPARATOR ', ') AS top_4_recommended
FROM ranked_recs r
JOIN products p
  ON r.base_product = p.product_key
WHERE r.rnk <= 4
GROUP BY p.product_name
ORDER BY p.product_name;


