#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据集构建脚本 (NovelMart E-Commerce Dataset)
构建包含用户、商品、订单、订单明细、评论等表的电商分析数据集
数据量：用户10,000+，商品5,000+，订单50,000+，订单明细150,000+，评论30,000+
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import math
import os
import sys

# Windows 控制台默认 GBK，统一改为 UTF-8 输出避免中文乱码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# 设置随机种子，确保数据可复现
# ============================================================
np.random.seed(42)
random.seed(42)

# ============================================================
# 配置参数
# ============================================================
N_USERS = 12000
N_PRODUCTS = 5000
N_ORDERS = 55000
N_REVIEWS = 35000

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 基础数据字典
# ============================================================
PROVINCES = [
    '北京', '上海', '广东', '浙江', '江苏', '四川', '湖北', '湖南', '福建', '山东',
    '河南', '河北', '辽宁', '陕西', '重庆', '安徽', '江西', '天津', '云南', '贵州',
    '广西', '山西', '吉林', '黑龙江', '内蒙古', '甘肃', '海南', '新疆', '宁夏', '青海', '西藏'
]

CITIES = {
    '北京': ['朝阳区', '海淀区', '丰台区', '东城区', '西城区', '通州区', '大兴区'],
    '上海': ['浦东新区', '徐汇区', '静安区', '黄浦区', '长宁区', '杨浦区', '闵行区'],
    '广东': ['广州', '深圳', '东莞', '佛山', '珠海', '惠州', '中山'],
    '浙江': ['杭州', '宁波', '温州', '嘉兴', '湖州', '绍兴', '金华'],
    '江苏': ['南京', '苏州', '无锡', '常州', '南通', '徐州', '扬州'],
    '四川': ['成都', '绵阳', '德阳', '宜宾', '南充', '泸州'],
    '湖北': ['武汉', '宜昌', '襄阳', '荆州', '黄石', '十堰'],
    '湖南': ['长沙', '株洲', '湘潭', '衡阳', '岳阳', '常德'],
    '福建': ['福州', '厦门', '泉州', '漳州', '莆田', '龙岩'],
    '山东': ['济南', '青岛', '烟台', '潍坊', '临沂', '淄博', '威海'],
    '河南': ['郑州', '洛阳', '开封', '南阳', '许昌', '新乡'],
    '河北': ['石家庄', '唐山', '保定', '邯郸', '廊坊', '沧州'],
    '辽宁': ['沈阳', '大连', '鞍山', '抚顺', '锦州', '营口'],
    '陕西': ['西安', '咸阳', '宝鸡', '渭南', '延安', '汉中'],
    '重庆': ['渝中区', '江北区', '南岸区', '沙坪坝区', '九龙坡区', '渝北区'],
    '安徽': ['合肥', '芜湖', '蚌埠', '淮南', '马鞍山', '安庆'],
    '江西': ['南昌', '九江', '景德镇', '赣州', '宜春', '上饶'],
    '天津': ['和平区', '南开区', '河西区', '河东区', '河北区', '滨海新区'],
    '云南': ['昆明', '大理', '丽江', '曲靖', '玉溪', '保山'],
    '贵州': ['贵阳', '遵义', '六盘水', '安顺', '毕节', '铜仁'],
    '广西': ['南宁', '柳州', '桂林', '梧州', '北海', '玉林'],
    '山西': ['太原', '大同', '阳泉', '长治', '晋城', '临汾'],
    '吉林': ['长春', '吉林', '四平', '辽源', '通化', '白山'],
    '黑龙江': ['哈尔滨', '齐齐哈尔', '牡丹江', '佳木斯', '大庆', '鸡西'],
    '内蒙古': ['呼和浩特', '包头', '赤峰', '通辽', '鄂尔多斯', '呼伦贝尔'],
    '甘肃': ['兰州', '天水', '白银', '酒泉', '张掖', '武威'],
    '海南': ['海口', '三亚', '儋州', '琼海', '文昌', '万宁'],
    '新疆': ['乌鲁木齐', '克拉玛依', '吐鲁番', '哈密', '昌吉', '库尔勒'],
    '宁夏': ['银川', '石嘴山', '吴忠', '固原', '中卫'],
    '青海': ['西宁', '海东', '格尔木', '德令哈'],
    '西藏': ['拉萨', '日喀则', '昌都', '林芝', '山南']
}

CATEGORIES = {
    '电子产品': ['手机', '笔记本电脑', '平板电脑', '耳机', '智能手表', '相机', '音箱', '移动硬盘', '充电宝', '显示器',
               '键盘', '鼠标', '路由器', '打印机', '投影仪', '智能家居设备', '游戏主机', '数据线', '内存卡', 'VR设备'],
    '服装鞋帽': ['男装T恤', '女装连衣裙', '牛仔裤', '运动鞋', '羽绒服', '衬衫', '休闲裤', '卫衣', '高跟鞋', '运动外套',
               '内衣', '袜子', '围巾', '帽子', '太阳镜', '皮带', '睡衣', '泳衣', '汉服', '西装'],
    '食品饮料': ['坚果零食', '茶叶', '咖啡', '巧克力', '方便面', '蜂蜜', '进口饼干', '饮料', '牛奶', '保健品',
               '调味料', '大米', '食用油', '红酒', '糖果', '薯片', '果冻', '肉干', '燕窝', '蛋白粉'],
    '美妆个护': ['面霜', '口红', '粉底液', '洗面奶', '面膜', '香水', '眼影盘', '防晒霜', '洗发水', '沐浴露',
               '护手霜', '指甲油', '卸妆水', '化妆刷', '美容仪', '染发剂', '身体乳', '眉笔', '定妆喷雾', '精华液'],
    '家居生活': ['床上四件套', '沙发', '餐桌', '灯具', '窗帘', '地毯', '收纳箱', '厨房刀具', '保温杯', '雨伞',
               '抱枕', '晾衣架', '垃圾桶', '空气净化器', '加湿器', '电风扇', '吸尘器', '洗碗机', '微波炉', '电饭煲'],
    '图书文娱': ['小说', '经管书籍', '英语教材', '考研资料', '漫画', '儿童绘本', '科幻小说', '历史书籍', '心理学', '编程书籍',
               '文具', '笔记本', '钢笔', '书法字帖', '拼图', '乐器', '围棋', '瑜伽垫', '健身器材', '篮球'],
    '母婴用品': ['纸尿裤', '婴儿奶粉', '奶瓶', '婴儿推车', '儿童安全座椅', '婴儿湿巾', '童装', '积木玩具', '婴儿沐浴露', '辅食机',
               '婴儿床', '爬行垫', '儿童水杯', '摇铃', '早教机', '婴儿背带', '温奶器', '儿童牙刷', '游泳圈', '儿童帐篷'],
}

