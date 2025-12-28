
from flask import Flask, request, jsonify, make_response, send_from_directory
from flask_cors import CORS
import json
import sys
import os
from datetime import datetime

# 设置系统编码
if sys.version_info[0] >= 3:
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 使用PyMySQL作为MySQLdb的替代
import pymysql

pymysql.install_as_MySQLdb()
import MySQLdb
from MySQLdb import OperationalError, ProgrammingError, IntegrityError
import traceback

# 初始化Flask应用
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'passwd': '123456',
    'db': 'campus_secondhand_simple',
    'charset': 'utf8mb4',
    'autocommit': False
}


# ==================== 辅助函数 ====================
def json_response(data, status_code=200):
    """自定义JSON响应，确保中文不被转义"""
    response = make_response(
        json.dumps(data, ensure_ascii=False, indent=2, separators=(',', ': '))
    )
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.status_code = status_code
    return response


def get_db_connection():
    """获取数据库连接"""
    try:
        conn = MySQLdb.connect(**DB_CONFIG)
        conn.ping(reconnect=True)
        return conn
    except OperationalError as e:
        print(f"数据库连接失败：{str(e)}")
        return None
    except Exception as e:
        print(f"数据库连接异常：{traceback.format_exc()}")
        return None


def close_db_resource(conn, cur):
    """关闭数据库资源"""
    if cur:
        try:
            cur.close()
        except:
            pass
    if conn:
        try:
            conn.close()
        except:
            pass


