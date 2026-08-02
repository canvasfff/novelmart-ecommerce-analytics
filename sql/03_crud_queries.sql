-- ============================================================
-- NovelMart 电商经营分析平台 - CRUD 增删改查操作大全
-- 数据库名: ecommerce_analysis
-- 使用说明: 请先执行 01_create_database.sql 和 02_data_import.sql
-- 创建日期: 2026-07-31
-- ============================================================
-- 本文件包含4大模块:
--   A. INSERT  — 插入操作（5个场景）
--   B. SELECT  — 查询分析（15个分析场景）
--   C. UPDATE  — 更新操作（5个场景）
--   D. DELETE  — 删除操作（3个场景）
-- 每个操作均配有详细中文注释，适合数据分析师面试作品集展示
-- ============================================================

USE ecommerce_analysis;

SET NAMES utf8mb4;


-- ################################################################
-- A. INSERT 插入操作（增）
-- ################################################################

-- ---------------------------------------------------------------
-- A-1. 插入新用户
-- 场景: 有新用户注册，录入用户表。注意 user_id 需自增或手动指定。
-- ---------------------------------------------------------------
INSERT INTO users (
    user_id, username, real_name, email, phone,
    gender, age, province, city, registration_date,
    membership_level, total_orders, total_spent,
    avg_order_value, first_order_date, last_order_date,
    total_reviews, avg_rating_given, account_age_days
) VALUES (
    100001,                          -- user_id: 假设现有数据为1-100000，新用户从100001起
    'new_user_zhang',                -- username: 新用户名
    '张伟',                          -- real_name: 真实姓名
    'zhangwei@example.com',          -- email
    '13800138001',                   -- phone
    '男',                            -- gender
    28,                              -- age
    '广东',                          -- province
    '深圳',                          -- city
    '2026-07-31',                    -- registration_date: 今天注册
    '普通会员',                      -- membership_level: 默认等级
    0,                               -- total_orders: 新用户暂无订单
    0.00,                            -- total_spent: 暂无消费
    0.00,                            -- avg_order_value
    NULL,                            -- first_order_date: 尚无首次下单
    NULL,                            -- last_order_date
    0,                               -- total_reviews
    0.0,                             -- avg_rating_given
    0                                -- account_age_days: 新建账户，0天
);

-- 验证插入结果
SELECT * FROM users WHERE user_id = 100001;


-- ---------------------------------------------------------------
-- A-2. 插入新商品
-- 场景: 商家上架新品，录入商品信息
-- ---------------------------------------------------------------
INSERT INTO products (
    product_id, product_name, category, subcategory,
    brand, price, cost_price, stock_quantity,
    sales_count, rating_avg, listing_date, status
) VALUES (
    50001,                           -- product_id
    '华为 MateBook X Pro 2026',      -- product_name: 新品名称
    '电子产品',                      -- category
    '笔记本电脑',                    -- subcategory
    '华为',                          -- brand
    8999.00,                         -- price: 售价
    6200.00,                         -- cost_price: 成本价
    200,                             -- stock_quantity: 首批库存200台
    0,                               -- sales_count: 新品暂无销量
    0.0,                             -- rating_avg: 新品暂无评分
    '2026-07-31',                    -- listing_date: 今日上架
    '在售'                           -- status: 状态为在售
);

-- 验证
SELECT * FROM products WHERE product_id = 50001;


-- ---------------------------------------------------------------
-- A-3. 插入新订单及订单明细（事务处理）
-- 场景: 用户在购物车中下单，需同时写入 orders 和 order_items 两张表，
--       必须使用事务保证原子性 —— 要么全部成功，要么全部回滚
-- ---------------------------------------------------------------
START TRANSACTION;

-- 3a. 先插入订单主记录
INSERT INTO orders (
    order_id, user_id, order_date,
    total_amount, discount_amount, actual_amount,
    payment_method, shipping_method, shipping_cost,
    order_status, shipping_province, shipping_city
) VALUES (
    900001,                          -- order_id
    100001,                          -- user_id: 关联上面刚插入的新用户
    '2026-07-31 14:30:00',           -- order_date: 下单时间
    8999.00,                         -- total_amount: 商品总金额（笔记本）
    500.00,                          -- discount_amount: 折扣金额（新用户优惠）
    8499.00,                         -- actual_amount: 实付 = 8999 - 500
    '微信支付',                      -- payment_method
    '普通快递',                      -- shipping_method
    0.00,                            -- shipping_cost: 免运费
    '待付款',                        -- order_status
    '广东',                          -- shipping_province
    '深圳'                           -- shipping_city
);

-- 3b. 再插入订单明细
INSERT INTO order_items (
    item_id, order_id, product_id,
    quantity, unit_price, discount
) VALUES (
    600001,                          -- item_id
    900001,                          -- order_id: 关联上面的订单
    50001,                           -- product_id: 关联上面的新商品
    1,                               -- quantity: 购买1台
    8999.00,                         -- unit_price: 成交单价
    0.00                             -- discount: 单品折扣比例
);

-- 3c. 同步更新用户的订单统计数据（total_orders, total_spent等）
-- 注意: MySQL 的 SET 子句从左到右求值，total_spent/total_orders 此处已是最新值，
--       直接用最新值计算平均客单价，避免在公式里重复累加本次订单金额
UPDATE users
SET total_orders      = total_orders + 1,
    total_spent       = total_spent + 8499.00,
    avg_order_value   = ROUND(total_spent / total_orders, 2),
    first_order_date  = COALESCE(first_order_date, '2026-07-31'),
    last_order_date   = '2026-07-31'