BRANDS = {
    '电子产品': ['华为', '苹果', '小米', '三星', 'OPPO', 'vivo', '联想', '索尼', '戴尔', 'BOSE', '罗技', '雷蛇', '华硕', '佳能', '尼康'],
    '服装鞋帽': ['耐克', '阿迪达斯', '优衣库', 'ZARA', 'H&M', '李宁', '安踏', '海澜之家', '波司登', '太平鸟', 'UR', '森马', '鸿星尔克', '特步', '匡威'],
    '食品饮料': ['三只松鼠', '良品铺子', '百草味', '恰恰', '来伊份', '星巴克', '雀巢', '伊利', '蒙牛', '农夫山泉', '茅台', '五粮液', '张裕', '德芙', '费列罗'],
    '美妆个护': ['兰蔻', '雅诗兰黛', '欧莱雅', 'SK-II', '资生堂', '完美日记', '花西子', '百雀羚', '自然堂', '玉兰油', 'MAC', '迪奥', '香奈儿', '雪花秀', '倩碧'],
    '家居生活': ['宜家', '无印良品', '网易严选', '苏泊尔', '美的', '九阳', '格力', '海尔', '戴森', '双立人', '膳魔师', '爱仕达', '奥克斯', '方太', '老板电器'],
    '图书文娱': ['人民文学', '中信出版', '机械工业', '电子工业', '新东方', '得到', '樊登读书', '知乎', '当当', '京东图书'],
    '母婴用品': ['花王', '帮宝适', '惠氏', '美赞臣', '贝亲', '好孩子', 'babycare', '全棉时代', '子初', '可优比', '英氏', '飞鹤', '爱他美', '好奇', '启赋'],
}

# 各子类商品的实际售价区间 (min, max)，参考主流电商平台同品类真实定价。
# 注意：按子品类而非品牌定价，避免"数据线/袜子"这类低价品被品牌区间拉高到上万元。
SUBCAT_PRICE_RANGE = {
    '电子产品': {
        '手机': (699, 8999), '笔记本电脑': (2499, 16999), '平板电脑': (899, 7999),
        '耳机': (29, 1999), '智能手表': (199, 3999), '相机': (999, 15999),
        '音箱': (49, 2999), '移动硬盘': (199, 1299), '充电宝': (29, 299),
        '显示器': (499, 4999), '键盘': (29, 999), '鼠标': (19, 599),
        '路由器': (49, 999), '打印机': (299, 2999), '投影仪': (999, 9999),
        '智能家居设备': (99, 2999), '游戏主机': (1299, 5999), '数据线': (5, 99),
        '内存卡': (19, 399), 'VR设备': (499, 4999),
    },
    '服装鞋帽': {
        '男装T恤': (29, 399), '女装连衣裙': (59, 999), '牛仔裤': (59, 699),
        '运动鞋': (99, 1499), '羽绒服': (199, 2999), '衬衫': (49, 599),
        '休闲裤': (39, 499), '卫衣': (49, 599), '高跟鞋': (99, 899),
        '运动外套': (99, 1299), '内衣': (19, 199), '袜子': (5, 99),
        '围巾': (19, 299), '帽子': (19, 199), '太阳镜': (29, 599),
        '皮带': (29, 299), '睡衣': (39, 299), '泳衣': (39, 399),
        '汉服': (99, 1299), '西装': (199, 2999),
    },
    '食品饮料': {
        '坚果零食': (9.9, 199), '茶叶': (29, 999), '咖啡': (19, 399),
        '巧克力': (9.9, 199), '方便面': (2, 50), '蜂蜜': (19, 299),
        '进口饼干': (9.9, 99), '饮料': (3, 30), '牛奶': (10, 99),
        '保健品': (29, 999), '调味料': (3, 50), '大米': (15, 199),
        '食用油': (20, 199), '红酒': (39, 999), '糖果': (5, 99),
        '薯片': (3, 30), '果冻': (3, 30), '肉干': (19, 199),
        '燕窝': (199, 2999), '蛋白粉': (99, 799),
    },
    '美妆个护': {
        '面霜': (49, 999), '口红': (19, 399), '粉底液': (39, 699),
        '洗面奶': (19, 299), '面膜': (19, 299), '香水': (49, 1299),
        '眼影盘': (29, 599), '防晒霜': (29, 399), '洗发水': (19, 299),
        '沐浴露': (15, 199), '护手霜': (9.9, 199), '指甲油': (9.9, 199),
        '卸妆水': (19, 299), '化妆刷': (9.9, 199), '美容仪': (199, 2999),
        '染发剂': (19, 199), '身体乳': (19, 299), '眉笔': (9.9, 199),
        '定妆喷雾': (19, 299), '精华液': (59, 1299),
    },
    '家居生活': {
        '床上四件套': (99, 1999), '沙发': (499, 9999), '餐桌': (199, 3999),
        '灯具': (29, 999), '窗帘': (59, 999), '地毯': (49, 1999),
        '收纳箱': (9.9, 199), '厨房刀具': (29, 499), '保温杯': (19, 399),
        '雨伞': (9.9, 199), '抱枕': (9.9, 199), '晾衣架': (9.9, 99),
        '垃圾桶': (5, 99), '空气净化器': (299, 4999), '加湿器': (29, 499),
        '电风扇': (49, 999), '吸尘器': (199, 3999), '洗碗机': (999, 6999),
        '微波炉': (199, 1999), '电饭煲': (99, 1499),
    },
    '图书文娱': {
        '小说': (9.9, 99), '经管书籍': (19, 199), '英语教材': (15, 299),
        '考研资料': (29, 599), '漫画': (5, 50), '儿童绘本': (9.9, 99),
        '科幻小说': (9.9, 99), '历史书籍': (15, 199), '心理学': (15, 199),
        '编程书籍': (29, 299), '文具': (1, 50), '笔记本': (3, 99),
        '钢笔': (19, 1999), '书法字帖': (5, 99), '拼图': (9.9, 199),
        '乐器': (99, 9999), '围棋': (19, 299), '瑜伽垫': (29, 299),
        '健身器材': (19, 1999), '篮球': (39, 599),
    },
    '母婴用品': {
        '纸尿裤': (39, 399), '婴儿奶粉': (99, 999), '奶瓶': (19, 299),
        '婴儿推车': (199, 2999), '儿童安全座椅': (499, 3999), '婴儿湿巾': (9.9, 99),
        '童装': (29, 399), '积木玩具': (19, 599), '婴儿沐浴露': (19, 199),
        '辅食机': (99, 999), '婴儿床': (299, 2999), '爬行垫': (39, 499),
        '儿童水杯': (19, 199), '摇铃': (9.9, 99), '早教机': (49, 899),
        '婴儿背带': (29, 299), '温奶器': (49, 399), '儿童牙刷': (5, 99),
        '游泳圈': (19, 199), '儿童帐篷': (99, 999),
    },
}

