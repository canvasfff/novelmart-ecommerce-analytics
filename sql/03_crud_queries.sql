-- ============================================================
-- Olist 电商经营分析平台 - CRUD 增删改查与业务分析 SQL
-- 数据库名: olist_ecommerce
-- 使用说明: 先执行 01_create_database.sql 和 02_data_import.sql
-- ============================================================
-- 本文件包含:
--   A. INSERT 插入（新客户/卖家/商品/订单/明细/支付/评论）
--   B. SELECT 查询（CRUD + 业务分析 30+ 条）
--   C. UPDATE 更新
--   D. DELETE 删除
--   E. 存储过程调用
-- ============================================================

USE olist_ecommerce;
SET NAMES utf8mb4;

-- 动态参考日期
SET @ref_date = (SELECT MAX(order_purchase_timestamp) FROM orders);

-- ################################################################
-- A. INSERT 插入操作
-- ################################################################

-- A-1. 插入新客户
INSERT INTO customers (customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state)
VALUES ('TEST-CUST-000001', 'TEST-UNIQUE-000001', 10000, 'test city', 'SP');
SELECT * FROM customers WHERE customer_id = 'TEST-CUST-000001';

-- A-2. 插入新卖家
INSERT INTO sellers (seller_id, seller_zip_code_prefix, seller_city, seller_state)
VALUES ('TEST-SELLER-000001', 20000, 'test seller city', 'RJ');
SELECT * FROM sellers WHERE seller_id = 'TEST-SELLER-000001';

-- A-3. 插入新商品（带品类英文翻译）
INSERT INTO products (
    product_id, product_category_name, product_category_name_english,
    product_name_lenght, product_description_lenght, product_photos_qty,
    product_weight_g, product_length_cm, product_height_cm, product_width_cm,
    order_count, quantity_sold, price_sum, freight_sum, revenue, avg_price, review_count
) VALUES (
    'TEST-PRODUCT-000001', 'test_category', 'test_category',
    20, 100, 3, 500, 20, 10, 15,
    0, 0, 0, 0, 0, 0, 0
);
SELECT * FROM products WHERE product_id = 'TEST-PRODUCT-000001';

-- A-4. 插入新订单（事务：订单 + 明细 + 支付）
START TRANSACTION;

INSERT INTO orders (
    order_id, customer_id, customer_unique_id, customer_zip_code_prefix,
    customer_city, customer_state, order_status, order_status_cn,
    order_purchase_timestamp, order_approved_at,
    order_delivered_carrier_date, order_delivered_customer_date,
    order_estimated_delivery_date,
    payment_count, payment_installments, payment_value, payment_type,
    item_count, total_price, total_freight, total_order_value,
    delivery_days, estimated_delivery_days, delivery_delay_days, is_on_time
) VALUES (
    'TEST-ORDER-000001', 'TEST-CUST-000001', 'TEST-UNIQUE-000001', 10000,
    'test city', 'SP', 'delivered', '已送达',
    '2018-10-01 10:00:00', '2018-10-01 10:05:00',
    '2018-10-02 09:00:00', '2018-10-05 09:00:00',
    '2018-10-10 00:00:00',
    1, 1, 199.90, 'credit_card',
    1, 179.90, 20.00, 199.90,
    4.00, 9.00, -5.00, 1
);

INSERT INTO order_items (order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value)
VALUES ('TEST-ORDER-000001', 1, 'TEST-PRODUCT-000001', 'TEST-SELLER-000001', '2018-10-02 00:00:00', 179.90, 20.00);

INSERT INTO order_payments (order_id, payment_sequential, payment_type, payment_installments, payment_value)
VALUES ('TEST-ORDER-000001', 1, 'credit_card', 1, 199.90);

INSERT INTO order_reviews (review_id, order_id, review_score, review_comment_title, review_comment_message, review_creation_date, review_answer_timestamp)
VALUES ('TEST-REVIEW-000001', 'TEST-ORDER-000001', 5, 'Great', 'Test review message', '2018-10-06 12:00:00', '2018-10-06 12:30:00');

