-- ============================================================
-- Olist 电商经营分析平台 - MySQL 数据库建库建表脚本
-- 数据库名: olist_ecommerce
-- 数据集: Olist Brazilian E-Commerce Public Dataset
-- 创建日期: 2026-08-19
-- ============================================================

-- 1. 创建数据库
DROP DATABASE IF EXISTS olist_ecommerce;
CREATE DATABASE olist_ecommerce
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE olist_ecommerce;

-- ============================================================
-- 2. 基础维度表
-- ============================================================

-- 2.1 品类翻译表
CREATE TABLE category_translation (
    product_category_name          VARCHAR(100) PRIMARY KEY COMMENT '品类名称（葡萄牙语）',
    product_category_name_english  VARCHAR(100) NOT NULL COMMENT '品类名称（英文）'
) ENGINE=InnoDB COMMENT='Olist品类翻译表';

-- 2.2 客户表（订单级客户）
CREATE TABLE customers (
    customer_id             VARCHAR(50) PRIMARY KEY COMMENT '客户ID（订单级）',
    customer_unique_id      VARCHAR(50) NOT NULL COMMENT '客户唯一ID',
    customer_zip_code_prefix INT COMMENT '客户邮编前缀',
    customer_city           VARCHAR(100) COMMENT '客户城市',
    customer_state          CHAR(2) COMMENT '客户州',
    INDEX idx_unique_customer (customer_unique_id),
    INDEX idx_state (customer_state),
    INDEX idx_zip (customer_zip_code_prefix)
) ENGINE=InnoDB COMMENT='Olist客户表';

-- 2.3 客户聚合表（唯一客户维度，供 RFM/价值分析）
CREATE TABLE customers_agg (
    customer_unique_id       VARCHAR(50) PRIMARY KEY COMMENT '客户唯一ID',
    first_order_date         DATETIME COMMENT '首次下单时间',
    last_order_date          DATETIME COMMENT '最近下单时间',
    order_count              INT DEFAULT 0 COMMENT '有效订单数',
    total_payment_value      DECIMAL(12,2) DEFAULT 0.00 COMMENT '累计支付金额',
    avg_order_value          DECIMAL(10,2) DEFAULT 0.00 COMMENT '平均客单价',
    customer_zip_code_prefix INT COMMENT '客户邮编前缀',
    customer_city            VARCHAR(100) COMMENT '客户城市',
    customer_state           CHAR(2) COMMENT '客户州',
    review_count             INT DEFAULT 0 COMMENT '评论数',
    avg_review_score         DECIMAL(3,2) COMMENT '平均评分',
    INDEX idx_cust_state (customer_state)
) ENGINE=InnoDB COMMENT='客户聚合汇总表';

-- 2.4 卖家表
CREATE TABLE sellers (
    seller_id               VARCHAR(50) PRIMARY KEY COMMENT '卖家ID',
    seller_zip_code_prefix  INT COMMENT '卖家邮编前缀',
    seller_city             VARCHAR(100) COMMENT '卖家城市',
    seller_state            CHAR(2) COMMENT '卖家州',
    INDEX idx_seller_state (seller_state)
) ENGINE=InnoDB COMMENT='Olist卖家表';

-- 2.5 商品表（含商品表现聚合字段）
CREATE TABLE products (
    product_id                   VARCHAR(50) PRIMARY KEY COMMENT '商品ID',
    product_category_name        VARCHAR(100) COMMENT '商品品类（葡萄牙语）',
    product_category_name_english VARCHAR(100) COMMENT '商品品类（英文）',
    product_name_lenght          INT COMMENT '商品名称长度',
    product_description_lenght   INT COMMENT '商品描述长度',
    product_photos_qty           INT COMMENT '商品图片数量',
    product_weight_g             INT COMMENT '商品重量（克）',
    product_length_cm            INT COMMENT '商品长度（厘米）',
    product_height_cm            INT COMMENT '商品高度（厘米）',
    product_width_cm             INT COMMENT '商品宽度（厘米）',
    order_count                  INT DEFAULT 0 COMMENT '有效订单数',
    quantity_sold                INT DEFAULT 0 COMMENT '销售件数（明细行数）',
    price_sum                    DECIMAL(12,2) DEFAULT 0.00 COMMENT '商品销售额',
    freight_sum                  DECIMAL(12,2) DEFAULT 0.00 COMMENT '运费总额',
    revenue                      DECIMAL(12,2) DEFAULT 0.00 COMMENT '商品+运费总营收',
    avg_price                    DECIMAL(10,2) DEFAULT 0.00 COMMENT '平均售价',
    review_count                 INT DEFAULT 0 COMMENT '关联评论数',
    avg_review_score             DECIMAL(3,2) COMMENT '平均评论评分',
    INDEX idx_category (product_category_name),
    INDEX idx_category_en (product_category_name_english),
    INDEX idx_revenue (revenue)
) ENGINE=InnoDB COMMENT='Olist商品表';