# 品牌溢价系数：高端品牌略提价、性价比品牌略降价，未列出的品牌按 1.0
BRAND_FACTOR = {
    '苹果': 1.30, '索尼': 1.15, 'BOSE': 1.20, '戴森': 1.20, '双立人': 1.15,
    '茅台': 1.20, 'SK-II': 1.20, '香奈儿': 1.25, '迪奥': 1.20, '兰蔻': 1.15,
    '小米': 0.80, '安踏': 0.85, '完美日记': 0.85, '花西子': 0.90, '宜家': 0.90,
}

# 中文姓名库
SURNAMES = ['张', '李', '王', '陈', '刘', '杨', '黄', '赵', '周', '吴', '徐', '孙', '马', '朱', '胡',
            '林', '郭', '何', '高', '罗', '郑', '梁', '谢', '宋', '唐', '许', '韩', '冯', '邓', '曹',
            '彭', '曾', '萧', '田', '董', '潘', '袁', '于', '蒋', '蔡', '余', '杜', '叶', '程', '苏',
            '魏', '吕', '丁', '任', '沈', '姚', '卢', '姜', '崔', '钟', '谭', '陆', '汪', '范', '金',
            '石', '廖', '贾', '夏', '韦', '付', '方', '白', '邹', '孟', '熊', '秦', '邱', '江', '尹',
            '薛', '闫', '段', '雷', '侯', '尤', '龙', '史', '陶', '黎', '贺', '顾', '毛', '郝', '龚',
            '邵', '万', '钱', '严', '覃', '武', '戴', '莫', '孔', '向', '汤', '温', '康', '施', '文']

GIVEN_NAMES_MALE = ['伟', '强', '磊', '洋', '勇', '军', '杰', '涛', '明', '超', '华', '鹏', '飞', '刚', '平',
                    '辉', '龙', '威', '健', '博', '文', '亮', '宇', '浩', '新', '彬', '鑫', '毅', '俊', '帅']
GIVEN_NAMES_FEMALE = ['芳', '敏', '静', '丽', '婷', '雪', '艳', '娟', '霞', '红', '玲', '蕾', '颖', '慧', '莉',
                      '婷', '萍', '梅', '洁', '雯', '秀英', '晶晶', '晓燕', '美玲', '佳怡', '思琪', '雨桐', '梓涵']

PAYMENT_METHODS = ['支付宝', '微信支付', '银行卡', '货到付款', '花呗分期', '京东白条']
PAYMENT_WEIGHTS = [0.35, 0.30, 0.15, 0.05, 0.10, 0.05]

SHIPPING_METHODS = ['普通快递', '加急快递', '当日达', '自提']
SHIPPING_WEIGHTS = [0.50, 0.25, 0.10, 0.15]

ORDER_STATUSES = ['已完成', '待发货', '已发货', '待付款', '已取消', '退货中', '已退款']
ORDER_STATUS_WEIGHTS = [0.55, 0.10, 0.12, 0.08, 0.08, 0.04, 0.03]

# 有效订单：已付款且未取消/未退款的状态
# 所有营收/消费/RFM/留存等分析都应基于该口径，避免把未支付、取消、退款订单计入收入
VALID_ORDER_STATUSES = ['已完成', '待发货', '已发货']

MEMBERSHIP_LEVELS = ['普通会员', '银卡会员', '金卡会员', '钻石会员']
MEMBERSHIP_WEIGHTS = [0.50, 0.28, 0.15, 0.07]

REVIEW_TEMPLATES_POSITIVE = [
    "非常好用，{attr}很出色，推荐购买！",
    "质量很好，{attr}超出预期，物流也快。",
    "性价比很高，{attr}完全满足需求。",
    "第二次购买了，{attr}一如既往地好。",
    "包装精美，{attr}很棒，会回购的。",
    "朋友推荐的，果然不错，{attr}很满意。",
    "用了一段时间了，{attr}表现稳定。",
    "比实体店便宜，{attr}品质也没话说。",
    "很满意的一次购物，{attr}令人惊喜。",
    "品牌就是品牌，{attr}确实不一样。",
]