WHERE user_id = 100001;

COMMIT;
-- 如果任何一步出错，请执行 ROLLBACK; 回滚整个事务

-- 验证事务结果: 检查订单、明细、用户统计是否一致
SELECT o.order_id, o.user_id, o.actual_amount, o.order_status,
       oi.product_id, oi.quantity, oi.unit_price
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_id = 900001;

SELECT user_id, total_orders, total_spent, first_order_date
FROM users WHERE user_id = 100001;


-- ---------------------------------------------------------------
-- A-4. 批量插入订单明细（含订单主记录，事务保证原子性）
-- 场景: 一个订单包含多件商品（如购物车含3件商品），一次性批量写入
-- ---------------------------------------------------------------
START TRANSACTION;

-- 4a. 先插入订单主记录（订单900002此前不存在，必须先创建，否则外键约束会报错）
-- 金额口径: total_amount = 商品原价合计, discount_amount = 折扣金额,
--           actual_amount = total_amount - discount_amount + 运费
INSERT INTO orders (
    order_id, user_id, order_date,
    total_amount, discount_amount, actual_amount,
    payment_method, shipping_method, shipping_cost,
    order_status, shipping_province, shipping_city
) VALUES (
    900002,                            -- order_id
    100001,                            -- user_id: 关联 A-1 插入的新用户
    '2026-07-31 15:30:00',             -- order_date: 下单时间
    3324.00,                           -- total_amount: 2*1299 + 459 + 3*89 = 3324
    156.60,                            -- discount_amount: 1299*2*0.05 + 89*3*0.10 = 156.6
    3167.40,                           -- actual_amount: 3324 - 156.6 + 0 运费
    '支付宝',                          -- payment_method
    '普通快递',                        -- shipping_method
    0.00,                              -- shipping_cost: 免运费
    '待付款',                          -- order_status
    '广东',                            -- shipping_province
    '深圳'                             -- shipping_city
);

-- 4b. 再批量插入同一订单的多条明细
INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount) VALUES
    (600002, 900002, 100, 2, 1299.00, 0.05),   -- 商品100买2件，95折
    (600003, 900002, 250, 1, 459.00,  0.00),    -- 商品250买1件，无折扣
    (600004, 900002, 500, 3, 89.00,   0.10);    -- 商品500买3件，9折

-- 4c. 同步更新用户订单统计
UPDATE users
SET total_orders      = total_orders + 1,
    total_spent       = total_spent + 3167.40,
    avg_order_value   = ROUND(total_spent / total_orders, 2),
    last_order_date   = '2026-07-31'
WHERE user_id = 100001;

COMMIT;
-- 如果任何一步出错，请执行 ROLLBACK; 回滚整个事务

-- 批量验证（订单 + 明细金额 + 用户统计联动检查）
SELECT order_id, COUNT(*) AS item_count, SUM(quantity) AS total_qty,
       ROUND(SUM(quantity * unit_price * (1 - discount)), 2) AS line_total
FROM order_items
WHERE order_id = 900002
GROUP BY order_id;

SELECT user_id, total_orders, total_spent, avg_order_value
FROM users WHERE user_id = 100001;


-- ---------------------------------------------------------------
-- A-5. 插入商品评论
-- 场景: 用户购买后发表评价，同时触发器会自动更新产品的 rating_avg
-- ---------------------------------------------------------------
INSERT INTO reviews (
    review_id, user_id, product_id, order_id,
    rating, review_text, review_date, is_verified_purchase
) VALUES (
    800001,                          -- review_id
    100001,                          -- user_id: 评论用户
    50001,                           -- product_id: 被评论商品
    900001,                          -- order_id: 关联的订单号
    4,                               -- rating: 4分（5分制）
    '做工精致，性能出色，键盘手感极佳。唯一的遗憾是只有两个USB-C接口，需要转接器。整体性价比很高，推荐购买！',
    '2026-07-31',                    -- review_date: 评论日期
    TRUE                             -- is_verified_purchase: 认证购买
);

-- 验证评论以及触发器是否更新了商品评分
SELECT review_id, rating, review_text FROM reviews WHERE review_id = 800001;
SELECT product_id, product_name, rating_avg FROM products WHERE product_id = 50001;


-- ################################################################
-- B. SELECT 查询分析（查）—— 15个核心分析场景
-- ################################################################
-- ------------------------------------------------------------------
-- 口径说明（本文件所有营收/销售统计统一遵循）:
--   1. 「有效订单」 = 已完成 / 待发货 / 已发货（已付款且未退款）
--      （数据中不存在"待收货"状态，该值已从过滤条件中移除）
--   2. 销售额均按 数量 × 成交单价 × (1 - 折扣) 计算，
--      与 Python 分析 (02/03/04 脚本的 line_total) 口径保持一致
-- ------------------------------------------------------------------

-- ---------------------------------------------------------------
-- B-1. 消费最高的Top 10用户（用户价值排名）
-- 业务价值: 识别高价值用户，为 VIP 定向营销提供数据支撑
-- ---------------------------------------------------------------
SELECT
    u.user_id,
    u.real_name                       AS 用户姓名,
    u.province                        AS 省份,
    u.membership_level                AS 会员等级,
    u.total_orders                    AS 订单数,
    u.total_spent                     AS 累计消费金额,
    u.avg_order_value                 AS 平均客单价,
    u.last_order_date                 AS 最近下单日期,
    DATEDIFF('2026-07-31', u.last_order_date) AS 距今天数