-- 2.6 地理表（邮编前缀聚合）
CREATE TABLE geolocation (
    geolocation_zip_code_prefix INT NOT NULL COMMENT '邮编前缀',
    geolocation_lat             DECIMAL(10,7) COMMENT '纬度',
    geolocation_lng             DECIMAL(10,7) COMMENT '经度',
    geolocation_city            VARCHAR(100) COMMENT '城市',
    geolocation_state           CHAR(2) COMMENT '州',
    KEY idx_geo_zip (geolocation_zip_code_prefix),
    KEY idx_geo_state (geolocation_state)
) ENGINE=InnoDB COMMENT='Olist地理信息表（按邮编聚合）';

-- ============================================================
-- 3. 事实表
-- ============================================================

-- 3.1 订单表
CREATE TABLE orders (
    order_id                        VARCHAR(50) PRIMARY KEY COMMENT '订单ID',
    customer_id                     VARCHAR(50) NOT NULL COMMENT '客户ID',
    customer_unique_id              VARCHAR(50) COMMENT '客户唯一ID',
    customer_zip_code_prefix        INT COMMENT '客户邮编前缀',
    customer_city                   VARCHAR(100) COMMENT '客户城市',
    customer_state                  CHAR(2) COMMENT '客户州',
    order_status                    VARCHAR(20) COMMENT '订单状态',
    order_status_cn                 VARCHAR(20) COMMENT '订单状态中文',
    order_purchase_timestamp        DATETIME COMMENT '下单时间',
    order_approved_at               DATETIME COMMENT '支付/审批时间',
    order_delivered_carrier_date    DATETIME COMMENT '交承运商时间',
    order_delivered_customer_date   DATETIME COMMENT '送达客户时间',
    order_estimated_delivery_date   DATETIME COMMENT '预计送达时间',
    payment_count                   INT DEFAULT 0 COMMENT '支付笔数',
    payment_installments            INT DEFAULT 0 COMMENT '最大分期期数',
    payment_value                   DECIMAL(12,2) DEFAULT 0.00 COMMENT '订单支付总额',
    payment_type                    VARCHAR(20) COMMENT '主支付方式',
    item_count                      INT DEFAULT 0 COMMENT '商品明细行数',
    total_price                     DECIMAL(12,2) DEFAULT 0.00 COMMENT '商品总额',
    total_freight                   DECIMAL(12,2) DEFAULT 0.00 COMMENT '运费总额',
    total_order_value               DECIMAL(12,2) DEFAULT 0.00 COMMENT '订单总价值',
    delivery_days                   DECIMAL(8,2) COMMENT '实际送达天数',
    estimated_delivery_days         DECIMAL(8,2) COMMENT '预计送达天数',
    delivery_delay_days             DECIMAL(8,2) COMMENT '送达延迟天数',
    is_on_time                      TINYINT(1) COMMENT '是否准时送达',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    INDEX idx_customer (customer_id),
    INDEX idx_unique_customer (customer_unique_id),
    INDEX idx_status (order_status),
    INDEX idx_purchase_time (order_purchase_timestamp),
    INDEX idx_state (customer_state)
) ENGINE=InnoDB COMMENT='Olist订单事实表';

-- 3.2 订单明细表
CREATE TABLE order_items (
    order_id            VARCHAR(50) NOT NULL COMMENT '订单ID',
    order_item_id       INT NOT NULL COMMENT '订单内商品序号',
    product_id          VARCHAR(50) NOT NULL COMMENT '商品ID',
    seller_id           VARCHAR(50) NOT NULL COMMENT '卖家ID',
    shipping_limit_date DATETIME COMMENT '卖家发货截止时间',
    price               DECIMAL(10,2) DEFAULT 0.00 COMMENT '商品单价',
    freight_value       DECIMAL(10,2) DEFAULT 0.00 COMMENT '该商品运费',
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id),
    INDEX idx_product (product_id),
    INDEX idx_seller (seller_id)
) ENGINE=InnoDB COMMENT='Olist订单明细表';

-- 3.3 支付表
CREATE TABLE order_payments (
    order_id             VARCHAR(50) NOT NULL COMMENT '订单ID',
    payment_sequential   INT NOT NULL COMMENT '支付序号',
    payment_type         VARCHAR(20) COMMENT '支付方式',
    payment_installments INT DEFAULT 0 COMMENT '分期期数',
    payment_value        DECIMAL(10,2) DEFAULT 0.00 COMMENT '支付金额',
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    INDEX idx_payment_type (payment_type)
) ENGINE=InnoDB COMMENT='Olist订单支付表';

-- 3.4 评论表
CREATE TABLE order_reviews (
    review_id                VARCHAR(50) PRIMARY KEY COMMENT '评论ID',
    order_id                 VARCHAR(50) NOT NULL COMMENT '订单ID',
    review_score             TINYINT COMMENT '评分(1-5)',
    review_comment_title     VARCHAR(255) COMMENT '评论标题',
    review_comment_message   TEXT COMMENT '评论内容',
    review_creation_date     DATETIME COMMENT '评论创建时间',
    review_answer_timestamp  DATETIME COMMENT '评论回复时间',
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    INDEX idx_order (order_id),
    INDEX idx_score (review_score),
    INDEX idx_review_date (review_creation_date)
) ENGINE=InnoDB COMMENT='Olist订单评论表';

