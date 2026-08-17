-- ============================================================
-- NovelMart 电商经营分析平台 - 数据导入脚本
-- 数据库名: ecommerce_analysis
-- 使用说明: 请先执行 01_create_database.sql 建库建表
-- 导入日期: 2026-07-31
-- ============================================================
-- 【重要配置说明】
-- 1. 请将以下 CSV_PATH 变量路径替换为你本机CSV文件所在目录
-- 2. 如果 MySQL 开启了 secure_file_priv 限制，请将CSV文件复制到该目录
--    查看方式: SHOW VARIABLES LIKE 'secure_file_priv';
-- 3. 如果遇到 LOAD DATA 权限错误（ERROR 1148），需开启 local_infile:
--    SET GLOBAL local_infile = 1; 或在连接时使用 --local-infile=1
-- 4. Windows 用户: 路径使用正斜杠 / 或双反斜杠 \\，如 'F:/data/users.csv'
--    Linux/Mac 用户: 使用标准路径如 '/home/user/data/users.csv'
-- 5. CSV 文件源目录: C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/
--    - users.csv, products.csv, orders.csv, order_items.csv, reviews.csv
-- ============================================================

-- 使用目标数据库
USE ecommerce_analysis;


-- ============================================================
-- 0. 会话配置：确保正确处理 UTF-8 中文字符
-- ============================================================
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET SESSION character_set_client      = utf8mb4;
SET SESSION character_set_connection  = utf8mb4;
SET SESSION character_set_results     = utf8mb4;
SET SESSION character_set_database    = utf8mb4;


-- ============================================================
-- 1. 导入前准备：禁用外键检查和索引（提升导入速度）
--    导入完成后重新启用并重建索引
-- ============================================================
SET FOREIGN_KEY_CHECKS = 0;
SET UNIQUE_CHECKS = 0;
SET AUTOCOMMIT = 0;

-- 临时禁用索引以加速大量数据导入
-- ALTER TABLE users      DISABLE KEYS;
-- ALTER TABLE products   DISABLE KEYS;
-- ALTER TABLE orders     DISABLE KEYS;
-- ALTER TABLE order_items DISABLE KEYS;
-- ALTER TABLE reviews    DISABLE KEYS;

SELECT '>>> 开始数据导入，请耐心等待...' AS status;


-- ============================================================
-- 2. 导入用户表 (users)
--    导入顺序第1步：用户表无外键依赖，最先导入
-- ============================================================
TRUNCATE TABLE users;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/users.csv'
-- 如果你的 secure_file_priv 限制了路径，请使用以下 LOCAL 语法：
-- LOAD DATA LOCAL INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/users.csv'
INTO TABLE users
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'           -- Windows 换行符; Linux/Mac 请改为 '\n'
IGNORE 1 ROWS                         -- 跳过 CSV 标题行
(user_id, username, real_name, email, phone, gender, age, province, city,
 registration_date, membership_level, total_orders, total_spent,
 avg_order_value, @first_order_date, @last_order_date, total_reviews,
 avg_rating_given, account_age_days)
-- 无订单用户的首次/最近下单日期在 CSV 中为空字符串，
-- 严格模式下 DATE 列不接受 ''，统一转为 NULL
SET first_order_date = NULLIF(@first_order_date, ''),
    last_order_date  = NULLIF(@last_order_date, '');

SELECT CONCAT('>>> 用户表导入完成: ', COUNT(*), ' 条记录') AS result FROM users;


-- ============================================================
-- 3. 导入商品表 (products)
--    导入顺序第2步：商品表无外键依赖（或仅自引用），在订单之前导入
-- ============================================================
TRUNCATE TABLE products;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/products.csv'
INTO TABLE products
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(product_id, product_name, category, subcategory, brand,
 price, cost_price, stock_quantity, sales_count,
 rating_avg, listing_date, status);

SELECT CONCAT('>>> 商品表导入完成: ', COUNT(*), ' 条记录') AS result FROM products;


-- ============================================================
-- 4. 导入订单表 (orders)
--    导入顺序第3步：依赖 users 表（user_id 外键）
--    ⚠️ 注意：CSV 列顺序与建表列顺序不同，故显式指定映射
--    CSV列序: order_id, user_id, order_date, payment_method,
--              shipping_method, shipping_cost, order_status,
--              shipping_province, shipping_city, total_amount,
--              discount_amount, actual_amount
-- ============================================================
TRUNCATE TABLE orders;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/orders.csv'
INTO TABLE orders
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(order_id, user_id, order_date, payment_method, shipping_method,
 shipping_cost, order_status, shipping_province, shipping_city,
 total_amount, discount_amount, actual_amount);

SELECT CONCAT('>>> 订单表导入完成: ', COUNT(*), ' 条记录') AS result FROM orders;


-- ============================================================
-- 5. 导入订单明细表 (order_items)
--    导入顺序第4步：同时依赖 orders (order_id) 和 products (product_id)
--    ⚠️ 导入前确保 orders 和 products 都已导入完成
-- ============================================================
TRUNCATE TABLE order_items;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/order_items.csv'
INTO TABLE order_items
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(item_id, order_id, product_id, quantity, unit_price, discount);

SELECT CONCAT('>>> 订单明细表导入完成: ', COUNT(*), ' 条记录') AS result FROM order_items;


-- ============================================================
-- 6. 导入评论表 (reviews)
--    导入顺序第5步：依赖 users, products, orders 三表
--    放在最后导入，确保所有外键引用有效
-- ============================================================
TRUNCATE TABLE reviews;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/reviews.csv'
INTO TABLE reviews
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(review_id, user_id, product_id, order_id, rating,
 review_text, review_date, @is_verified_purchase)