@app.after_request
def after_request(response):
    """添加CORS头部"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


# ==================== 静态文件服务 ====================
@app.route('/')
def index():
    """默认页面"""
    return send_from_directory('.', 'login.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """静态文件服务"""
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    else:
        return json_response({"code": 404, "message": "文件不存在"}, 404)


# ==================== API接口 ====================
@app.route('/api/health', methods=['GET'])
def health():
    """健康检查接口"""
    return json_response({
        "code": 200,
        "message": "校园二手交易平台API服务器运行正常",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "2.0"
    })


@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    """用户登录"""
    if request.method == 'OPTIONS':
        return json_response({})

    if not request.is_json:
        return json_response({"code": 400, "success": False, "message": "请求格式错误"}, 400)

    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return json_response({"code": 400, "success": False, "message": "用户名/密码不能为空"}, 400)

    conn = get_db_connection()
    if not conn:
        return json_response({"code": 500, "success": False, "message": "数据库连接失败"}, 500)

    cur = None
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, email FROM user WHERE username=%s AND password=%s",
                    (username, password))
        row = cur.fetchone()

        if row:
            user_id, username, email = row
            return json_response({
                "code": 200,
                "success": True,
                "message": "登录成功",
                "user_id": user_id,
                "username": username,
                "email": email
            })
        else:
            return json_response({"code": 401, "success": False, "message": "用户名或密码错误"}, 401)

    except Exception as e:
        print(f"登录异常：{traceback.format_exc()}")
        return json_response({"code": 500, "success": False, "message": "服务器内部错误"}, 500)
    finally:
        close_db_resource(conn, cur)


@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    if not request.is_json:
        return json_response({"code": 400, "success": False, "message": "请求格式错误"}, 400)

    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()

    if not username or not password:
        return json_response({"code": 400, "success": False, "message": "用户名和密码不能为空"}, 400)

    if len(password) < 6:
        return json_response({"code": 400, "success": False, "message": "密码长度至少6位"}, 400)

    conn = get_db_connection()
    if not conn:
        return json_response({"code": 500, "success": False, "message": "数据库连接失败"}, 500)

    cur = None
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO user (username, password, email) VALUES (%s, %s, %s)",
                    (username, password, email))
        conn.commit()

        user_id = cur.lastrowid
        return json_response({
            "code": 200,
            "success": True,
            "message": "注册成功",
            "user_id": user_id,
            "username": username
        })

    except IntegrityError:
        conn.rollback()
        return json_response({"code": 400, "success": False, "message": "用户名已存在"}, 400)
    except Exception as e:
        conn.rollback()
        print(f"注册异常：{traceback.format_exc()}")
        return json_response({"code": 500, "success": False, "message": "注册失败"}, 500)
    finally:
        close_db_resource(conn, cur)


@app.route('/product_list', methods=['GET'])
def product_list():
    """获取商品列表 - 修复版本"""
    # 获取查询参数
    category_id = request.args.get('category_id', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')

    print(f"收到 /product_list 请求，参数: category_id={category_id}, min_price={min_price}, max_price={max_price}")

    # 先连接数据库获取真实数据
    conn = get_db_connection()
    if not conn:
        # 如果数据库连接失败，返回测试数据（为了前端能显示）
        products = [
            {
                "product_id": 1,
                "product_name": "Python编程从入门到实践",
                "price": 68.50,
                "category_name": "书籍",
                "seller_name": "张三"
            },
            {
                "product_id": 2,
                "product_name": "二手iPhone 12",
                "price": 2999.00,
                "category_name": "电子产品",
                "seller_name": "李四"
            },
            {
                "product_id": 3,
                "product_name": "保温杯",
                "price": 45.00,
                "category_name": "生活用品",
                "seller_name": "王五"
            },
            {
                "product_id": 4,
                "product_name": "Java核心技术",
                "price": 89.00,
                "category_name": "书籍",
                "seller_name": "赵六"
            },
            {
                "product_id": 5,
                "product_name": "小米充电宝",
                "price": 79.00,
                "category_name": "电子产品",
                "seller_name": "钱七"
            }
        ]

        # 简单的过滤逻辑
        filtered_products = products
        if min_price:
            try:
                min_price_float = float(min_price)
                filtered_products = [p for p in filtered_products if p['price'] >= min_price_float]
            except:
                pass
        if max_price:
            try:
                max_price_float = float(max_price)
                filtered_products = [p for p in filtered_products if p['price'] <= max_price_float]
            except:
                pass

        # 返回前端期望的格式
        return {
            "products": filtered_products,
            "count": len(filtered_products)
        }

    # 如果有数据库连接，查询真实数据
    cur = None
    try:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)

        # 构建查询SQL
        sql = """
            SELECT 
                p.product_id,
                p.product_name,
                p.price,
                p.description,
                c.category_name,
                u.username as seller_name
            FROM product p
            JOIN category c ON p.category_id = c.category_id
            JOIN user u ON p.user_id = u.user_id
            WHERE p.status = 1
        """
        params = []

        # 添加筛选条件
        if category_id and category_id.isdigit():
            sql += " AND p.category_id = %s"
            params.append(int(category_id))
        if min_price:
            try:
                sql += " AND p.price >= %s"
                params.append(float(min_price))
            except:
                pass
        if max_price:
            try:
                sql += " AND p.price <= %s"
                params.append(float(max_price))
            except:
                pass

        sql += " ORDER BY p.publish_time DESC"

        cur.execute(sql, params)
        products = cur.fetchall()

        # 返回前端期望的格式
        return {
            "products": products,
            "count": len(products)
        }

    except Exception as e:
        print(f"查询商品列表异常：{traceback.format_exc()}")
        # 出错时返回空数组
        return {
            "products": [],
            "count": 0
        }
    finally:
        close_db_resource(conn, cur)


@app.route('/api/publish_product', methods=['POST'])
def publish_product():
    """发布商品"""
    if not request.is_json:
        return json_response({"code": 400, "success": False, "message": "请求格式错误"}, 400)

    data = request.json
    product_name = data.get('product_name', '').strip()
    price = data.get('price')
    category_id = data.get('category_id')
    user_id = data.get('user_id')
    description = data.get('description', '')

    # 验证数据
    if not product_name:
        return json_response({"code": 400, "success": False, "message": "商品名称不能为空"}, 400)
    if not price or price <= 0:
        return json_response({"code": 400, "success": False, "message": "价格必须大于0"}, 400)
    if not category_id:
        return json_response({"code": 400, "success": False, "message": "请选择商品类别"}, 400)
    if not user_id:
        return json_response({"code": 400, "success": False, "message": "用户信息错误"}, 400)

    conn = get_db_connection()
    if not conn:
        return json_response({"code": 500, "success": False, "message": "数据库连接失败"}, 500)

    cur = None
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO product (product_name, price, description, category_id, user_id, 
                               status, publish_time, view_count) 
            VALUES (%s, %s, %s, %s, %s, 1, NOW(), 0)
        """, (product_name, price, description, category_id, user_id))
        conn.commit()

        product_id = cur.lastrowid
        return json_response({
            "code": 200,
            "success": True,
            "message": "发布成功",
            "product_id": product_id
        })

    except Exception as e:
        conn.rollback()
        print(f"发布商品异常：{traceback.format_exc()}")
        return json_response({"code": 500, "success": False, "message": "发布失败"}, 500)
    finally:
        close_db_resource(conn, cur)


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """获取所有商品类别"""
    conn = get_db_connection()
    if not conn:
        return json_response({
            "categories": [
                {"category_id": 1, "category_name": "书籍"},
                {"category_id": 2, "category_name": "电子产品"},
                {"category_id": 3, "category_name": "生活用品"},
                {"category_id": 4, "category_name": "服饰"},
                {"category_id": 5, "category_name": "其他"}
            ]
        })

    cur = None
    try:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT category_id, category_name, description FROM category ORDER BY category_name")
        categories = cur.fetchall()

        return json_response({
            "code": 200,
            "success": True,
            "categories": categories
        })

    except Exception as e:
        print(f"获取类别异常：{traceback.format_exc()}")
        return json_response({
            "categories": [
                {"category_id": 1, "category_name": "书籍"},
                {"category_id": 2, "category_name": "电子产品"},
                {"category_id": 3, "category_name": "生活用品"},
                {"category_id": 4, "category_name": "服饰"},
                {"category_id": 5, "category_name": "其他"}
            ]
        })
    finally:
        close_db_resource(conn, cur)


