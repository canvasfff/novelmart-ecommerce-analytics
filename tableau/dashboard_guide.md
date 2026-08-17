# Tableau 看板制作指南 - NovelMart 电商经营分析平台

## 环境准备

### 1. Tableau 软件安装
- **推荐版本**: Tableau Desktop 2024.x 或 Tableau Public (免费)
- **下载地址**: https://www.tableau.com/products/desktop
- **Tableau Public**: https://public.tableau.com/ (免费，功能齐全)

### 2. 数据源准备
在 `data/` 目录下已准备好的CSV文件可直接导入 Tableau：
- `users.csv` - 用户数据
- `products.csv` - 商品数据
- `orders.csv` - 订单数据
- `order_items.csv` - 订单明细
- `reviews.csv` - 评论数据

### 3. 数据连接步骤
1. 打开 Tableau Desktop
2. 左侧连接器选择「文本文件」
3. 依次导入各CSV文件
4. 在「数据源」标签页建立表关联：
   - `orders.user_id` = `users.user_id`
   - `orders.order_id` = `order_items.order_id`
   - `order_items.product_id` = `products.product_id`
   - `reviews.order_id` = `orders.order_id`
5. 数据提取：建议使用「数据提取」模式提高性能

> ⚠️ **口径提醒（重要）**：所有营收、销售额、客单价、复购率等指标，请使用全局筛选器或计算字段过滤 `order_status IN ('已完成', '待发货', '已发货')`。待付款、已取消、退货中、已退款订单不计入收入。

---

## 看板1：销售运营总览 (Sales Overview Dashboard)

### 目的
展示核心业务KPI，适合管理者快速了解业务状况

### KPI指标卡（顶部）
| 指标 | 计算字段 | 显示格式 |
|------|---------|---------|
| 总销售额(GMV) | `SUM([actual_amount])` | 货币(万元) |
| 总订单数 | `COUNTD([order_id])` | 数字(千) |
| 平均客单价 | `SUM([actual_amount])/COUNTD([order_id])` | 货币 |
| 活跃用户数 | `COUNTD([user_id])` | 数字 |
| 好评率 | `SUM(IIF([rating]>=4,1,0))/COUNT([rating])` | 百分比 |
| 退货率 | `SUM(IIF([order_status]='退货中',1,0))/COUNT([order_id])` | 百分比 |

### 图表组件
1. **月度销售趋势** (折线图)
   - 列: `MONTH(order_date)` (连续)
   - 行: `SUM(actual_amount)`
   - 颜色: 按年份区分
   - 添加趋势线和预测

2. **商品品类销售占比** (树状图)
   - 大小: `SUM(sales_count)`
   - 颜色: `category`
   - 标签: category + sales_count

3. **省份销售热力图** (地图)
   - 地理角色: 省份
   - 颜色: `SUM(actual_amount)` (红-绿发散色阶)
   - 标签: 省份名称 + 销售额

4. **支付方式分布** (环形图)
   - 角度: `COUNT(order_id)`
   - 颜色: `payment_method`

### 筛选器
- 日期范围 (滑块)
- 商品品类 (多选下拉)
- 会员等级 (多选下拉)
- 订单状态 (多选下拉)

---

## 看板2：用户分析 (Customer Analytics Dashboard)

### 图表组件
1. **用户RFM分布散点图**
   - 列: 消费频率 (Frequency)
   - 行: 消费金额 (Monetary)
   - 颜色: 最近消费 (Recency分段)
   - 大小: 订单数
   - 添加参考线区分象限

2. **会员等级消费对比** (分组柱状图)
   - 列: `membership_level`
   - 行: `AVG(total_spent)`
   - 颜色: `gender`

3. **用户年龄分布** (直方图)
   - 列: `age` (数据桶)
   - 行: `COUNT(user_id)`

4. **省份用户分布** (符号地图)
   - 大小: `COUNT(user_id)`
   - 颜色: `AVG(total_spent)`

5. **用户生命周期分析** (面积图)
   - 列: `account_age_days` (数据桶)
   - 行: `COUNT(user_id)`
   - 颜色: `membership_level`

### 筛选器
- 省份 (多选)
- 年龄范围 (滑块)
- 会员等级

---

## 看板3：商品分析 (Product Analytics Dashboard)

### 图表组件
1. **商品销量排名** (条形图)
   - 行: `product_name` (Top 20)
   - 列: `SUM(sales_count)`
   - 颜色: `category`

2. **品类利润率对比** (散点图)
   - 列: `SUM(sales_count)`
   - 行: `AVG(price - cost_price)`
   - 颜色: `category`
   - 大小: `COUNT(review_id)`

