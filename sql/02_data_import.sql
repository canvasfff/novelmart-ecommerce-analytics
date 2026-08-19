-- ============================================================
-- Olist 电商经营分析平台 - 数据导入脚本
-- 数据库名: olist_ecommerce
-- 使用说明:
--   1. 先执行 01_create_database.sql 建库建表
--   2. 将下面的 CSV_PATH 替换为 data/processed 在本机的绝对路径
--   3. 如果 MySQL 开启 secure_file_priv，请将 CSV 放到该目录或使用 LOCAL
--   4. Windows 路径示例: 'F:/database/bigdata/开源项目/ecommerce-analysis/data/processed/'
-- ============================================================

USE olist_ecommerce;

SET NAMES utf8mb4;
SET SESSION character_set_client      = utf8mb4;
SET SESSION character_set_connection  = utf8mb4;
SET SESSION character_set_results     = utf8mb4;

-- 导入前关闭外键检查提升速度
SET FOREIGN_KEY_CHECKS = 0;
SET UNIQUE_CHECKS = 0;

-- 注意：MySQL 路径使用正斜杠；请将所有
-- 'C:/your_project_path/ecommerce-analysis/data/processed/'
-- 替换为本机 data/processed 实际路径。

-- ============================================================
-- 1. 导入品类翻译表
-- ============================================================
TRUNCATE TABLE category_translation;
LOAD DATA INFILE 'C:/your_project_path/ecommerce-analysis/data/processed/category_translation.csv'
-- 如果使用 LOCAL: LOAD DATA LOCAL INFILE 'C:/your_project_path/...'
INTO TABLE category_translation
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'            -- Windows; Linux/Mac 改 '\n'
IGNORE 1 ROWS
(product_category_name, product_category_name_english);
SELECT CONCAT('>>> category_translation: ', COUNT(*)) AS result FROM category_translation;

-- ============================================================
-- 2. 导入客户表
-- ============================================================
TRUNCATE TABLE customers;
LOAD DATA INFILE 'C:/your_project_path/ecommerce-analysis/data/processed/customers.csv'
INTO TABLE customers
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state);
SELECT CONCAT('>>> customers: ', COUNT(*)) AS result FROM customers;

-- ============================================================
-- 3. 导入卖家表
-- ============================================================
TRUNCATE TABLE sellers;
LOAD DATA INFILE 'C:/your_project_path/ecommerce-analysis/data/processed/sellers.csv'
INTO TABLE sellers
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(seller_id, seller_zip_code_prefix, seller_city, seller_state);
SELECT CONCAT('>>> sellers: ', COUNT(*)) AS result FROM sellers;

-- ============================================================
-- 4. 导入商品表
-- ============================================================
TRUNCATE TABLE products;
LOAD DATA INFILE 'C:/your_project_path/ecommerce-analysis/data/processed/products.csv'
INTO TABLE products
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(product_id, product_category_name, product_name_lenght, product_description_lenght,
 product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm,
 product_category_name_english, order_count, quantity_sold, price_sum, freight_sum,
 revenue, avg_price, review_count, avg_review_score);
SELECT CONCAT('>>> products: ', COUNT(*)) AS result FROM products;

-- ============================================================
-- 5. 导入地理表（邮编聚合）
-- ============================================================
TRUNCATE TABLE geolocation;
LOAD DATA INFILE 'C:/your_project_path/ecommerce-analysis/data/processed/geolocation_zip.csv'
INTO TABLE geolocation
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state);
SELECT CONCAT('>>> geolocation: ', COUNT(*)) AS result FROM geolocation;

-- ============================================================
-- 6. 导入客户聚合表
-- ============================================================
TRUNCATE TABLE customers_agg;
LOAD DATA INFILE 'C:/your_project_path/ecommerce-analysis/data/processed/customers_agg.csv'
INTO TABLE customers_agg
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(customer_unique_id, @first_order_date, @last_order_date, order_count, total_payment_value,
 avg_order_value, customer_zip_code_prefix, customer_city, customer_state, review_count,
 @avg_review_score)
SET first_order_date = NULLIF(@first_order_date, ''),
    last_order_date  = NULLIF(@last_order_date, ''),
    avg_review_score = NULLIF(@avg_review_score, '');
SELECT CONCAT('>>> customers_agg: ', COUNT(*)) AS result FROM customers_agg;

-- ============================================================
-- 7. 导入订单表
-- ============================================================
TRUNCATE TABLE orders;
LOAD DATA INFILE 'C:/your_project_path/ecommerce-analysis/data/processed/orders.csv'
INTO TABLE orders
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(order_id, customer_id, order_status, order_purchase_timestamp, @order_approved_at,
 @order_delivered_carrier_date, @order_delivered_customer_date, order_estimated_delivery_date,
 order_status_cn, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state,
 payment_count, payment_installments, payment_value, payment_type, item_count,
 total_price, total_freight, total_order_value, @delivery_days, @estimated_delivery_days,
 @delivery_delay_days, @is_on_time)
SET order_approved_at = NULLIF(@order_approved_at, ''),
    order_delivered_carrier_date = NULLIF(@order_delivered_carrier_date, ''),
    order_delivered_customer_date = NULLIF(@order_delivered_customer_date, ''),
    delivery_days = NULLIF(@delivery_days, ''),
    estimated_delivery_days = NULLIF(@estimated_delivery_days, ''),
    delivery_delay_days = NULLIF(@delivery_delay_days, ''),
    is_on_time = NULLIF(@is_on_time, '');
SELECT CONCAT('>>> orders: ', COUNT(*)) AS result FROM orders;

-- ============================================================
-- 8. 导入订单明细表
-- ============================================================
TRUNCATE TABLE order_items;
LOAD DATA INFILE 'C:/your_project_path/ecommerce-analysis/data/processed/order_items.csv'
INTO TABLE order_items
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value);
SELECT CONCAT('>>> order_items: ', COUNT(*)) AS result FROM order_items;

-- ============================================================
-- 9. 导入订单支付表
-- ============================================================
TRUNCATE TABLE order_payments;
LOAD DATA INFILE 'C:/your_project_path/ecommerce-analysis/data/processed/payments.csv'
INTO TABLE order_payments
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(order_id, payment_sequential, payment_type, payment_installments, payment_value);
SELECT CONCAT('>>> order_payments: ', COUNT(*)) AS result FROM order_payments;

-- ============================================================
-- 10. 导入订单评论表
-- ============================================================
TRUNCATE TABLE order_reviews;
LOAD DATA INFILE 'C:/your_project_path/ecommerce-analysis/data/processed/reviews.csv'
INTO TABLE order_reviews
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(review_id, order_id, review_score, review_comment_title, review_comment_message,
 review_creation_date, @review_answer_timestamp)
SET review_answer_timestamp = NULLIF(@review_answer_timestamp, '');
SELECT CONCAT('>>> order_reviews: ', COUNT(*)) AS result FROM order_reviews;

-- ============================================================
-- 11. 恢复设置
-- ============================================================
SET FOREIGN_KEY_CHECKS = 1;
SET UNIQUE_CHECKS = 1;

-- ============================================================
-- 12. 导入验证
-- ============================================================
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL SELECT 'customers_agg', COUNT(*) FROM customers_agg
UNION ALL SELECT 'sellers', COUNT(*) FROM sellers
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'geolocation', COUNT(*) FROM geolocation
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'order_payments', COUNT(*) FROM order_payments
UNION ALL SELECT 'order_reviews', COUNT(*) FROM order_reviews
ORDER BY table_name;