-- ============================================================
-- 4. 分析视图
-- ============================================================

-- 4.1 订单级分析视图：订单 + 客户 + 商品明细金额
CREATE VIEW v_order_facts AS
SELECT
    o.order_id,
    o.customer_unique_id,
    o.customer_city,
    o.customer_state,
    o.order_status,
    o.order_status_cn,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    o.payment_value,
    o.payment_type,
    o.item_count,
    o.total_price,
    o.total_freight,
    o.total_order_value,
    o.delivery_days,
    o.delivery_delay_days,
    o.is_on_time
FROM orders o
WHERE o.order_status IN ('delivered','shipped','invoiced','processing','created','approved');

-- 4.2 商品销售表现视图
CREATE VIEW v_product_performance AS
SELECT
    p.product_id,
    p.product_category_name,
    p.product_category_name_english,
    p.product_weight_g,
    p.quantity_sold,
    p.order_count,
    p.price_sum,
    p.freight_sum,
    p.revenue,
    p.avg_price,
    p.review_count,
    p.avg_review_score,
    ROUND(p.revenue / NULLIF(p.quantity_sold, 0), 2) AS revenue_per_unit,
    ROUND(p.freight_sum / NULLIF(p.revenue, 0) * 100, 2) AS freight_rate_pct
FROM products p;

-- 4.3 客户价值视图
CREATE VIEW v_customer_summary AS
SELECT
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    c.first_order_date,
    c.last_order_date,
    c.order_count,
    c.total_payment_value,
    c.avg_order_value,
    c.review_count,
    c.avg_review_score,
    ROUND(c.total_payment_value / NULLIF(DATEDIFF(c.last_order_date, c.first_order_date) + 1, 0), 2) AS daily_value
FROM customers_agg c;

-- ============================================================
-- 5. 存储过程：RFM 客户分群
-- ============================================================
DELIMITER //

CREATE PROCEDURE sp_calculate_rfm()
BEGIN
    DECLARE ref_date DATETIME;
    SET ref_date = (SELECT MAX(order_purchase_timestamp) FROM orders);

    DROP TABLE IF EXISTS rfm_analysis;
    CREATE TABLE rfm_analysis AS
    SELECT
        c.customer_unique_id,
        c.customer_state,
        c.customer_city,
        DATEDIFF(ref_date, MAX(o.order_purchase_timestamp)) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(o.payment_value), 2) AS monetary,
        CASE
            WHEN DATEDIFF(ref_date, MAX(o.order_purchase_timestamp)) <= 90 THEN 4
            WHEN DATEDIFF(ref_date, MAX(o.order_purchase_timestamp)) <= 180 THEN 3
            WHEN DATEDIFF(ref_date, MAX(o.order_purchase_timestamp)) <= 365 THEN 2
            ELSE 1
        END AS r_score,
        CASE
            WHEN COUNT(DISTINCT o.order_id) >= 5 THEN 4
            WHEN COUNT(DISTINCT o.order_id) >= 3 THEN 3
            WHEN COUNT(DISTINCT o.order_id) >= 2 THEN 2
            ELSE 1
        END AS f_score,
        CASE
            WHEN SUM(o.payment_value) >= 1000 THEN 4
            WHEN SUM(o.payment_value) >= 500 THEN 3
            WHEN SUM(o.payment_value) >= 200 THEN 2
            ELSE 1
        END AS m_score
    FROM customers_agg c
    LEFT JOIN orders o
        ON c.customer_unique_id = o.customer_unique_id
        AND o.order_status IN ('delivered','shipped','invoiced','processing','created','approved')
    GROUP BY c.customer_unique_id, c.customer_state, c.customer_city;

    ALTER TABLE rfm_analysis ADD COLUMN rfm_total INT;
    ALTER TABLE rfm_analysis ADD COLUMN rfm_segment VARCHAR(20);
    UPDATE rfm_analysis SET rfm_total = r_score + f_score + m_score;
    UPDATE rfm_analysis SET rfm_segment =
        CASE
            WHEN rfm_total >= 10 THEN '高价值客户'
            WHEN rfm_total >= 7 THEN '中价值客户'
            WHEN rfm_total >= 4 THEN '一般客户'
            ELSE '低价值客户'
        END;
END//

DELIMITER ;

-- ============================================================
-- 6. 触发器：防止非法评分写入
-- ============================================================
DELIMITER //

CREATE TRIGGER trg_order_reviews_check_score
BEFORE INSERT ON order_reviews
FOR EACH ROW
BEGIN
    IF NEW.review_score < 1 OR NEW.review_score > 5 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'review_score must be between 1 and 5';
    END IF;
END//

DELIMITER ;

-- ============================================================
-- 7. 验证
-- ============================================================
SELECT '数据库创建完成' AS status;