3. **评分与销量关系** (气泡图)
   - 列: `rating_avg`
   - 行: `sales_count`
   - 大小: `stock_quantity`
   - 颜色: `category`

4. **品牌市场份额** (堆叠柱状图)
   - 列: `brand`
   - 行: `SUM(sales_count)`
   - 颜色: `category`

5. **库存预警表** (交叉表/高亮表)
   - 行: `product_name`
   - 颜色: `stock_quantity` (红-绿)
   - 筛选: `stock_quantity < 100 AND sales_count > 1000`

### 筛选器
- 商品品类、品牌、价格区间、评分区间

---

## 看板4：评论分析 (Review Analysis Dashboard)

### 图表组件
1. **评分分布** (柱状图)
   - 列: `rating`
   - 行: `COUNT(review_id)`
   - 颜色: rating (绿-红渐变)

2. **各品类平均评分** (雷达图替代：横向柱状图)
   - 行: `category`
   - 列: `AVG(rating)`
   - 参考线: 总体平均评分

3. **评论数时间趋势** (面积图)
   - 列: `MONTH(review_date)`
   - 行: `COUNT(review_id)`
   - 颜色: `rating分段`

4. **认证购买 vs 非认证评分对比** (箱线图)
   - 列: `is_verified_purchase`
   - 行: `rating`

### 筛选器
- 评论日期、评分范围、品类

---

## Tableau 技巧提示

### 计算字段示例
```tableau
// RFM-Recency分数
IF DATEDIFF('day', [last_order_date], TODAY()) <= 30 THEN 5
ELSEIF DATEDIFF('day', [last_order_date], TODAY()) <= 90 THEN 4
ELSEIF DATEDIFF('day', [last_order_date], TODAY()) <= 180 THEN 3
ELSEIF DATEDIFF('day', [last_order_date], TODAY()) <= 365 THEN 2
ELSE 1
END

// 客户价值分段
IF [total_spent] >= 5000 THEN "高价值"
ELSEIF [total_spent] >= 1500 THEN "中价值"
ELSEIF [total_spent] >= 500 THEN "普通"
ELSE "低价值"
END

// 同比销售额增长
(ZN(SUM([actual_amount])) - LOOKUP(ZN(SUM([actual_amount])), -12)) / 
ABS(LOOKUP(ZN(SUM([actual_amount])), -12))
```

### 仪表板布局建议
- 尺寸: 1200 x 2000 像素 (桌面端)
- 顶部: KPI指标卡 (平铺)
- 中部: 主要图表 (2列布局)
- 底部: 详细表格/交叉表
- 左侧或顶部: 全局筛选器

### 配色方案
- 主色调: #2196F3 (蓝)
- 辅助色: #FF9800 (橙), #4CAF50 (绿), #F44336 (红)
- 背景: #FAFAFA
- 文字: #212121

### 导出与分享
1. **Tableau Public**: 免费发布到云端，可嵌入网页
2. **Tableau Server**: 企业内部部署
3. **Tableau Reader**: 打包为 .twbx 文件分享
4. **图片导出**: 各图表可导出为PNG用于报告

---

## 数据刷新流程

### 重要：.twbx 是打包快照
`工作簿 1.twbx` 是打包工作簿，`data/` 下的 CSV 在打包时被复制进包内
（`Data/data/*.csv`）。**重新生成 data/ 目录的 CSV 后，Tableau 不会自动感知**——
必须重新打包，看板才会读到新数据。

### ⚠️ 先关闭 Tableau，再打包！
如果 Tableau Desktop 正开着这个工作簿，它的会话里保存着旧数据源
（提取文件 + 指向临时解压目录的路径）。此时任何打包操作都会被
Tableau 再次保存时覆盖，导致工作簿损坏（报"未找到文件"错误）。
**顺序必须是：关 Tableau → 打包 → 重新打开。**

### 推荐流程（脚本一键刷新）
```
1. 完全退出 Tableau Desktop（工作簿不保存）
2. python data/generate_data.py            # 重新生成数据（或更新 CSV）
3. python tableau/refresh_twbx.py          # 自动备份并重打包 .twbx
4. 重新打开 Tableau 工作簿                 # 看到新数据
```
`refresh_twbx.py` 会把最新 5 张 CSV 替换进包内，并校验客单价确认成功。

### 手动流程（Tableau 内操作）
```
1. 在 Tableau 中打开 .twbx
2. 数据 → 编辑数据源 → 将每个数据源的文件路径指向 data/ 目录下的新 CSV
3. 文件 → 另存为 .twbx（重新打包）
```
若连接方式为「数据提取(.hyper)」：数据 → 刷新数据提取 即可。
建议: 每周更新一次CSV数据后执行上述流程
