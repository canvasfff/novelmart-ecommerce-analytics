-- ============================================================
-- NovelMart 电商经营分析平台 - MySQL数据库建库建表脚本
-- 数据库名: ecommerce_analysis
-- 创建日期: 2026-07-31
-- ============================================================

-- 1. 创建数据库
DROP DATABASE IF EXISTS ecommerce_analysis;
CREATE DATABASE ecommerce_analysis
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE ecommerce_analysis;

-- ============================================================
-- 2. 创建用户表 (users)
-- ============================================================
CREATE TABLE users (
    user_id             INT PRIMARY KEY COMMENT '用户唯一标识',
    username            VARCHAR(50) NOT NULL COMMENT '用户名',
    real_name           VARCHAR(20) COMMENT '真实姓名',
    email               VARCHAR(100) COMMENT '电子邮箱',
    phone               VARCHAR(15) COMMENT '手机号',
    gender              VARCHAR(4) COMMENT '性别:男/女/未知',
    age                 INT COMMENT '年龄',
    province            VARCHAR(20) COMMENT '省份',
    city                VARCHAR(30) COMMENT '城市/区',
    registration_date   DATE COMMENT '注册日期',
    membership_level    VARCHAR(10) DEFAULT '普通会员' COMMENT '会员等级',
    total_orders        INT DEFAULT 0 COMMENT '累计订单数',
    total_spent         DECIMAL(12,2) DEFAULT 0.00 COMMENT '累计消费金额',
    avg_order_value     DECIMAL(10,2) DEFAULT 0.00 COMMENT '平均客单价',
    first_order_date    DATE COMMENT '首次下单日期',
    last_order_date     DATE COMMENT '最近下单日期',
    total_reviews       INT DEFAULT 0 COMMENT '累计评论数',
    avg_rating_given    DECIMAL(3,1) DEFAULT 0.0 COMMENT '平均给出评分',
    account_age_days    INT DEFAULT 0 COMMENT '账户年龄(天)',
    INDEX idx_province (province),
    INDEX idx_membership (membership_level),
    INDEX idx_reg_date (registration_date),
    INDEX idx_age (age)
) ENGINE=InnoDB COMMENT='用户信息表';


-- ============================================================
-- 3. 创建商品表 (products)
-- ============================================================
CREATE TABLE products (
    product_id      INT PRIMARY KEY COMMENT '商品唯一标识',
    product_name    VARCHAR(100) NOT NULL COMMENT '商品名称',
    category        VARCHAR(20) COMMENT '商品大类',
    subcategory     VARCHAR(30) COMMENT '商品子类',
    brand           VARCHAR(30) COMMENT '品牌',
    price           DECIMAL(10,2) NOT NULL COMMENT '售价',
    cost_price      DECIMAL(10,2) COMMENT '成本价',
    stock_quantity  INT DEFAULT 0 COMMENT '库存数量',
    sales_count     INT DEFAULT 0 COMMENT '累计销量',
    rating_avg      DECIMAL(3,1) DEFAULT 0.0 COMMENT '平均评分',
    listing_date    DATE COMMENT '上架日期',
    status          VARCHAR(10) DEFAULT '在售' COMMENT '商品状态:在售/下架/缺货',
    INDEX idx_category (category),
    INDEX idx_subcategory (subcategory ASC),
    INDEX idx_brand (brand),
    INDEX idx_price (price),
    INDEX idx_status (status),
    INDEX idx_rating (rating_avg)
) ENGINE=InnoDB COMMENT='商品信息表';