COMMIT;

-- 验证新订单
SELECT o.order_id, o.order_status, o.payment_value, oi.product_id, p.payment_type, r.review_score
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN order_payments p ON o.order_id = p.order_id
JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_id = 'TEST-ORDER-000001';

-- ################################################################
-- B. SELECT 查询分析
-- ################################################################

-- B-1. 核心 KPI
SELECT
    COUNT(*) AS total_orders,
    SUM(CASE WHEN order_status IN ('delivered','shipped','invoiced','processing','created','approved')
             THEN 1 ELSE 0 END) AS valid_orders,
    ROUND(SUM(CASE WHEN order_status IN ('delivered','shipped','invoiced','processing','created','approved')
                   THEN payment_value ELSE 0 END), 2) AS valid_revenue,
    ROUND(AVG(CASE WHEN order_status IN ('delivered','shipped','invoiced','processing','created','approved')
                   THEN payment_value END), 2) AS avg_order_value
FROM orders;

-- B-2. 月度销售趋势
SELECT
    DATE_FORMAT(order_purchase_timestamp, '%Y-%m') AS month,
    COUNT(DISTINCT order_id) AS order_count,
    COUNT(DISTINCT customer_unique_id) AS customer_count,
    ROUND(SUM(payment_value), 2) AS revenue,
    ROUND(AVG(payment_value), 2) AS avg_order_value
FROM orders
WHERE order_status IN ('delivered','shipped','invoiced','processing','created','approved')
GROUP BY DATE_FORMAT(order_purchase_timestamp, '%Y-%m')
ORDER BY month;

-- B-3. 品类销售排行
SELECT
    p.product_category_name_english,
    COUNT(DISTINCT oi.order_id) AS order_count,
    SUM(oi.price) AS product_revenue,
    SUM(oi.freight_value) AS freight_revenue,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS total_revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status IN ('delivered','shipped','invoiced','processing','created','approved')
GROUP BY p.product_category_name_english
ORDER BY total_revenue DESC
LIMIT 15;

-- B-4. 州销售排行
SELECT
    customer_state,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(payment_value), 2) AS revenue,
    ROUND(AVG(payment_value), 2) AS avg_order_value
FROM orders
WHERE order_status IN ('delivered','shipped','invoiced','processing','created','approved')
GROUP BY customer_state
ORDER BY revenue DESC;

-- B-5. 支付方式分布
SELECT
    payment_type,
    COUNT(*) AS payment_count,
    ROUND(SUM(payment_value), 2) AS payment_amount,
    ROUND(AVG(payment_installments), 2) AS avg_installments
FROM order_payments
GROUP BY payment_type
ORDER BY payment_count DESC;

-- B-6. 评分分布
SELECT
    review_score,
    COUNT(*) AS review_count,
    ROUND(COUNT(*) / (SELECT COUNT(*) FROM order_reviews) * 100, 2) AS pct
FROM order_reviews
GROUP BY review_score
ORDER BY review_score;