@app.route('/api/toggle_favorite', methods=['POST'])
def toggle_favorite():
    """收藏/取消收藏商品"""
    if not request.is_json:
        return json_response({"code": 400, "success": False, "message": "请求格式错误"}, 400)

    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')

    if not user_id or not product_id:
        return json_response({"code": 400, "success": False, "message": "参数不完整"}, 400)

    conn = get_db_connection()
    if not conn:
        return json_response({"code": 500, "success": False, "message": "数据库连接失败"}, 500)

    cur = None
    try:
        cur = conn.cursor()

        # 检查是否已收藏
        cur.execute("SELECT favorite_id FROM favorites WHERE user_id=%s AND product_id=%s",
                    (user_id, product_id))
        existing = cur.fetchone()

        if existing:
            # 取消收藏
            cur.execute("DELETE FROM favorites WHERE user_id=%s AND product_id=%s",
                        (user_id, product_id))
            message = "已取消收藏"
            is_favorite = False
        else:
            # 添加收藏
            cur.execute("INSERT INTO favorites (user_id, product_id) VALUES (%s, %s)",
                        (user_id, product_id))
            message = "收藏成功"
            is_favorite = True

        conn.commit()
        return json_response({
            "code": 200,
            "success": True,
            "message": message,
            "is_favorite": is_favorite
        })

    except Exception as e:
        conn.rollback()
        print(f"收藏操作异常：{traceback.format_exc()}")
        return json_response({"code": 500, "success": False, "message": "操作失败"}, 500)
    finally:
        close_db_resource(conn, cur)