-- ============================================================
-- 4. 创建订单表 (orders)
-- ============================================================
CREATE TABLE orders (
    order_id            INT PRIMARY KEY COMMENT '订单唯一标识',
    user_id             INT NOT NULL COMMENT '用户ID',
    order_date          DATETIME COMMENT '下单时间',
    total_amount        DECIMAL(12,2) DEFAULT 0.00 COMMENT '商品总金额',
    discount_amount     DECIMAL(10,2) DEFAULT 0.00 COMMENT '折扣金额',
    actual_amount       DECIMAL(12,2) DEFAULT 0.00 COMMENT '实付金额(含运费)',
    payment_method      VARCHAR(15) COMMENT '支付方式',
    shipping_method     VARCHAR(10) COMMENT '配送方式',
    shipping_cost       DECIMAL(8,2) DEFAULT 0.00 COMMENT '运费',
    order_status        VARCHAR(10) DEFAULT '待付款' COMMENT '订单状态',
    shipping_province   VARCHAR(20) COMMENT '收货省份',
    shipping_city       VARCHAR(30) COMMENT '收货城市',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_order_date (order_date),
    INDEX idx_status (order_status),
    INDEX idx_payment (payment_method)
) ENGINE=InnoDB COMMENT='订单信息表';


-- ============================================================
-- 5. 创建订单明细表 (order_items)
-- ============================================================
CREATE TABLE order_items (
    item_id     INT PRIMARY KEY COMMENT '明细唯一标识',
    order_id    INT NOT NULL COMMENT '订单ID',
    product_id  INT NOT NULL COMMENT '商品ID',
    quantity    INT DEFAULT 1 COMMENT '购买数量',
    unit_price  DECIMAL(10,2) NOT NULL COMMENT '成交单价',
    discount    DECIMAL(4,2) DEFAULT 0.00 COMMENT '折扣比例(0-1)',
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    INDEX idx_order (order_id),
    INDEX idx_product (product_id)
) ENGINE=InnoDB COMMENT='订单明细表';


-- ============================================================
-- 6. 创建评论表 (reviews)
-- ============================================================
CREATE TABLE reviews (
    review_id           INT PRIMARY KEY COMMENT '评论唯一标识',
    user_id             INT NOT NULL COMMENT '用户ID',
    product_id          INT NOT NULL COMMENT '商品ID',
    order_id            INT NOT NULL COMMENT '订单ID',
    rating              TINYINT CHECK (rating BETWEEN 1 AND 5) COMMENT '评分(1-5)',
    review_text         TEXT COMMENT '评论内容',
    review_date         DATE COMMENT '评论日期',
    is_verified_purchase BOOLEAN DEFAULT TRUE COMMENT '是否认证购买',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_product (product_id),
    INDEX idx_rating (rating),
    INDEX idx_review_date (review_date)
) ENGINE=InnoDB COMMENT='商品评论表';


-- ============================================================
-- 7. 创建视图 - 用户消费总览
-- ============================================================
CREATE VIEW v_user_spending_summary AS
SELECT
    u.user_id,
    u.real_name,
    u.province,
    u.membership_level,
    u.total_spent,
    u.total_orders,
    u.avg_order_value,
    u.total_reviews,
    u.avg_rating_given,
    u.account_age_days,
    ROUND(u.total_spent / NULLIF(u.account_age_days, 0), 2) AS daily_avg_spent,
    CASE
        WHEN u.total_spent >= 50000 THEN '高价值'
        WHEN u.total_spent >= 10000 THEN '中价值'
        WHEN u.total_spent >= 1000 THEN '普通价值'
        ELSE '低价值'
    END AS customer_value_segment
FROM users u;


-- ============================================================
-- 8. 创建视图 - 商品销售表现
-- ============================================================
CREATE VIEW v_product_performance AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    p.brand,
    p.price,
    p.cost_price,
    p.sales_count,
    p.rating_avg,
    p.stock_quantity,
    ROUND(p.price - p.cost_price, 2) AS profit_per_unit,
    ROUND((p.price - p.cost_price) / NULLIF(p.price, 0) * 100, 2) AS profit_margin_pct,
    ROUND(p.sales_count * (p.price - p.cost_price), 2) AS estimated_total_profit,
    p.status,
    CASE
        WHEN p.rating_avg >= 4.5 THEN '好评如潮'
        WHEN p.rating_avg >= 4.0 THEN '好评'
        WHEN p.rating_avg >= 3.0 THEN '中评'
        WHEN p.rating_avg >= 2.0 THEN '差评'
        ELSE '很差'
    END AS rating_level
FROM products p;