FROM users u
ORDER BY u.total_spent DESC
LIMIT 10;


-- ---------------------------------------------------------------
-- B-2. 月度销售收入趋势分析
-- 业务价值: 观察营收变化趋势，识别销售旺季与淡季，辅助制定运营策略
-- ---------------------------------------------------------------
SELECT
    DATE_FORMAT(o.order_date, '%Y-%m')      AS 月份,
    COUNT(DISTINCT o.order_id)              AS 订单数,
    COUNT(DISTINCT o.user_id)               AS 下单用户数,
    ROUND(SUM(o.total_amount), 2)           AS 商品总额,
    ROUND(SUM(o.discount_amount), 2)        AS 折扣总额,
    ROUND(SUM(o.actual_amount), 2)          AS 实收总额,
    ROUND(AVG(o.actual_amount), 2)          AS 平均订单金额,
    ROUND(SUM(o.actual_amount) / NULLIF(COUNT(DISTINCT o.user_id), 0), 2)
                                            AS 人均消费金额,
    ROUND(SUM(o.discount_amount) / NULLIF(SUM(o.total_amount), 0) * 100, 2)
                                            AS 折扣率_pct
FROM orders o
WHERE o.order_status IN ('已完成', '待发货', '已发货')
GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
ORDER BY 月份 DESC;


-- ---------------------------------------------------------------
-- B-3. 商品大类销售排行榜（含销售额、销量、利润率）
-- 业务价值: 识别核心品类，优化品类运营策略和资源配置
-- ---------------------------------------------------------------
SELECT
    p.category                             AS 商品大类,
    COUNT(DISTINCT p.product_id)           AS 商品数,
    SUM(oi.quantity)                       AS 总销量,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2)
                                            AS 总销售额,
    ROUND(AVG(p.rating_avg), 2)             AS 品类平均评分,
    ROUND(AVG(p.price - p.cost_price), 2)   AS 平均单品毛利,
    ROUND(SUM(oi.quantity * (oi.unit_price * (1 - oi.discount) - p.cost_price)), 2)
                                            AS 预估总毛利
FROM products p
JOIN order_items oi     ON p.product_id = oi.product_id
JOIN orders o           ON oi.order_id = o.order_id
WHERE o.order_status IN ('已完成', '待发货', '已发货')
GROUP BY p.category
ORDER BY 总销售额 DESC;


-- ---------------------------------------------------------------
-- B-4. 高评分商品榜单（评分 > 4.5 且有一定销量基础）
-- 业务价值: 挖掘口碑爆款，用于首页推荐和营销活动选品
-- ---------------------------------------------------------------
SELECT
    p.product_id,
    p.product_name                        AS 商品名称,
    p.category                            AS 大类,
    p.brand                               AS 品牌,
    p.price                               AS 售价,
    p.sales_count                         AS 累计销量,
    p.rating_avg                          AS 平均评分,
    p.stock_quantity                      AS 库存,
    ROUND(p.price - p.cost_price, 2)      AS 单品毛利,
    p.status                              AS 商品状态
FROM products p
WHERE p.rating_avg > 4.5
  AND p.sales_count >= 10                 -- 至少10笔销量，排除偶然高分
  AND p.status = '在售'
ORDER BY p.rating_avg DESC, p.sales_count DESC
LIMIT 20;


-- ---------------------------------------------------------------
-- B-5. 用户订单数量分布分析（消费频次分层）
-- 业务价值: 了解用户活跃度分布，判断平台用户粘性
-- ---------------------------------------------------------------
SELECT
    CASE
        WHEN u.total_orders = 1  THEN '1次（新客）'
        WHEN u.total_orders = 2  THEN '2次'
        WHEN u.total_orders BETWEEN 3 AND 5   THEN '3-5次（回头客）'
        WHEN u.total_orders BETWEEN 6 AND 10  THEN '6-10次（忠诚用户）'
        WHEN u.total_orders BETWEEN 11 AND 20 THEN '11-20次（高频用户）'
        ELSE '20次以上（超级用户）'
    END                                          AS 下单频次区间,
    COUNT(*)                                     AS 用户数,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2)
                                                 AS 占比_pct,
    ROUND(AVG(u.total_spent), 2)                 AS 人均累计消费
FROM users u
WHERE u.total_orders > 0
GROUP BY 下单频次区间
ORDER BY MIN(u.total_orders);


-- ---------------------------------------------------------------
-- B-6. 支付方式分布分析
-- 业务价值: 了解用户支付偏好，优化支付渠道体验
-- ---------------------------------------------------------------
SELECT
    o.payment_method                      AS 支付方式,
    COUNT(*)                              AS 订单数,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2)
                                          AS 订单占比_pct,
    ROUND(SUM(o.actual_amount), 2)        AS 交易总额,
    ROUND(AVG(o.actual_amount), 2)        AS 平均订单金额
FROM orders o
WHERE o.order_status IN ('已完成', '待发货', '已发货')
GROUP BY o.payment_method
ORDER BY 订单数 DESC;