@app.route('/api/user_favorites/<int:user_id>', methods=['GET'])
def user_favorites(user_id):
    """获取用户收藏列表"""
    conn = get_db_connection()
    if not conn:
        return json_response({"code": 500, "success": False, "message": "数据库连接失败"}, 500)

    cur = None
    try:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT 
                p.product_id,
                p.product_name,
                p.price,
                p.description,
                c.category_name,
                f.created_at
            FROM favorites f
            JOIN product p ON f.product_id = p.product_id
            JOIN category c ON p.category_id = c.category_id
            WHERE f.user_id = %s AND p.status = 1
            ORDER BY f.created_at DESC
        """, (user_id,))

        favorites = cur.fetchall()
        return json_response({
            "code": 200,
            "success": True,
            "favorites": favorites,
            "count": len(favorites)
        })

    except Exception as e:
        print(f"获取收藏列表异常：{traceback.format_exc()}")
        return json_response({"code": 500, "success": False, "message": "查询失败"}, 500)
    finally:
        close_db_resource(conn, cur)


@app.route('/api/create_order', methods=['POST'])
def create_order():
    """创建订单"""
    if not request.is_json:
        return json_response({"code": 400, "success": False, "message": "请求格式错误"}, 400)

    data = request.json
    product_id = data.get('product_id')
    buyer_id = data.get('buyer_id')

    if not product_id or not buyer_id:
        return json_response({"code": 400, "success": False, "message": "参数不完整"}, 400)

    conn = get_db_connection()
    if not conn:
        return json_response({"code": 500, "success": False, "message": "数据库连接失败"}, 500)

    cur = None
    try:
        cur = conn.cursor()

        # 检查商品是否存在
        cur.execute("SELECT user_id, price, product_name FROM product WHERE product_id=%s AND status=1",
                    (product_id,))
        product = cur.fetchone()

        if not product:
            return json_response({"code": 404, "success": False, "message": "商品不存在或已售出"}, 404)

        seller_id, price, product_name = product

        # 不能购买自己的商品
        if seller_id == buyer_id:
            return json_response({"code": 400, "success": False, "message": "不能购买自己的商品"}, 400)

        # 检查是否已有未完成的订单
        cur.execute("SELECT order_id FROM orders WHERE product_id=%s AND status IN (1,2,3)",
                    (product_id,))
        existing_order = cur.fetchone()
        if existing_order:
            return json_response({"code": 400, "success": False, "message": "该商品已有未完成的订单"}, 400)

        # 创建订单
        cur.execute("""
            INSERT INTO orders (product_id, buyer_id, seller_id, price, order_time, status) 
            VALUES (%s, %s, %s, %s, NOW(), 1)
        """, (product_id, buyer_id, seller_id, price))

        # 更新商品状态为已售出
        cur.execute("UPDATE product SET status=0 WHERE product_id=%s", (product_id,))

        conn.commit()
        return json_response({
            "code": 200,
            "success": True,
            "message": "下单成功",
            "order_id": cur.lastrowid,
            "product_name": product_name,
            "price": price
        })

    except Exception as e:
        conn.rollback()
        print(f"创建订单异常：{traceback.format_exc()}")
        return json_response({"code": 500, "success": False, "message": f"下单失败: {str(e)}"}, 500)
    finally:
        close_db_resource(conn, cur)


@app.route('/api/hot_categories', methods=['GET'])
def hot_categories():
    """热门商品类别统计"""
    conn = get_db_connection()
    if not conn:
        return json_response({
            "categories": ["书籍", "电子产品", "生活用品", "服饰", "其他"],
            "counts": [15, 10, 8, 5, 3]
        })

    cur = None
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.category_name, COUNT(p.product_id) as count
            FROM category c
            LEFT JOIN product p ON c.category_id = p.category_id AND p.status = 1
            GROUP BY c.category_id, c.category_name
            ORDER BY count DESC
        """)
        rows = cur.fetchall()

        categories = []
        counts = []
        for row in rows:
            categories.append(row[0] or "其他")
            counts.append(row[1] or 0)

        return json_response({
            "categories": categories,
            "counts": counts
        })
    except Exception as e:
        print(f"热门类别查询异常：{traceback.format_exc()}")
        return json_response({
            "categories": ["书籍", "电子产品", "生活用品"],
            "counts": [15, 10, 8]
        })
    finally:
        close_db_resource(conn, cur)