-- B-7. 平均评分与好评率
SELECT
    ROUND(AVG(review_score), 2) AS avg_score,
    ROUND(SUM(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS good_rate_pct
FROM order_reviews;

-- B-8. 商品 Top10（按营收）
SELECT
    p.product_id,
    p.product_category_name_english,
    p.quantity_sold,
    ROUND(p.revenue, 2) AS revenue,
    ROUND(p.avg_price, 2) AS avg_price,
    p.review_count,
    p.avg_review_score
FROM products p
ORDER BY p.revenue DESC
LIMIT 10;

-- B-9. 卖家 Top10（按销售额）
SELECT
    oi.seller_id,
    COUNT(DISTINCT oi.order_id) AS order_count,
    ROUND(SUM(oi.price), 2) AS product_revenue,
    ROUND(SUM(oi.freight_value), 2) AS freight_revenue,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS total_revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status IN ('delivered','shipped','invoiced','processing','created','approved')
GROUP BY oi.seller_id
ORDER BY total_revenue DESC
LIMIT 10;

-- B-10. 复购客户分析
SELECT
    customer_unique_id,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(payment_value), 2) AS total_spent
FROM orders
WHERE order_status IN ('delivered','shipped','invoiced','processing','created','approved')
GROUP BY customer_unique_id
HAVING COUNT(DISTINCT order_id) >= 2
ORDER BY order_count DESC, total_spent DESC
LIMIT 10;

-- B-11. 复购率
SELECT
    ROUND(SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS repeat_rate_pct
FROM (
    SELECT customer_unique_id, COUNT(DISTINCT order_id) AS order_count
    FROM orders
    WHERE order_status IN ('delivered','shipped','invoiced','processing','created','approved')
    GROUP BY customer_unique_id
) t;

-- B-12. 配送时效表现
SELECT
    customer_state,
    COUNT(*) AS delivered_orders,
    ROUND(AVG(delivery_days), 2) AS avg_delivery_days,
    ROUND(AVG(delivery_delay_days), 2) AS avg_delay_days,
    ROUND(AVG(is_on_time) * 100, 2) AS on_time_rate_pct
FROM orders
WHERE order_status = 'delivered' AND delivery_days IS NOT NULL
GROUP BY customer_state
ORDER BY delivered_orders DESC;

-- B-13. 准时率总览
SELECT
    ROUND(AVG(is_on_time) * 100, 2) AS overall_on_time_pct,
    ROUND(AVG(delivery_days), 2) AS avg_delivery_days
FROM orders
WHERE order_status = 'delivered';

-- B-14. 客户价值视图
SELECT * FROM v_customer_summary
ORDER BY total_payment_value DESC
LIMIT 10;

-- B-15. 商品表现视图
SELECT * FROM v_product_performance
LIMIT 10;

-- B-16. 订单事实视图（月度销售）
SELECT
    DATE_FORMAT(order_purchase_timestamp, '%Y-%m') AS month,
    COUNT(*) AS order_count,
    ROUND(SUM(payment_value), 2) AS revenue,
    ROUND(AVG(payment_value), 2) AS avg_order_value
FROM v_order_facts
GROUP BY month
ORDER BY month;

-- B-17. 高价值客户（RFM 存储过程结果）
CALL sp_calculate_rfm();
SELECT rfm_segment, COUNT(*) AS customer_count, ROUND(AVG(monetary), 2) AS avg_monetary
FROM rfm_analysis
GROUP BY rfm_segment
ORDER BY avg_monetary DESC;

-- B-18. 品类-评分关系（通过订单明细关联评论）
SELECT
    p.product_category_name_english,
    COUNT(DISTINCT r.review_id) AS review_count,
    ROUND(AVG(r.review_score), 2) AS avg_score,
    ROUND(SUM(CASE WHEN r.review_score >= 4 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS good_rate_pct
FROM order_reviews r
JOIN orders o ON r.order_id = o.order_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_category_name_english
HAVING review_count >= 50
ORDER BY avg_score DESC
LIMIT 15;

-- B-19. 城市 Top10
SELECT
    customer_state,
    customer_city,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(payment_value), 2) AS revenue
FROM orders
WHERE order_status IN ('delivered','shipped','invoiced','processing','created','approved')
GROUP BY customer_state, customer_city
ORDER BY revenue DESC
LIMIT 10;

-- B-20. 窗口函数：月度营收环比
WITH monthly AS (
    SELECT
        DATE_FORMAT(order_purchase_timestamp, '%Y-%m') AS month,
        SUM(payment_value) AS revenue
    FROM orders
    WHERE order_status IN ('delivered','shipped','invoiced','processing','created','approved')
    GROUP BY month
)
SELECT
    month,
    ROUND(revenue, 2) AS revenue,
    ROUND(LAG(revenue) OVER (ORDER BY month), 2) AS prev_revenue,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month) * 100, 2) AS mom_pct
FROM monthly
ORDER BY month;

-- B-21. 订单明细行数分布
SELECT
    item_count,
    COUNT(*) AS order_count
FROM orders
WHERE order_status IN ('delivered','shipped','invoiced','processing','created','approved')
GROUP BY item_count
ORDER BY item_count;

-- ################################################################
-- C. UPDATE 更新操作
-- ################################################################

-- C-1. 更新订单状态（示例：将测试订单改为已取消）
UPDATE orders SET order_status = 'canceled', order_status_cn = '已取消'
WHERE order_id = 'TEST-ORDER-000001';

-- C-2. 更新商品品类英文名
UPDATE products
SET product_category_name_english = 'test_category_updated'
WHERE product_id = 'TEST-PRODUCT-000001';

-- C-3. 更新支付方式
UPDATE order_payments SET payment_type = 'boleto'
WHERE order_id = 'TEST-ORDER-000001' AND payment_sequential = 1;

-- C-4. 更新评论内容
UPDATE order_reviews
SET review_comment_message = 'Updated test review'
WHERE review_id = 'TEST-REVIEW-000001';

-- C-5. 更新客户地址
UPDATE customers
SET customer_city = 'updated city', customer_state = 'MG'
WHERE customer_id = 'TEST-CUST-000001';

-- 验证更新
SELECT order_id, order_status FROM orders WHERE order_id = 'TEST-ORDER-000001';
SELECT product_id, product_category_name_english FROM products WHERE product_id = 'TEST-PRODUCT-000001';

-- ################################################################
-- D. DELETE 删除操作
-- ################################################################

-- D-1. 删除测试评论
DELETE FROM order_reviews WHERE review_id = 'TEST-REVIEW-000001';

-- D-2. 删除测试订单关联明细/支付/订单（注意外键顺序）
DELETE FROM order_payments WHERE order_id = 'TEST-ORDER-000001';
DELETE FROM order_items WHERE order_id = 'TEST-ORDER-000001';
DELETE FROM orders WHERE order_id = 'TEST-ORDER-000001';

-- D-3. 删除测试商品/卖家/客户
DELETE FROM products WHERE product_id = 'TEST-PRODUCT-000001';
DELETE FROM sellers WHERE seller_id = 'TEST-SELLER-000001';
DELETE FROM customers WHERE customer_id = 'TEST-CUST-000001';

-- 验证清理
SELECT COUNT(*) AS test_orders_remaining FROM orders WHERE order_id LIKE 'TEST-%';
SELECT COUNT(*) AS test_customers_remaining FROM customers WHERE customer_id LIKE 'TEST-%';

-- ################################################################
-- E. 常用分析结果导出（用于 Tableau/报告）
-- ################################################################

-- E-1. 月度营收（导出 CSV 用）
SELECT month, revenue FROM (
    SELECT
        DATE_FORMAT(order_purchase_timestamp, '%Y-%m') AS month,
        ROUND(SUM(payment_value), 2) AS revenue
    FROM orders
    WHERE order_status IN ('delivered','shipped','invoiced','processing','created','approved')
    GROUP BY month
) t ORDER BY month;

-- E-2. 州级销售（地图用）
SELECT
    customer_state,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(payment_value), 2) AS revenue
FROM orders
WHERE order_status IN ('delivered','shipped','invoiced','processing','created','approved')
GROUP BY customer_state
ORDER BY revenue DESC;

-- E-3. 商品表现（Tableau 商品分析）
SELECT * FROM v_product_performance LIMIT 1000;

-- E-4. RFM 明细（Tableau 用户分析）
CALL sp_calculate_rfm();
SELECT * FROM rfm_analysis LIMIT 1000;