-- ---------------------------------------------------------------
-- B-7. 各省份订单量及销售额排名
-- 业务价值: 识别核心市场区域，指导仓储物流布局和区域营销投入
-- ---------------------------------------------------------------
SELECT
    COALESCE(o.shipping_province, '未知')   AS 省份,
    COUNT(DISTINCT o.order_id)              AS 订单数,
    COUNT(DISTINCT o.user_id)               AS 下单用户数,
    ROUND(SUM(o.actual_amount), 2)          AS 销售总额,
    ROUND(AVG(o.actual_amount), 2)          AS 平均订单金额,
    ROUND(SUM(o.actual_amount) / NULLIF(COUNT(DISTINCT o.user_id), 0), 2)
                                            AS 人均消费
FROM orders o
WHERE o.order_status IN ('已完成', '待发货', '已发货')
GROUP BY 省份
ORDER BY 销售总额 DESC
LIMIT 15;


-- ---------------------------------------------------------------
-- B-8. 各品类平均评分对比
-- 业务价值: 评估不同品类用户满意度差异，定位需要改进的品类
-- ---------------------------------------------------------------
SELECT
    p.category                             AS 大类,
    ROUND(AVG(p.rating_avg), 2)            AS 品类商品均分,
    ROUND(STDDEV(p.rating_avg), 2)         AS 评分标准差,
    MIN(p.rating_avg)                      AS 最低分,
    MAX(p.rating_avg)                      AS 最高分,
    COUNT(*)                               AS 商品数,
    ROUND(SUM(CASE WHEN p.rating_avg >= 4.5 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                           AS 高评分商品占比_pct
FROM products p
WHERE p.sales_count > 0
GROUP BY p.category
ORDER BY 品类商品均分 DESC;


-- ---------------------------------------------------------------
-- B-9. 高销量低库存补货预警
-- 业务价值: 提前发现畅销品库存不足问题，避免断货影响销售
-- ---------------------------------------------------------------
SELECT
    p.product_id,
    p.product_name                        AS 商品名称,
    p.category                            AS 大类,
    p.brand                               AS 品牌,
    p.sales_count                         AS 累计销量,
    p.stock_quantity                      AS 当前库存,
    -- 按日均销量估算可售天数（假设上架至今日均销售）
    ROUND(p.sales_count / NULLIF(DATEDIFF('2026-07-31', p.listing_date), 0), 2)
                                          AS 日均销量,
    CASE
        WHEN p.stock_quantity = 0 THEN '0（紧急补货！）'
        WHEN ROUND(p.stock_quantity / NULLIF(
            p.sales_count / NULLIF(DATEDIFF('2026-07-31', p.listing_date), 0), 0), 0) <= 7
            THEN '7天以内（需补货）'
        WHEN ROUND(p.stock_quantity / NULLIF(
            p.sales_count / NULLIF(DATEDIFF('2026-07-31', p.listing_date), 0), 0), 0) <= 30
            THEN '30天以内（预警）'
        ELSE '充足'
    END                                    AS 库存预警等级,
    ROUND(p.price - p.cost_price, 2)       AS 单品毛利
FROM products p
WHERE p.sales_count >= 50                  -- 有一定销量基础
  AND p.stock_quantity < 200               -- 库存偏低
  AND p.status = '在售'
ORDER BY p.stock_quantity ASC, p.sales_count DESC
LIMIT 20;


-- ---------------------------------------------------------------
-- B-10. 客户 RFM 分析（Recency - 最近消费 / Frequency - 消费频率 / Monetary - 消费金额）
-- 业务价值: 经典客户价值分层模型，支持精准营销和客户挽回策略
-- ---------------------------------------------------------------
SELECT
    u.user_id,
    u.real_name                            AS 用户名,
    u.province                             AS 省份,
    u.membership_level                     AS 会员等级,
    -- R: Recency —— 距最后消费天数
    DATEDIFF('2026-07-31', MAX(o.order_date))
                                           AS 最近消费距今天数,
    -- F: Frequency —— 历史订单总数
    COUNT(DISTINCT o.order_id)             AS 消费频次,
    -- M: Monetary —— 累计消费金额
    ROUND(SUM(o.actual_amount), 2)         AS 累计消费金额,
    -- R得分（分值越高越近）
    CASE
        WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 30  THEN 5
        WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 90  THEN 4
        WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 180 THEN 3
        WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 365 THEN 2
        ELSE 1
    END                                    AS R得分,
    -- F得分（分值越高购买越频繁）
    CASE
        WHEN COUNT(DISTINCT o.order_id) >= 20 THEN 5
        WHEN COUNT(DISTINCT o.order_id) >= 10 THEN 4
        WHEN COUNT(DISTINCT o.order_id) >= 5  THEN 3
        WHEN COUNT(DISTINCT o.order_id) >= 2  THEN 2
        ELSE 1
    END                                    AS F得分,
    -- M得分（分值越高贡献越大）
    CASE
        WHEN SUM(o.actual_amount) >= 50000 THEN 5
        WHEN SUM(o.actual_amount) >= 20000 THEN 4
        WHEN SUM(o.actual_amount) >= 5000  THEN 3
        WHEN SUM(o.actual_amount) >= 1000  THEN 2
        ELSE 1
    END                                    AS M得分,
    -- 综合分层
    CASE
        WHEN (CASE WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 30  THEN 5
                    WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 90  THEN 4
                    WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 180 THEN 3
                    WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 365 THEN 2
                    ELSE 1 END
              + CASE WHEN COUNT(DISTINCT o.order_id) >= 20 THEN 5
                     WHEN COUNT(DISTINCT o.order_id) >= 10 THEN 4
                     WHEN COUNT(DISTINCT o.order_id) >= 5  THEN 3
                     WHEN COUNT(DISTINCT o.order_id) >= 2  THEN 2
                     ELSE 1 END
              + CASE WHEN SUM(o.actual_amount) >= 50000 THEN 5
                     WHEN SUM(o.actual_amount) >= 20000 THEN 4
                     WHEN SUM(o.actual_amount) >= 5000  THEN 3
                     WHEN SUM(o.actual_amount) >= 1000  THEN 2
                     ELSE 1 END) >= 13 THEN '高价值客户'
        WHEN (CASE WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 30  THEN 5
                    WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 90  THEN 4
                    WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 180 THEN 3
                    WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 365 THEN 2
                    ELSE 1 END
              + CASE WHEN COUNT(DISTINCT o.order_id) >= 20 THEN 5
                     WHEN COUNT(DISTINCT o.order_id) >= 10 THEN 4
                     WHEN COUNT(DISTINCT o.order_id) >= 5  THEN 3
                     WHEN COUNT(DISTINCT o.order_id) >= 2  THEN 2
                     ELSE 1 END
              + CASE WHEN SUM(o.actual_amount) >= 50000 THEN 5
                     WHEN SUM(o.actual_amount) >= 20000 THEN 4
                     WHEN SUM(o.actual_amount) >= 5000  THEN 3
                     WHEN SUM(o.actual_amount) >= 1000  THEN 2
                     ELSE 1 END) >= 9  THEN '中价值客户'
        WHEN (CASE WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 30  THEN 5
                    WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 90  THEN 4
                    WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 180 THEN 3
                    WHEN DATEDIFF('2026-07-31', MAX(o.order_date)) <= 365 THEN 2
                    ELSE 1 END
              + CASE WHEN COUNT(DISTINCT o.order_id) >= 20 THEN 5
                     WHEN COUNT(DISTINCT o.order_id) >= 10 THEN 4
                     WHEN COUNT(DISTINCT o.order_id) >= 5  THEN 3
                     WHEN COUNT(DISTINCT o.order_id) >= 2  THEN 2
                     ELSE 1 END
              + CASE WHEN SUM(o.actual_amount) >= 50000 THEN 5
                     WHEN SUM(o.actual_amount) >= 20000 THEN 4
                     WHEN SUM(o.actual_amount) >= 5000  THEN 3
                     WHEN SUM(o.actual_amount) >= 1000  THEN 2
                     ELSE 1 END) >= 5  THEN '一般客户'
        ELSE '低价值客户'
    END                                    AS 客户价值分层
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE o.order_status IN ('已完成', '待发货', '已发货') OR o.order_id IS NULL
GROUP BY u.user_id, u.real_name, u.province, u.membership_level
ORDER BY 累计消费金额 DESC
LIMIT 30;


-- ---------------------------------------------------------------
-- B-11. 用户注册月份队列分析（Cohort Analysis）
-- 业务价值: 按注册月份分组，观察不同批次用户的累计行为表现
-- ---------------------------------------------------------------
SELECT
    DATE_FORMAT(u.registration_date, '%Y-%m')     AS 注册月份,
    COUNT(*)                                       AS 注册用户数,
    -- 该批次中有多少用户转化为了下单用户（转化率）
    ROUND(SUM(CASE WHEN u.total_orders > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
                                                   AS 下单转化率_pct,
    -- 该批次用户的平均累计消费金额
    ROUND(AVG(u.total_spent), 2)                   AS 人均累计消费,
    -- 该批次用户的平均订单数
    ROUND(AVG(u.total_orders), 2)                  AS 人均订单数,
    -- 该批次用户的平均评论数（活跃度指标）
    ROUND(AVG(u.total_reviews), 2)                 AS 人均评论数,
    ROUND(AVG(u.avg_rating_given), 2)              AS 平均给出评分
FROM users u
GROUP BY DATE_FORMAT(u.registration_date, '%Y-%m')
ORDER BY 注册月份;


-- ---------------------------------------------------------------
-- B-12. 各类目内商品销售额排名（窗口函数 DENSE_RANK）
-- 业务价值: 识别各类目下的明星商品和长尾商品，支撑类目运营精细化
-- ---------------------------------------------------------------
SELECT
    p.category                                   AS 大类,
    p.product_name                               AS 商品名称,
    p.brand                                      AS 品牌,
    p.price                                      AS 售价,
    p.sales_count                                AS 累计销量,
    p.rating_avg                                 AS 评分,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2)   AS 销售额,
    DENSE_RANK() OVER (
        PARTITION BY p.category
        ORDER BY SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) DESC
    )                                            AS 类目内销售额排名,
    -- 累计占比（该商品在该类目中的销售贡献累计）
    ROUND(
        SUM(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)))
            OVER (PARTITION BY p.category ORDER BY SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) DESC)
        / NULLIF(SUM(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)))
            OVER (PARTITION BY p.category), 0) * 100
    , 2)                                         AS 类目内累计占比_pct