@app.route('/api/price_distribution', methods=['GET'])
def price_distribution():
    """价格分布统计"""
    conn = get_db_connection()
    if not conn:
        return json_response({
            "price_ranges": ["0-50元", "51-100元", "101-200元", "201-500元", "501元以上"],
            "counts": [20, 15, 10, 5, 2]
        })

    cur = None
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                CASE 
                    WHEN price <= 50 THEN '0-50元'
                    WHEN price <= 100 THEN '51-100元'
                    WHEN price <= 200 THEN '101-200元'
                    WHEN price <= 500 THEN '201-500元'
                    ELSE '501元以上'
                END as price_range,
                COUNT(*) as count
            FROM product
            WHERE status = 1
            GROUP BY price_range
            ORDER BY 
                CASE price_range
                    WHEN '0-50元' THEN 1
                    WHEN '51-100元' THEN 2
                    WHEN '101-200元' THEN 3
                    WHEN '201-500元' THEN 4
                    ELSE 5
                END
        """)
        rows = cur.fetchall()

        price_ranges = []
        counts = []
        for row in rows:
            price_ranges.append(row[0])
            counts.append(row[1])

        return json_response({
            "price_ranges": price_ranges,
            "counts": counts
        })
    except Exception as e:
        print(f"价格分布查询异常：{traceback.format_exc()}")
        return json_response({
            "price_ranges": ["0-50元", "51-100元", "101元以上"],
            "counts": [20, 15, 5]
        })
    finally:
        close_db_resource(conn, cur)


@app.route('/api/debug/tables', methods=['GET'])
def debug_tables():
    """数据库诊断接口"""
    conn = get_db_connection()
    if not conn:
        return json_response({"code": 500, "success": False, "message": "数据库连接失败"}, 500)

    cur = None
    try:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)

        # 检查所有表
        cur.execute("SHOW TABLES")
        tables = cur.fetchall()

        result = {}
        for table in tables:
            table_name = table[f'Tables_in_{DB_CONFIG["db"]}']
            cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cur.fetchone()['count']
            result[table_name] = count

            # 如果是product表，检查status分布
            if table_name == 'product':
                cur.execute("SELECT status, COUNT(*) as count FROM product GROUP BY status")
                status_dist = cur.fetchall()
                result['product_status'] = status_dist

        return json_response({
            "code": 200,
            "success": True,
            "message": "数据库诊断完成",
            "data": result
        })

    except Exception as e:
        print(f"诊断异常：{traceback.format_exc()}")
        return json_response({"code": 500, "success": False, "message": f"诊断失败: {str(e)}"}, 500)
    finally:
        close_db_resource(conn, cur)


@app.route('/api/user_products/<int:user_id>', methods=['GET'])
def user_products(user_id):
    """获取用户发布的商品"""
    conn = get_db_connection()
    if not conn:
        return json_response({"code": 500, "success": False, "message": "数据库连接失败"}, 500)

    cur = None
    try:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT 
                p.*,
                c.category_name,
                COUNT(DISTINCT f.favorite_id) as favorite_count
            FROM product p
            JOIN category c ON p.category_id = c.category_id
            LEFT JOIN favorites f ON p.product_id = f.product_id
            WHERE p.user_id = %s
            GROUP BY p.product_id
            ORDER BY p.publish_time DESC
        """, (user_id,))

        products = cur.fetchall()
        return json_response({
            "code": 200,
            "success": True,
            "products": products,
            "count": len(products)
        })

    except Exception as e:
        print(f"获取用户商品异常：{traceback.format_exc()}")
        return json_response({"code": 500, "success": False, "message": "查询失败"}, 500)
    finally:
        close_db_resource(conn, cur)


@app.route('/api/check_favorite/<int:user_id>/<int:product_id>', methods=['GET'])
def check_favorite(user_id, product_id):
    """检查是否已收藏"""
    conn = get_db_connection()
    if not conn:
        return json_response({"code": 500, "success": False, "message": "数据库连接失败"}, 500)

    cur = None
    try:
        cur = conn.cursor()
        cur.execute("SELECT favorite_id FROM favorites WHERE user_id=%s AND product_id=%s",
                    (user_id, product_id))
        existing = cur.fetchone()

        return json_response({
            "code": 200,
            "success": True,
            "is_favorite": existing is not None
        })

    except Exception as e:
        print(f"检查收藏异常：{traceback.format_exc()}")
        return json_response({"code": 500, "success": False, "message": "查询失败"}, 500)
    finally:
        close_db_resource(conn, cur)


# ==================== 启动服务器 ====================
if __name__ == '__main__':
    print("=" * 60)
    print("校园二手交易平台服务器启动中...")
    print("=" * 60)
    print("访问地址: http://localhost:5000")
    print("健康检查: http://localhost:5000/api/health")
    print("数据库诊断: http://localhost:5000/api/debug/tables")
    print("商品列表: http://localhost:5000/product_list")
    print("测试账号: test/123456, admin/admin123, 张三/123456, 李四/123456")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)