REVIEW_TEMPLATES_NEUTRAL = [
    "还行吧，{attr}中规中矩，对得起价格。",
    "一般般，{attr}没有想象中好，但也不差。",
    "凑合能用，{attr}有待改进。",
    "性价比一般，{attr}勉强可以接受。",
    "没什么特别的，{attr}正常水平。",
]

REVIEW_TEMPLATES_NEGATIVE = [
    "不太满意，{attr}和描述有差距。",
    "质量一般，{attr}有点让人失望。",
    "物流太慢了，{attr}也不够好。",
    "包装破损了，{attr}也受影响。",
    "性价比不高，{attr}不值这个价。",
    "有色差/尺寸偏差，{attr}不够精确。",
    "用了几次就出问题了，{attr}质量堪忧。",
    "跟图片不一样，{attr}严重不符描述。",
    "太失望了，{attr}完全是劣质产品。",
    "不建议购买，{attr}存在明显缺陷。",
]

POSITIVE_ATTRS = ['品质', '做工', '材质', '颜色', '外观设计', '手感', '效果', '功能', '性能', '舒适度']
NEUTRAL_ATTRS = ['整体表现', '使用体验', '综合感受', '实际效果', '日常使用']
NEGATIVE_ATTRS = ['做工细节', '用料', '耐用性', '精确度', '色差问题', '质感', '包装', '售后服务', '物流速度', '使用说明']