FROM products p
JOIN order_items oi    ON p.product_id = oi.product_id
JOIN orders o          ON oi.order_id = o.order_id
WHERE o.order_status IN ('已完成', '待发货', '已发货')
GROUP BY p.category, p.product_id, p.product_name, p.brand, p.price, p.sales_count, p.rating_avg
ORDER BY p.category, 销售额 DESC;


-- ---------------------------------------------------------------
-- B-13. 评论情感分析（好评/中评/差评分布）
-- 业务价值: 掌握整体用户满意度，定位差评重灾区产品
-- ---------------------------------------------------------------
SELECT
    CASE
        WHEN r.rating >= 4 THEN '好评'
        WHEN r.rating = 3  THEN '中评'
        ELSE '差评'
    END                                          AS 评论情感,
    COUNT(*)                                     AS 评论数,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2)
                                                 AS 占比_pct,
    COUNT(DISTINCT r.product_id)                 AS 涉及商品数,
    COUNT(DISTINCT r.user_id)                    AS 涉及用户数
FROM reviews r
WHERE r.review_text IS NOT NULL
  AND TRIM(r.review_text) <> ''                   -- 排除空评论
GROUP BY 评论情感
ORDER BY 评论数 DESC;


-- 进一步细化：按产品查看差评率，定位需要改进的商品
SELECT
    p.product_id,
    p.product_name                               AS 商品名称,
    p.category                                   AS 大类,
    p.rating_avg                                 AS 当前评分,
    COUNT(*)                                     AS 总评论数,
    SUM(CASE WHEN r.rating <= 2 THEN 1 ELSE 0 END)
                                                 AS 差评数,
    ROUND(SUM(CASE WHEN r.rating <= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
                                                 AS 差评率_pct,
    SUM(CASE WHEN r.rating >= 4 THEN 1 ELSE 0 END)
                                                 AS 好评数,
    ROUND(SUM(CASE WHEN r.rating >= 4 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
                                                 AS 好评率_pct
FROM reviews r
JOIN products p ON r.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category, p.rating_avg
HAVING COUNT(*) >= 20                            -- 至少有20条评论才有统计意义
ORDER BY 差评率_pct DESC
LIMIT 15;


-- ---------------------------------------------------------------
-- B-14. 每订单平均商品数分析
-- 业务价值: 评估用户购物篮大小，指导满减、搭配推荐等策略
-- ---------------------------------------------------------------
SELECT
    ROUND(AVG(item_count), 1)                    AS 平均每单商品件数,
    ROUND(AVG(total_qty), 1)                     AS 平均每单商品数量,
    ROUND(MAX(item_count), 0)                    AS 最大单品数,
    ROUND(MIN(item_count), 0)                    AS 最小单品数,
    -- 订单商品数分布
    ROUND(SUM(CASE WHEN item_count = 1     THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
                                                 AS 仅含1件商品订单占比_pct,
    ROUND(SUM(CASE WHEN item_count >= 2 AND item_count <= 3 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
                                                 AS `含2-3件商品订单占比_pct`,
    ROUND(SUM(CASE WHEN item_count >= 4     THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
                                                 AS 含4件以上商品订单占比_pct
FROM (
    SELECT
        o.order_id,
        COUNT(DISTINCT oi.product_id) AS item_count,   -- 不同商品种类数
        SUM(oi.quantity)              AS total_qty       -- 商品总件数
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status IN ('已完成', '待发货', '已发货')
    GROUP BY o.order_id
) sub;


-- ---------------------------------------------------------------
-- B-15. 用户复购率分析
-- 业务价值: 衡量平台用户粘性和忠诚度，复购率 = 下单>=2次的用户数 / 总下单用户数
-- ---------------------------------------------------------------
SELECT
    -- 总下单用户数
    COUNT(*)                                       AS 总下单用户数,
    -- 复购用户数（订单数 >= 2）
    SUM(CASE WHEN u.total_orders >= 2 THEN 1 ELSE 0 END)
                                                   AS 复购用户数,
    -- 复购率
    ROUND(SUM(CASE WHEN u.total_orders >= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
                                                   AS 复购率_pct,
    -- 高频复购（订单数 >= 5）
    SUM(CASE WHEN u.total_orders >= 5 THEN 1 ELSE 0 END)
                                                   AS 高频复购用户数,
    ROUND(SUM(CASE WHEN u.total_orders >= 5 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
                                                   AS 高频复购率_pct,
    -- 仅购1次的用户
    SUM(CASE WHEN u.total_orders = 1 THEN 1 ELSE 0 END)
                                                   AS 仅购1次用户数
FROM users u
WHERE u.total_orders > 0;


-- 进一步按会员等级分析复购率
SELECT
    u.membership_level                             AS 会员等级,
    COUNT(*)                                       AS 下单用户数,
    SUM(CASE WHEN u.total_orders >= 2 THEN 1 ELSE 0 END)
                                                   AS 复购用户数,
    ROUND(SUM(CASE WHEN u.total_orders >= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
                                                   AS 复购率_pct,
    ROUND(AVG(u.total_orders), 1)                  AS 人均订单数,
    ROUND(AVG(u.total_spent), 2)                   AS 人均消费金额
FROM users u
WHERE u.total_orders > 0
GROUP BY u.membership_level
ORDER BY 复购率_pct DESC;


-- ################################################################
-- C. UPDATE 更新操作（改）
-- ################################################################

-- ---------------------------------------------------------------
-- C-1. 根据消费金额自动更新用户会员等级
-- 场景: 运营人员定期根据用户累计消费，批量刷新会员等级
--       钻石 >= 50000, 金卡 >= 30000, 银卡 >= 10000, 铜卡 >= 3000, 其余为普通会员
-- ---------------------------------------------------------------
-- 首先查看更新前的会员等级分布
SELECT membership_level AS 更新前等级, COUNT(*) AS 人数 FROM users GROUP BY membership_level;

-- 执行批量更新
UPDATE users
SET membership_level = CASE
    WHEN total_spent >= 50000 THEN '钻石会员'
    WHEN total_spent >= 30000 THEN '金卡会员'
    WHEN total_spent >= 10000 THEN '银卡会员'
    WHEN total_spent >= 3000  THEN '铜卡会员'
    ELSE '普通会员'
END
WHERE total_orders > 0;    -- 至少有1笔订单才更新

-- 验证更新后分布
SELECT membership_level AS 更新后等级, COUNT(*) AS 人数 FROM users GROUP BY membership_level;

-- 随机抽查几条记录确认
SELECT user_id, real_name, total_spent, total_orders, membership_level
FROM users WHERE total_orders > 0
ORDER BY total_spent DESC LIMIT 10;


-- ---------------------------------------------------------------
-- C-2. 低库存商品自动更新状态为「缺货」
-- 场景: 库存为0或低于安全库存阈值(5件)的商品，自动标记为缺货状态
-- ---------------------------------------------------------------
-- 更新前快照
SELECT status AS 更新前状态, COUNT(*) AS 商品数
FROM products WHERE stock_quantity < 5 AND status = '在售';

-- 执行更新
UPDATE products
SET status = '缺货'
WHERE stock_quantity < 5
  AND status = '在售';       -- 只更新当前在售的商品

-- 验证
SELECT product_id, product_name, stock_quantity, status
FROM products WHERE status = '缺货'
ORDER BY stock_quantity ASC LIMIT 15;


-- ---------------------------------------------------------------
-- C-3. 对滞销商品应用清仓折扣（调整售价和状态）
-- 场景: 上架超过180天、销量低于10件且非知名品牌的商品，
--       打8折清仓处理，并标记为「清仓促销」
-- ---------------------------------------------------------------
-- 先查看需要打折的商品（更新前预览）
SELECT
    product_id, product_name, brand, price, sales_count, listing_date, status,
    DATEDIFF('2026-07-31', listing_date) AS 上架天数,
    ROUND(price * 0.8, 2)               AS 折后价格
FROM products
WHERE DATEDIFF('2026-07-31', listing_date) > 180
  AND sales_count < 10
  AND status = '在售'
  AND price > 50;                       -- 价格太低的不参与（避免亏本）

-- 执行更新
UPDATE products
SET
    price  = ROUND(price * 0.8, 2),     -- 打8折
    status = '清仓促销'
WHERE DATEDIFF('2026-07-31', listing_date) > 180
  AND sales_count < 10
  AND status = '在售'
  AND price > 50;

-- 验证更新结果
SELECT product_id, product_name, price, status
FROM products WHERE status = '清仓促销'
ORDER BY price LIMIT 10;


-- ---------------------------------------------------------------
-- C-4. 批量修改待发货订单的配送方式
-- 场景: 物流合作方切换，将所有「待发货」且配送方式为「普通快递」的订单
--       改为「加急快递」（例如双十一期间默认升级物流）
-- ---------------------------------------------------------------
-- 更新前统计
SELECT shipping_method AS 当前配送方式, COUNT(*) AS 订单数
FROM orders
WHERE order_status = '待发货' AND shipping_method = '普通快递'
GROUP BY shipping_method;

-- 执行批量更新
UPDATE orders
SET
    shipping_method = '加急快递',
    shipping_cost   = shipping_cost + 8.00,   -- 升级加急加收8元运费
    actual_amount   = actual_amount + 8.00    -- 同步实付金额，保持金额口径一致
WHERE order_status = '待发货'
  AND shipping_method = '普通快递';

-- 验证
SELECT shipping_method AS 更新后配送方式, COUNT(*) AS 订单数
FROM orders WHERE order_status = '待发货'
GROUP BY shipping_method;

-- 抽查几单
SELECT order_id, user_id, shipping_method, shipping_cost, order_status
FROM orders WHERE order_status = '待发货' AND shipping_method = '加急快递'
LIMIT 10;


-- ---------------------------------------------------------------
-- C-5. 根据最新评论数据修正商品评分
-- 场景: 由于触发器可能遗漏或数据迁移后不一致，定期校准 products.rating_avg
--       使其与 reviews 表中的实际平均评分一致
-- ---------------------------------------------------------------
-- 更新前：比较产品表评分和评论表实际评分的差异
SELECT
    p.product_id,
    p.product_name,
    p.rating_avg                AS 产品表评分,
    ROUND(AVG(r.rating), 1)     AS 评论表实际均分,
    ROUND(p.rating_avg - ROUND(AVG(r.rating), 1), 1)
                                AS 评分偏差
FROM products p
JOIN reviews r ON p.product_id = r.product_id
GROUP BY p.product_id, p.product_name, p.rating_avg
HAVING ABS(ROUND(p.rating_avg - AVG(r.rating), 1)) > 0.1   -- 偏差超过0.1分的才展示
ORDER BY 评分偏差 DESC
LIMIT 15;

-- 执行修正更新（使用子查询关联 reviews 表计算真实平均分）
UPDATE products p
JOIN (
    SELECT
        r.product_id,
        ROUND(AVG(r.rating), 1) AS avg_rating
    FROM reviews r
    GROUP BY r.product_id
) calc ON p.product_id = calc.product_id
SET p.rating_avg = calc.avg_rating
WHERE ABS(p.rating_avg - calc.avg_rating) > 0.05;   -- 仅修正偏差超过0.05分的，避免无意义更新

-- 验证：修正后理论上不应再有偏差
SELECT COUNT(*) AS 仍有偏差的商品数
FROM products p
JOIN (
    SELECT product_id, ROUND(AVG(rating), 1) AS avg_rating
    FROM reviews GROUP BY product_id
) calc ON p.product_id = calc.product_id
WHERE ABS(p.rating_avg - calc.avg_rating) > 0.1;


-- ################################################################
-- D. DELETE 删除操作（删）
-- ################################################################

-- ---------------------------------------------------------------
-- D-1. 删除超过1年的已取消订单及关联数据
-- 场景: 定期清理历史无效数据，释放存储空间
--       注意：由于设置了 ON DELETE CASCADE，删除订单会自动删除
--       对应的 order_items 和 reviews 记录
-- ---------------------------------------------------------------
-- 删除前统计即将清理的数据量
SELECT 'orders' AS 表名, COUNT(*) AS 待删除记录数
FROM orders
WHERE order_status = '已取消'
  AND order_date < DATE_SUB('2026-07-31', INTERVAL 1 YEAR)
UNION ALL
SELECT 'order_items' AS 表名, COUNT(*) AS 待删除记录数
FROM order_items
WHERE order_id IN (
    SELECT order_id FROM orders
    WHERE order_status = '已取消'
      AND order_date < DATE_SUB('2026-07-31', INTERVAL 1 YEAR)
)
UNION ALL
SELECT 'reviews' AS 表名, COUNT(*) AS 待删除记录数
FROM reviews
WHERE order_id IN (
    SELECT order_id FROM orders
    WHERE order_status = '已取消'
      AND order_date < DATE_SUB('2026-07-31', INTERVAL 1 YEAR)
);

-- ⚠️ 执行删除前请确认备份！
-- 执行删除（CASCADE 会自动清理 order_items 和 reviews 中的关联数据）
DELETE FROM orders
WHERE order_status = '已取消'
  AND order_date < DATE_SUB('2026-07-31', INTERVAL 1 YEAR);

-- 验证删除结果
SELECT ROW_COUNT() AS 已删除订单数;
SELECT COUNT(*) AS 剩余已取消且超1年订单数
FROM orders
WHERE order_status = '已取消'
  AND order_date < DATE_SUB('2026-07-31', INTERVAL 1 YEAR);


-- ---------------------------------------------------------------
-- D-2. 删除疑似垃圾评论（评分1分且评论内容为空或无效）
-- 场景: 恶意差评或垃圾评论清理，保护商品评分的公正性
-- ---------------------------------------------------------------
-- 删除前预览要清理的评论
SELECT
    review_id,
    user_id,
    product_id,
    rating,
    review_text,
    review_date
FROM reviews
WHERE rating = 1
  AND (review_text IS NULL
       OR TRIM(review_text) = ''
       OR CHAR_LENGTH(TRIM(review_text)) < 5);   -- 少于5个字符视为无效评论

-- 执行删除
DELETE FROM reviews
WHERE rating = 1
  AND (review_text IS NULL
       OR TRIM(review_text) = ''
       OR CHAR_LENGTH(TRIM(review_text)) < 5);

-- 验证
SELECT ROW_COUNT() AS 已删除垃圾评论数;


-- ---------------------------------------------------------------
-- D-3. 删除注册超过2年但从未下单的静默用户
-- 场景: 清理长期不活跃的无效账户，维护用户表质量
--       注意：这些用户无订单也无评论（外键CASCADE不触发），可以直接删除
-- ---------------------------------------------------------------
-- 删除前统计
SELECT
    COUNT(*)                             AS 待删除用户数,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM users), 2)
                                         AS 占总用户比_pct
FROM users
WHERE total_orders = 0
  AND registration_date < DATE_SUB('2026-07-31', INTERVAL 2 YEAR);

-- 抽样查看几个待删除用户
SELECT user_id, username, real_name, registration_date,
       DATEDIFF('2026-07-31', registration_date) AS 注册天数,
       total_orders, total_spent
FROM users
WHERE total_orders = 0
  AND registration_date < DATE_SUB('2026-07-31', INTERVAL 2 YEAR)
LIMIT 10;

-- ⚠️ 执行删除前请确认备份！
-- 执行删除
DELETE FROM users
WHERE total_orders = 0
  AND registration_date < DATE_SUB('2026-07-31', INTERVAL 2 YEAR);

-- 验证
SELECT ROW_COUNT() AS 已删除静默用户数;

-- 确认无残留
SELECT COUNT(*) AS 剩余静默用户数
FROM users
WHERE total_orders = 0
  AND registration_date < DATE_SUB('2026-07-31', INTERVAL 2 YEAR);


-- ============================================================
-- 全文件结束
-- 执行完成后建议:
--   1. 检查各表行数是否与预期一致
--   2. 执行 ANALYZE TABLE users, products, orders, order_items, reviews;
--      更新表统计信息以优化后续查询性能
--   3. 定期备份数据库: mysqldump -u root -p ecommerce_analysis > backup.sql
-- ============================================================
SELECT '>>> CRUD 操作脚本执行完毕 <<<' AS done;