-- ============================================================
-- 9. 创建视图 - 月度销售统计
-- ============================================================
CREATE VIEW v_monthly_sales AS
SELECT
    DATE_FORMAT(o.order_date, '%Y-%m') AS month,
    COUNT(DISTINCT o.order_id) AS order_count,
    COUNT(DISTINCT o.user_id) AS unique_customers,
    SUM(o.total_amount) AS total_revenue,
    SUM(o.discount_amount) AS total_discount,
    SUM(o.actual_amount) AS actual_revenue,
    ROUND(AVG(o.actual_amount), 2) AS avg_order_value,
    SUM(oi.quantity) AS total_units_sold
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = '已完成'
GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
ORDER BY month DESC;


-- ============================================================
-- 10. 存储过程 - 计算用户RFM值
-- ============================================================
DELIMITER //

CREATE PROCEDURE sp_calculate_rfm()
BEGIN
    DROP TABLE IF EXISTS rfm_analysis;
    CREATE TABLE rfm_analysis AS
    SELECT
        u.user_id,
        u.real_name,
        u.membership_level,
        DATEDIFF('2026-07-31', MAX(o.order_date)) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(o.actual_amount), 2) AS monetary,
        CASE
            WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 30 THEN 5
            WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 90 THEN 4
            WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 180 THEN 3
            WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 365 THEN 2
            ELSE 1
        END AS r_score,
        CASE
            WHEN COUNT(DISTINCT o.order_id) >= 20 THEN 5
            WHEN COUNT(DISTINCT o.order_id) >= 10 THEN 4
            WHEN COUNT(DISTINCT o.order_id) >= 5 THEN 3
            WHEN COUNT(DISTINCT o.order_id) >= 2 THEN 2
            ELSE 1
        END AS f_score,
        CASE
            WHEN SUM(o.actual_amount) >= 50000 THEN 5
            WHEN SUM(o.actual_amount) >= 20000 THEN 4
            WHEN SUM(o.actual_amount) >= 5000 THEN 3
            WHEN SUM(o.actual_amount) >= 1000 THEN 2
            ELSE 1
        END AS m_score
    FROM users u
    LEFT JOIN orders o ON u.user_id = o.user_id
    GROUP BY u.user_id, u.real_name, u.membership_level;

    -- 计算综合RFM分数
    ALTER TABLE rfm_analysis ADD COLUMN rfm_total INT;
    ALTER TABLE rfm_analysis ADD COLUMN rfm_segment VARCHAR(20);
    UPDATE rfm_analysis SET rfm_total = r_score + f_score + m_score;
    UPDATE rfm_analysis SET rfm_segment =
        CASE
            WHEN rfm_total >= 13 THEN '高价值客户'
            WHEN rfm_total >= 9 THEN '中价值客户'
            WHEN rfm_total >= 5 THEN '一般客户'
            ELSE '低价值客户'
        END;

    SELECT rfm_segment, COUNT(*) AS cnt,
           ROUND(AVG(monetary), 2) AS avg_monetary
    FROM rfm_analysis GROUP BY rfm_segment;
END //

DELIMITER ;


-- ============================================================
-- 11. 触发器 - 新评论自动更新商品评分
-- ============================================================
DELIMITER //

CREATE TRIGGER trg_update_product_rating
AFTER INSERT ON reviews
FOR EACH ROW
BEGIN
    UPDATE products p
    SET p.rating_avg = (
        SELECT ROUND(AVG(r.rating), 1)
        FROM reviews r
        WHERE r.product_id = NEW.product_id
    )
    WHERE p.product_id = NEW.product_id;
END //

DELIMITER ;


-- ============================================================
-- 12. 索引优化(覆盖常用查询)
-- ============================================================
CREATE INDEX idx_orders_user_date ON orders(user_id, order_date);
CREATE INDEX idx_orders_status_date ON orders(order_status, order_date);
CREATE INDEX idx_order_items_order_product ON order_items(order_id, product_id);
CREATE INDEX idx_reviews_product_rating ON reviews(product_id, rating);
CREATE INDEX idx_products_cat_sales ON products(category, sales_count DESC);