-- CSV 中 is_verified_purchase 为 Python 布尔值 True/False，
-- 直接写入 BOOLEAN(TINYINT) 列会被转成 0，这里需显式转换为 1/0
SET is_verified_purchase = IF(@is_verified_purchase IN ('True','TRUE','true','1'), 1, 0);

SELECT CONCAT('>>> 评论表导入完成: ', COUNT(*), ' 条记录') AS result FROM reviews;
-- 校验认证购买标记：正常应存在部分 1 值
SELECT '认证购买标记校验' AS check_name,
       SUM(is_verified_purchase = 1) AS verified_count,
       SUM(is_verified_purchase = 0) AS unverified_count
FROM reviews;


-- ============================================================
-- 7. 导入完成后恢复设置
-- ============================================================
SET FOREIGN_KEY_CHECKS = 1;
SET UNIQUE_CHECKS = 1;
COMMIT;
SET AUTOCOMMIT = 1;

-- 重新启用索引（如果之前禁用过）
-- ALTER TABLE users      ENABLE KEYS;
-- ALTER TABLE products   ENABLE KEYS;
-- ALTER TABLE orders     ENABLE KEYS;
-- ALTER TABLE order_items ENABLE KEYS;
-- ALTER TABLE reviews    ENABLE KEYS;

SELECT '>>> 数据导入全部完成，外键检查已恢复' AS status;


-- ============================================================
-- 8. 数据导入验证（Verification）
-- ============================================================

-- 8.1 各表行数统计
SELECT 'users'       AS table_name, COUNT(*) AS row_count FROM users
UNION ALL
SELECT 'products'    AS table_name, COUNT(*) AS row_count FROM products
UNION ALL
SELECT 'orders'      AS table_name, COUNT(*) AS row_count FROM orders
UNION ALL
SELECT 'order_items' AS table_name, COUNT(*) AS row_count FROM order_items
UNION ALL
SELECT 'reviews'     AS table_name, COUNT(*) AS row_count FROM reviews
ORDER BY table_name;


-- 8.2 外键完整性检查：检查 orders 中是否存在无效 user_id
SELECT 'orders→users FK 检查' AS check_name,
       COUNT(*) AS orphan_records
FROM orders o
LEFT JOIN users u ON o.user_id = u.user_id
WHERE u.user_id IS NULL;


-- 8.3 外键完整性检查：检查 order_items 中是否存在无效引用
SELECT 'order_items→orders FK 检查' AS check_name,
       COUNT(*) AS orphan_records
FROM order_items oi
LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;

SELECT 'order_items→products FK 检查' AS check_name,
       COUNT(*) AS orphan_records
FROM order_items oi
LEFT JOIN products p ON oi.product_id = p.product_id
WHERE p.product_id IS NULL;


-- 8.4 外键完整性检查：检查 reviews 的引用完整性
SELECT 'reviews→users FK 检查' AS check_name,
       COUNT(*) AS orphan_records
FROM reviews r
LEFT JOIN users u ON r.user_id = u.user_id
WHERE u.user_id IS NULL;

SELECT 'reviews→products FK 检查' AS check_name,
       COUNT(*) AS orphan_records
FROM reviews r
LEFT JOIN products p ON r.product_id = p.product_id
WHERE p.product_id IS NULL;

SELECT 'reviews→orders FK 检查' AS check_name,
       COUNT(*) AS orphan_records
FROM reviews r
LEFT JOIN orders o ON r.order_id = o.order_id
WHERE o.order_id IS NULL;


-- 8.5 抽样查看各表前5条数据，确认数据可读且中文无乱码
SELECT '--- users 表抽样 (前5条) ---' AS info;
SELECT user_id, username, real_name, gender, province, city, membership_level
FROM users LIMIT 5;

SELECT '--- products 表抽样 (前5条) ---' AS info;
SELECT product_id, product_name, category, subcategory, brand, price, status
FROM products LIMIT 5;

SELECT '--- orders 表抽样 (前5条) ---' AS info;
SELECT order_id, user_id, order_date, order_status, actual_amount, payment_method
FROM orders LIMIT 5;

SELECT '--- order_items 表抽样 (前5条) ---' AS info;
SELECT item_id, order_id, product_id, quantity, unit_price
FROM order_items LIMIT 5;

SELECT '--- reviews 表抽样 (前5条) ---' AS info;
SELECT review_id, user_id, product_id, rating, review_text, review_date
FROM reviews LIMIT 5;


-- 8.6 数值合理性检查：检查关键字段是否有异常值
SELECT '价格字段异常检查' AS check_name,
       SUM(CASE WHEN price < 0 OR price IS NULL THEN 1 ELSE 0 END) AS negative_or_null
FROM products;

SELECT '订单金额异常检查' AS check_name,
       SUM(CASE WHEN actual_amount < 0 THEN 1 ELSE 0 END) AS negative_amount
FROM orders;

SELECT '评分范围检查 (1-5)' AS check_name,
       SUM(CASE WHEN rating < 1 OR rating > 5 THEN 1 ELSE 0 END) AS out_of_range
FROM reviews;


-- 8.7 数据时间范围概览
SELECT '时间范围概览' AS info;
SELECT
    (SELECT MIN(registration_date) FROM users)  AS earliest_user_reg,
    (SELECT MAX(registration_date) FROM users)  AS latest_user_reg,
    (SELECT MIN(order_date) FROM orders)        AS earliest_order,
    (SELECT MAX(order_date) FROM orders)        AS latest_order,
    (SELECT MIN(review_date) FROM reviews)      AS earliest_review,
    (SELECT MAX(review_date) FROM reviews)      AS latest_review;


SELECT '>>> 数据导入验证全部完成！如果以上检查均无异常，即可开始数据分析。' AS final_message;