def generate_users(n=N_USERS):
    """生成用户数据"""
    print(f"正在生成 {n} 条用户数据...")
    user_ids = np.arange(1, n + 1)
    genders = np.random.choice(['男', '女', '未知'], n, p=[0.48, 0.48, 0.04])
    ages = np.random.randint(16, 72, n)
    # 添加年龄的合理分布
    ages = np.concatenate([np.random.randint(18, 35, int(n * 0.45)),
                          np.random.randint(25, 45, int(n * 0.30)),
                          np.random.randint(35, 60, int(n * 0.20)),
                          np.random.randint(14, 70, int(n * 0.05))])[:n]
    np.random.shuffle(ages)

    province_list = list(CITIES.keys())
    # Use population-weighted probabilities, normalized
    province_weights = np.array([12, 10, 10, 7, 7, 6, 6, 5, 5, 4,
                                 3, 3, 3, 3, 2, 2, 2, 2, 1, 1,
                                 1, 1, 1, 1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
    province_probs = province_weights / province_weights.sum()
    provinces = np.random.choice(province_list, n, p=province_probs)
    cities = [random.choice(CITIES[p]) for p in provinces]

    reg_start = datetime(2018, 1, 1)
    reg_end = datetime(2025, 12, 31)
    reg_days = (reg_end - reg_start).days
    reg_dates = [reg_start + timedelta(days=int(x)) for x in np.random.randint(0, reg_days, n)]

    membership = np.random.choice(MEMBERSHIP_LEVELS, n, p=MEMBERSHIP_WEIGHTS)

    # 根据会员等级调整消费金额
    base_spent = {'普通会员': (0, 2000), '银卡会员': (500, 10000),
                 '金卡会员': (2000, 30000), '钻石会员': (5000, 100000)}

    usernames = []
    real_names = []
    for i in range(n):
        surname = random.choice(SURNAMES)
        if genders[i] == '女':
            gname = random.choice(GIVEN_NAMES_FEMALE)
            if random.random() < 0.3:
                gname = random.choice(GIVEN_NAMES_FEMALE) + random.choice(GIVEN_NAMES_FEMALE)
        else:
            gname = random.choice(GIVEN_NAMES_MALE)
            if random.random() < 0.3:
                gname = random.choice(GIVEN_NAMES_MALE) + random.choice(GIVEN_NAMES_MALE)
        real_names.append(surname + gname)
        usernames.append(f"user_{user_ids[i]:06d}")

    phones = ['1' + str(random.choice([3, 4, 5, 6, 7, 8, 9])) + ''.join([str(random.randint(0, 9)) for _ in range(9)]) for _ in range(n)]

    emails = [f"{username}@{random.choice(['qq.com', '163.com', 'gmail.com', 'outlook.com', '126.com', 'sina.com'])}" for username in usernames]

    df = pd.DataFrame({
        'user_id': user_ids,
        'username': usernames,
        'real_name': real_names,
        'email': emails,
        'phone': phones,
        'gender': genders,
        'age': ages,
        'province': provinces,
        'city': cities,
        'registration_date': reg_dates,
        'membership_level': membership,
    })
    return df


def generate_products(n=N_PRODUCTS):
    """生成商品数据"""
    print(f"正在生成 {n} 条商品数据...")
    product_ids = np.arange(1, n + 1)

    categories = []
    subcategories = []
    brands = []
    prices = []
    costs = []
    for i in range(n):
        cat = random.choice(list(CATEGORIES.keys()))
        subcat = random.choice(CATEGORIES[cat])
        brand = random.choice(BRANDS.get(cat, ['其他品牌']))

        # 价格按子品类实际售价区间设定，对数均匀采样（价格集中在常见中低价位，少量高价）
        price_range = SUBCAT_PRICE_RANGE.get(cat, {}).get(subcat, (9.9, 999))
        lo, hi = price_range
        price = math.exp(random.uniform(math.log(lo), math.log(hi)))
        # 品牌溢价/折扣系数微调
        price *= BRAND_FACTOR.get(brand, 1.0)
        price = round(price, 2)
        cost_ratio = random.uniform(0.25, 0.75)
        cost = round(price * cost_ratio, 2)

        categories.append(cat)
        subcategories.append(subcat)
        brands.append(brand)
        prices.append(price)
        costs.append(cost)

    # 生成商品名称
    # 注意：品牌放在独立字段中，商品名不再拼接品牌，避免出现“机械工业 文具”“茅台 薯片”等品牌-子类错配名称
    colors = ['黑', '白', '红', '蓝', '银', '金', '灰', '粉']
    editions = ['经典款', '新款', '升级版', 'Pro', 'Plus', '青春版', '旗舰版', '标准版', '限定版', '']
    product_names = []
    for i in range(n):
        edition = random.choice(editions)
        color_suffix = ''
        if random.random() < 0.4:
            color_suffix = '(' + random.choice(colors) + '色)'
        name = subcategories[i] + ' ' + edition + color_suffix
        product_names.append(name.strip())

    # 初始库存和销量
    stock_quantities = np.random.randint(0, 5000, n)
    sales_counts = np.random.randint(0, 20000, n)
    # 热门商品的库存偏少，销量偏高
    for i in range(n):
        if random.random() < 0.15:  # 15%是爆款
            stock_quantities[i] = np.random.randint(0, 500)
            sales_counts[i] = np.random.randint(5000, 30000)
        elif random.random() < 0.10:  # 10%是滞销品
            stock_quantities[i] = np.random.randint(2000, 5000)
            sales_counts[i] = np.random.randint(0, 50)

    rating_avgs = np.round(np.clip(np.random.normal(4.0, 0.8, n), 1.0, 5.0), 1)

    listing_start = datetime(2019, 1, 1)
    listing_end = datetime(2025, 6, 30)
    listing_days = (listing_end - listing_start).days
    listing_dates = [listing_start + timedelta(days=int(x)) for x in np.random.randint(0, listing_days, n)]

    # 商品状态：大部分在售，少数缺货或下架
    statuses = np.random.choice(['在售', '下架', '缺货'], n, p=[0.82, 0.10, 0.08])

    df = pd.DataFrame({
        'product_id': product_ids,
        'product_name': product_names,
        'category': categories,
        'subcategory': subcategories,
        'brand': brands,
        'price': prices,
        'cost_price': costs,
        'stock_quantity': stock_quantities,
        'sales_count': sales_counts,
        'rating_avg': rating_avgs,
        'listing_date': listing_dates,
        'status': statuses,
    })
    return df


def generate_orders(users_df, n=N_ORDERS):
    """生成订单数据"""
    print(f"正在生成 {n} 条订单数据...")
    order_ids = np.arange(1, n + 1)

    # 高频用户更可能下单
    user_probs = np.ones(len(users_df))
    # 高等级会员下单概率更高
    for i, level in enumerate(users_df['membership_level']):
        if level == '钻石会员':
            user_probs[i] = 3.0
        elif level == '金卡会员':
            user_probs[i] = 2.0
        elif level == '银卡会员':
            user_probs[i] = 1.5
    user_probs = user_probs / user_probs.sum()

    user_ids = np.random.choice(users_df['user_id'].values, n, p=user_probs)

    # 订单日期集中在近两年
    order_start = datetime(2024, 1, 1)
    order_end = datetime(2026, 6, 30)
    order_days = (order_end - order_start).days
    # 使用有界指数分布让订单更集中在近期
    # 注意：不要用 np.clip 把超界值压到边界，否则会在最早日期产生大量订单堆积（2024-01 异常尖峰）
    raw_days = np.random.exponential(scale=order_days * 0.35, size=n)
    out_of_range = raw_days > order_days
    while out_of_range.any():
        raw_days[out_of_range] = np.random.exponential(scale=order_days * 0.35, size=int(out_of_range.sum()))
        out_of_range = raw_days > order_days
    raw_days = raw_days.astype(int)
    order_dates = [order_end - timedelta(days=int(x)) for x in raw_days]
    order_dates.sort(reverse=True)

    # 保证下单时间不早于用户注册时间，避免出现 first_order_date < registration_date 的逻辑矛盾
    user_reg = users_df.set_index('user_id')['registration_date'].to_dict()
    for i, uid in enumerate(user_ids):
        reg = user_reg.get(uid)
        if reg is not None and order_dates[i] < reg:
            span = max(1, (order_end - reg).days)
            offset = int(np.random.exponential(scale=span * 0.35))
            offset = min(offset, span)
            order_dates[i] = reg + timedelta(days=offset)

    # 支付方式
    payment_methods = np.random.choice(PAYMENT_METHODS, n, p=PAYMENT_WEIGHTS)
    shipping_methods = np.random.choice(SHIPPING_METHODS, n, p=SHIPPING_WEIGHTS)
    order_statuses = np.random.choice(ORDER_STATUSES, n, p=ORDER_STATUS_WEIGHTS)

    # 运费
    shipping_costs = np.zeros(n)
    for i, method in enumerate(shipping_methods):
        if method == '普通快递':
            shipping_costs[i] = round(np.random.choice([0, 5, 8, 10, 12, 15], p=[0.4, 0.2, 0.15, 0.1, 0.1, 0.05]), 2)
        elif method == '加急快递':
            shipping_costs[i] = round(np.random.uniform(12, 30), 2)
        elif method == '当日达':
            shipping_costs[i] = round(np.random.uniform(25, 50), 2)
        else:
            shipping_costs[i] = 0

    # 用户省份城市映射
    user_map = users_df.set_index('user_id')[['province', 'city']].to_dict('index')
    provinces = []
    cities = []
    for uid in user_ids:
        info = user_map.get(uid, {'province': '北京', 'city': '朝阳区'})
        provinces.append(info['province'])
        cities.append(info['city'])

    df = pd.DataFrame({
        'order_id': order_ids,
        'user_id': user_ids,
        'order_date': order_dates,
        'payment_method': payment_methods,
        'shipping_method': shipping_methods,
        'shipping_cost': shipping_costs,
        'order_status': order_statuses,
        'shipping_province': provinces,
        'shipping_city': cities,
    })
    return df


def generate_order_items(orders_df, products_df):
    """生成订单明细数据"""
    print(f"正在生成订单明细数据...")
    items = []
    item_id = 1

    product_prices = products_df.set_index('product_id')['price'].to_dict()
    product_categories = products_df.set_index('product_id')['category'].to_dict()

    # 商品购买概率与价格负相关（需求曲线）：低价日用品购买频次高，高价大件购买频次低。
    # 幂律权重 p^-0.9，经模拟验证可使实际成交商品均价约 ¥55、客单价约 ¥300，符合主流电商水平
    product_weights = products_df['price'].values ** -0.9
    product_weights = product_weights / product_weights.sum()

    for _, order in orders_df.iterrows():
        order_id = order['order_id']
        # 每单1-8件商品，大多数2-4件
        n_items = int(np.random.choice([1, 2, 3, 4, 5, 6, 7, 8],
                                       p=[0.08, 0.22, 0.25, 0.20, 0.12, 0.07, 0.04, 0.02]))
        # 随机选择商品（热门低价商品更可能被购买）
        selected_products = np.random.choice(products_df['product_id'].values, n_items,
                                             p=product_weights, replace=False)

        for pid in selected_products:
            base_price = product_prices.get(pid, 99)
            # 价格波动：实际售价在基础价格的85%-110%之间
            unit_price = round(base_price * random.uniform(0.85, 1.10), 2)
            quantity = int(np.random.choice([1, 2, 3, 4, 5], p=[0.55, 0.28, 0.10, 0.05, 0.02]))
            # 折扣
            if random.random() < 0.25:
                discount = round(random.uniform(0.05, 0.40), 2)
            else:
                discount = 0.0

            items.append({
                'item_id': item_id,
                'order_id': order_id,
                'product_id': pid,
                'quantity': quantity,
                'unit_price': unit_price,
                'discount': discount,
            })
            item_id += 1

    df = pd.DataFrame(items)

    # 计算订单金额并更新到订单表（向量化，避免 groupby.apply 的弃用警告）
    amount_df = df.assign(
        _line_amount=df['unit_price'] * df['quantity'] * (1 - df['discount']),
        _discount_amount=df['unit_price'] * df['quantity'] * df['discount']
    )
    order_amounts = amount_df.groupby('order_id')['_line_amount'].sum().round(2).to_dict()
    order_discounts = amount_df.groupby('order_id')['_discount_amount'].sum().round(2).to_dict()

    orders_df['total_amount'] = orders_df['order_id'].map(order_amounts).fillna(0)
    orders_df['discount_amount'] = orders_df['order_id'].map(order_discounts).fillna(0)
    orders_df['actual_amount'] = orders_df['total_amount'] - orders_df['discount_amount'] + orders_df['shipping_cost']

    return df, orders_df


def generate_reviews(orders_df, order_items_df, products_df, n=N_REVIEWS):
    """生成评论数据"""
    print(f"正在生成 {n} 条评论数据...")
    # 从已完成订单中筛选
    completed_orders = orders_df[orders_df['order_status'] == '已完成']
    # 从已完成订单的明细中抽样
    completed_items = order_items_df[order_items_df['order_id'].isin(completed_orders['order_id'])]

    if len(completed_items) < n:
        sample_n = len(completed_items)
    else:
        sample_n = n

    sampled = completed_items.sample(n=sample_n, random_state=42) if sample_n > 0 else completed_items

    review_ids = np.arange(1, sample_n + 1)
    ratings = np.random.choice([5, 4, 3, 2, 1], sample_n, p=[0.38, 0.28, 0.18, 0.10, 0.06])

    # 生成评论文本
    review_texts = []
    for i in range(sample_n):
        if ratings[i] >= 4:
            tmpl = random.choice(REVIEW_TEMPLATES_POSITIVE)
            attr = random.choice(POSITIVE_ATTRS)
        elif ratings[i] == 3:
            tmpl = random.choice(REVIEW_TEMPLATES_NEUTRAL)
            attr = random.choice(NEUTRAL_ATTRS)
        else:
            tmpl = random.choice(REVIEW_TEMPLATES_NEGATIVE)
            attr = random.choice(NEGATIVE_ATTRS)
        review_texts.append(tmpl.format(attr=attr))

    # 评论日期在订单日期后1-30天
    order_dates_map = orders_df.set_index('order_id')['order_date'].to_dict()
    review_dates = []
    for oid in sampled['order_id']:
        odate = order_dates_map.get(oid, datetime(2024, 1, 1))
        days_later = np.random.randint(1, 31)
        review_dates.append(odate + timedelta(days=days_later))

    # 是否认证购买
    is_verified = np.random.choice([True, False], sample_n, p=[0.85, 0.15])

    user_ids_map = orders_df.set_index('order_id')['user_id'].to_dict()

    df = pd.DataFrame({
        'review_id': review_ids,
        'user_id': sampled['order_id'].map(user_ids_map).values,
        'product_id': sampled['product_id'].values,
        'order_id': sampled['order_id'].values,
        'rating': ratings,
        'review_text': review_texts,
        'review_date': review_dates,
        'is_verified_purchase': is_verified,
    })
    return df


def add_user_derived_fields(users_df, orders_df, reviews_df):
    """为用户表添加衍生统计字段"""
    print("正在计算用户衍生字段...")

    # 按用户聚合订单统计：只统计有效订单（已付款且未取消/未退款），
    # 避免把待付款、已取消、退货中、已退款订单计入用户消费与订单数
    order_stats = orders_df[orders_df['order_status'].isin(VALID_ORDER_STATUSES)].groupby('user_id').agg(
        total_orders=('order_id', 'count'),
        total_spent=('actual_amount', 'sum'),
        avg_order_value=('actual_amount', 'mean'),
        first_order_date=('order_date', 'min'),
        last_order_date=('order_date', 'max'),
    ).reset_index()

    # 按用户聚合评论统计
    review_stats = reviews_df.groupby('user_id').agg(
        total_reviews=('review_id', 'count'),
        avg_rating_given=('rating', 'mean'),
    ).reset_index()

    # 合并
    users_df = users_df.merge(order_stats, on='user_id', how='left')
    users_df = users_df.merge(review_stats, on='user_id', how='left')

    users_df['total_orders'] = users_df['total_orders'].fillna(0).astype(int)
    users_df['total_spent'] = users_df['total_spent'].fillna(0).round(2)
    users_df['avg_order_value'] = users_df['avg_order_value'].fillna(0).round(2)
    users_df['total_reviews'] = users_df['total_reviews'].fillna(0).astype(int)
    users_df['avg_rating_given'] = users_df['avg_rating_given'].fillna(0).round(1)

    # 计算用户生命周期（天）
    today = datetime(2026, 7, 31)
    users_df['account_age_days'] = (today - users_df['registration_date']).dt.days

    return users_df


def main():
    print("=" * 60)
    print("电商数据集构建工具 (NovelMart)")
    print("=" * 60)

    # 1. 生成用户
    users_df = generate_users(N_USERS)
    print(f"  [OK] 用户: {len(users_df)} 条")

    # 2. 生成商品
    products_df = generate_products(N_PRODUCTS)
    print(f"  [OK] 商品: {len(products_df)} 条")

    # 3. 生成订单
    orders_df = generate_orders(users_df, N_ORDERS)
    print(f"  [OK] 订单基础: {len(orders_df)} 条")

    # 4. 生成订单明细 + 更新订单金额
    order_items_df, orders_df = generate_order_items(orders_df, products_df)
    print(f"  [OK] 订单明细: {len(order_items_df)} 条")

    # 5. 生成评论
    reviews_df = generate_reviews(orders_df, order_items_df, products_df, N_REVIEWS)
    print(f"  [OK] 评论: {len(reviews_df)} 条")

    # 5.5 回填商品真实销量与评分（保持 products 与 order_items/reviews 一致）
    #     说明: sales_count/rating_avg 之前是独立随机数，与订单明细、评论脱节，
    #     这里用实际聚合结果覆盖，保证跨表口径一致
    actual_sales = order_items_df.groupby('product_id')['quantity'].sum()
    products_df['sales_count'] = products_df['product_id'].map(actual_sales).fillna(0).astype(int)

    review_ratings = reviews_df.groupby('product_id')['rating'].mean().round(1)
    # 仅回填有评论的商品；无评论商品保留生成值（与 SQL 校准脚本 C-5 的口径一致）
    has_review_mask = products_df['product_id'].isin(review_ratings.index)
    products_df.loc[has_review_mask, 'rating_avg'] = products_df.loc[has_review_mask, 'product_id'].map(review_ratings)
    print(f"  [OK] 商品表已回填实际销量与评分 (sales_count/rating_avg)")

    # 6. 更新用户衍生字段
    users_df = add_user_derived_fields(users_df, orders_df, reviews_df)
    print(f"  [OK] 用户衍生字段已更新")

    # 7. 输出统计
    print("\n" + "=" * 60)
    print("数据生成完成！数据集统计：")
    print("=" * 60)
    print(f"  用户表:     {len(users_df):>8,} 条")
    print(f"  商品表:     {len(products_df):>8,} 条")
    print(f"  订单表:     {len(orders_df):>8,} 条")
    print(f"  订单明细:   {len(order_items_df):>8,} 条")
    print(f"  评论表:     {len(reviews_df):>8,} 条")
    print(f"  总数据量:   {(len(users_df)+len(products_df)+len(orders_df)+len(order_items_df)+len(reviews_df)):>8,} 条")
    valid_mask = orders_df['order_status'].isin(VALID_ORDER_STATUSES)
    print(f"\n  有效订单数:   {valid_mask.sum():,} 条")
    print(f"  订单总金额(有效): RMB{orders_df.loc[valid_mask, 'actual_amount'].sum():,.2f}")
    print(f"  平均客单价(有效): RMB{orders_df.loc[valid_mask, 'actual_amount'].mean():,.2f}")
    print(f"  商品均价:   RMB{products_df['price'].mean():,.2f}")
    print(f"  平均评分:   {reviews_df['rating'].mean():.2f}")

    # 8. 保存
    print("\n正在保存数据...")
    users_df.to_csv(os.path.join(DATA_DIR, 'users.csv'), index=False, encoding='utf-8-sig')
    products_df.to_csv(os.path.join(DATA_DIR, 'products.csv'), index=False, encoding='utf-8-sig')
    orders_df.to_csv(os.path.join(DATA_DIR, 'orders.csv'), index=False, encoding='utf-8-sig')
    order_items_df.to_csv(os.path.join(DATA_DIR, 'order_items.csv'), index=False, encoding='utf-8-sig')
    reviews_df.to_csv(os.path.join(DATA_DIR, 'reviews.csv'), index=False, encoding='utf-8-sig')
    print("数据已保存到 data/ 目录")

    # 9. 保存数据字典
    data_dict = pd.DataFrame([
        {'表名': 'users', '字段': 'user_id', '类型': 'INT', '说明': '用户唯一标识'},
        {'表名': 'users', '字段': 'username', '类型': 'VARCHAR(50)', '说明': '用户名'},
        {'表名': 'users', '字段': 'real_name', '类型': 'VARCHAR(20)', '说明': '真实姓名'},
        {'表名': 'users', '字段': 'email', '类型': 'VARCHAR(100)', '说明': '电子邮箱'},
        {'表名': 'users', '字段': 'phone', '类型': 'VARCHAR(15)', '说明': '手机号'},
        {'表名': 'users', '字段': 'gender', '类型': 'VARCHAR(4)', '说明': '性别(男/女/未知)'},
        {'表名': 'users', '字段': 'age', '类型': 'INT', '说明': '年龄'},
        {'表名': 'users', '字段': 'province', '类型': 'VARCHAR(20)', '说明': '省份'},
        {'表名': 'users', '字段': 'city', '类型': 'VARCHAR(30)', '说明': '城市/区'},
        {'表名': 'users', '字段': 'registration_date', '类型': 'DATE', '说明': '注册日期'},
        {'表名': 'users', '字段': 'membership_level', '类型': 'VARCHAR(10)', '说明': '会员等级'},
        {'表名': 'users', '字段': 'total_orders', '类型': 'INT', '说明': '累计订单数'},
        {'表名': 'users', '字段': 'total_spent', '类型': 'DECIMAL(12,2)', '说明': '累计消费金额'},
        {'表名': 'users', '字段': 'avg_order_value', '类型': 'DECIMAL(10,2)', '说明': '平均客单价'},
        {'表名': 'users', '字段': 'first_order_date', '类型': 'DATE', '说明': '首次下单日期'},
        {'表名': 'users', '字段': 'last_order_date', '类型': 'DATE', '说明': '最近下单日期'},
        {'表名': 'users', '字段': 'total_reviews', '类型': 'INT', '说明': '累计评论数'},
        {'表名': 'users', '字段': 'avg_rating_given', '类型': 'DECIMAL(3,1)', '说明': '平均给出评分'},
        {'表名': 'users', '字段': 'account_age_days', '类型': 'INT', '说明': '账户年龄(天)'},
        {'表名': 'products', '字段': 'product_id', '类型': 'INT', '说明': '商品唯一标识'},
        {'表名': 'products', '字段': 'product_name', '类型': 'VARCHAR(100)', '说明': '商品名称'},
        {'表名': 'products', '字段': 'category', '类型': 'VARCHAR(20)', '说明': '商品大类'},
        {'表名': 'products', '字段': 'subcategory', '类型': 'VARCHAR(30)', '说明': '商品子类'},
        {'表名': 'products', '字段': 'brand', '类型': 'VARCHAR(30)', '说明': '品牌'},
        {'表名': 'products', '字段': 'price', '类型': 'DECIMAL(10,2)', '说明': '售价'},
        {'表名': 'products', '字段': 'cost_price', '类型': 'DECIMAL(10,2)', '说明': '成本价'},
        {'表名': 'products', '字段': 'stock_quantity', '类型': 'INT', '说明': '库存数量'},
        {'表名': 'products', '字段': 'sales_count', '类型': 'INT', '说明': '累计销量'},
        {'表名': 'products', '字段': 'rating_avg', '类型': 'DECIMAL(3,1)', '说明': '平均评分'},
        {'表名': 'products', '字段': 'listing_date', '类型': 'DATE', '说明': '上架日期'},
        {'表名': 'products', '字段': 'status', '类型': 'VARCHAR(10)', '说明': '商品状态'},
        {'表名': 'orders', '字段': 'order_id', '类型': 'INT', '说明': '订单唯一标识'},
        {'表名': 'orders', '字段': 'user_id', '类型': 'INT', '说明': '用户ID(FK)'},
        {'表名': 'orders', '字段': 'order_date', '类型': 'DATETIME', '说明': '下单时间'},
        {'表名': 'orders', '字段': 'total_amount', '类型': 'DECIMAL(12,2)', '说明': '商品总金额'},
        {'表名': 'orders', '字段': 'discount_amount', '类型': 'DECIMAL(10,2)', '说明': '折扣金额'},
        {'表名': 'orders', '字段': 'actual_amount', '类型': 'DECIMAL(12,2)', '说明': '实付金额'},
        {'表名': 'orders', '字段': 'payment_method', '类型': 'VARCHAR(15)', '说明': '支付方式'},
        {'表名': 'orders', '字段': 'shipping_method', '类型': 'VARCHAR(10)', '说明': '配送方式'},
        {'表名': 'orders', '字段': 'shipping_cost', '类型': 'DECIMAL(8,2)', '说明': '运费'},
        {'表名': 'orders', '字段': 'order_status', '类型': 'VARCHAR(10)', '说明': '订单状态'},
        {'表名': 'orders', '字段': 'shipping_province', '类型': 'VARCHAR(20)', '说明': '收货省份'},
        {'表名': 'orders', '字段': 'shipping_city', '类型': 'VARCHAR(30)', '说明': '收货城市'},
        {'表名': 'order_items', '字段': 'item_id', '类型': 'INT', '说明': '明细唯一标识'},
        {'表名': 'order_items', '字段': 'order_id', '类型': 'INT', '说明': '订单ID(FK)'},
        {'表名': 'order_items', '字段': 'product_id', '类型': 'INT', '说明': '商品ID(FK)'},
        {'表名': 'order_items', '字段': 'quantity', '类型': 'INT', '说明': '购买数量'},
        {'表名': 'order_items', '字段': 'unit_price', '类型': 'DECIMAL(10,2)', '说明': '成交单价'},
        {'表名': 'order_items', '字段': 'discount', '类型': 'DECIMAL(4,2)', '说明': '折扣比例'},
        {'表名': 'reviews', '字段': 'review_id', '类型': 'INT', '说明': '评论唯一标识'},
        {'表名': 'reviews', '字段': 'user_id', '类型': 'INT', '说明': '用户ID(FK)'},
        {'表名': 'reviews', '字段': 'product_id', '类型': 'INT', '说明': '商品ID(FK)'},
        {'表名': 'reviews', '字段': 'order_id', '类型': 'INT', '说明': '订单ID(FK)'},
        {'表名': 'reviews', '字段': 'rating', '类型': 'TINYINT', '说明': '评分(1-5)'},
        {'表名': 'reviews', '字段': 'review_text', '类型': 'TEXT', '说明': '评论内容'},
        {'表名': 'reviews', '字段': 'review_date', '类型': 'DATE', '说明': '评论日期'},
        {'表名': 'reviews', '字段': 'is_verified_purchase', '类型': 'BOOLEAN', '说明': '是否认证购买'},
    ])
    data_dict.to_csv(os.path.join(DATA_DIR, 'data_dictionary.csv'), index=False, encoding='utf-8-sig')
    print("数据字典已保存到 data/data_dictionary.csv")

    print("\n[DONE] 全部完成!")


if __name__ == '__main__':
    main()
