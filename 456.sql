-- 修正版数据库初始化脚本
-- init_database_fixed.sql

-- 1. 删除旧数据库并创建新数据库
DROP DATABASE IF EXISTS campus_secondhand_simple;
CREATE DATABASE campus_secondhand_simple DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campus_secondhand_simple;

-- 2. 创建表（按依赖顺序）
-- 用户表
CREATE TABLE user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    avatar VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 商品类别表
CREATE TABLE category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    INDEX idx_category_name (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 商品表
CREATE TABLE product (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT,
    category_id INT NOT NULL,
    user_id INT NOT NULL,
    images TEXT,
    status TINYINT DEFAULT 1 COMMENT '1-在售, 0-已售, 2-下架',
    publish_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    view_count INT DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES category(category_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id),
    INDEX idx_category (category_id),
    INDEX idx_user (user_id),
    INDEX idx_status (status),
    INDEX idx_publish_time (publish_time DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 收藏表
CREATE TABLE favorites (
    favorite_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE CASCADE,
    UNIQUE KEY unique_favorite (user_id, product_id),
    INDEX idx_user (user_id),
    INDEX idx_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 订单表
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    buyer_id INT NOT NULL,
    seller_id INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    status TINYINT DEFAULT 1 COMMENT '1-待付款, 2-待发货, 3-待收货, 4-已完成, 5-已取消',
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pay_time TIMESTAMP NULL,
    complete_time TIMESTAMP NULL,
    FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES user(user_id) ON DELETE CASCADE,
    INDEX idx_buyer (buyer_id),
    INDEX idx_seller (seller_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 插入测试数据
-- 用户数据
INSERT INTO user (username, password, email, phone) VALUES
('test', '123456', 'test@example.com', '13800138001'),
('admin', 'admin123', 'admin@example.com', '13800138002'),
('张三', '123456', 'zhangsan@example.com', '13800138003'),
('李四', '123456', 'lisi@example.com', '13800138004');

-- 商品类别
INSERT INTO category (category_name, description) VALUES
('书籍', '教材、小说、专业书籍等'),
('电子产品', '手机、电脑、平板等'),
('生活用品', '日常用品、家居用品等'),
('服饰', '衣服、鞋子、配饰等'),
('其他', '其他未分类商品');

-- 商品数据（确保status=1）
INSERT INTO product (product_name, price, description, category_id, user_id, status, view_count) VALUES
('Java编程思想', 45.00, '经典Java编程书籍，九成新，带书签', 1, 1, 1, 10),
('iPhone 12 Pro', 3800.00, '二手手机，功能完好，128GB，蓝色', 2, 2, 1, 25),
('考研数学真题', 20.00, '近5年考研数学真题，含详细解析', 1, 3, 1, 15),
('USB充电式台灯', 25.00, '三档调光，充电式台灯，九成新', 3, 4, 1, 8),
('冬季棉衣', 80.00, 'L码冬季棉衣，保暖性好，只穿过几次', 4, 1, 1, 12),
('二手笔记本电脑', 2500.00, '联想ThinkPad，i5处理器，8GB内存', 2, 2, 1, 30),
('英语四级词汇书', 15.00, '全新未使用，附带记忆卡片', 1, 3, 1, 5),
('篮球', 50.00, '标准7号篮球，手感好', 5, 4, 1, 3);

-- 收藏数据
INSERT INTO favorites (user_id, product_id) VALUES
(1, 2),
(2, 1),
(3, 5),
(4, 3);

-- 订单数据（修正：使用NOW()而不是NOM()）
INSERT INTO orders (product_id, buyer_id, seller_id, price, status, order_time) VALUES
(3, 1, 3, 20.00, 4, DATE_SUB(NOW(), INTERVAL 5 DAY)),
(5, 2, 1, 80.00, 2, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(7, 4, 3, 15.00, 3, DATE_SUB(NOW(), INTERVAL 1 DAY));

-- 4. 验证数据
SELECT '✅ 数据库初始化完成！' as message;
SELECT '📱 测试账号:' as info, 'test/123456, admin/admin123, 张三/123456, 李四/123456' as credentials;
SELECT '🌐 访问地址: http://localhost:5000' as frontend_url;

-- 5. 验证各表数据
SELECT '📊 数据统计:' as title;
SELECT 'user表' as 表名, COUNT(*) as 记录数 FROM user
UNION ALL
SELECT 'category表', COUNT(*) FROM category
UNION ALL
SELECT 'product表', COUNT(*) FROM product
UNION ALL
SELECT 'favorites表', COUNT(*) FROM favorites
UNION ALL
SELECT 'orders表', COUNT(*) FROM orders;