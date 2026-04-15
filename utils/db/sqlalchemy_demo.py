"""
SQLAlchemy Core 示例（原生 SQL 版本）
pip install sqlalchemy pymysql psycopg2-binary

# MYSQL
CREATE TABLE user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    age INT,
    create_time DATETIME
);

#PG
CREATE TABLE user (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    age INT,
    create_time TIMESTAMP
);
"""

from sqlalchemy import create_engine, text
from datetime import datetime

# ================== 🔧 配置区 ==================

DB_TYPE = "mysql"  # 可选: mysql / pg

MYSQL_URL = "mysql+pymysql://root:123456@localhost:3306/test_db?charset=utf8mb4"

PG_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/test_db"

# 自动选择
DB_URL = MYSQL_URL if DB_TYPE == "mysql" else PG_URL

# 创建引擎（类似数据源）
engine = create_engine(
    DB_URL,
    echo=False,           # 是否打印 SQL
    pool_size=5,          # 连接池大小
    max_overflow=10       # 最大溢出连接
)

# ==============================================


# ================== 批量插入 ==================
def batch_insert(data):
    sql = text("""
        INSERT INTO user(name, age, create_time)
        VALUES (:name, :age, :create_time)
    """)

    # 自动事务（推荐写法）
    with engine.begin() as conn:
        conn.execute(sql, data)

    print("✅ batch insert success")


def batch_insert2(data):
    values = []
    params = {}
    for i, row in enumerate(data):
        values.append(f"(:name{i}, :age{i}, :time{i})")
        params[f"name{i}"] = row["name"]
        params[f"age{i}"] = row["age"]
        params[f"time{i}"] = row["create_time"]

    sql = text(f"""
        INSERT INTO user(name, age, create_time)
        VALUES {", ".join(values)}
    """)

    with engine.begin() as conn:
        conn.execute(sql, params)


# ================== 查询 ==================
def query_data():
    sql = text("SELECT id, name, age, create_time FROM user")

    with engine.connect() as conn:
        result = conn.execute(sql)

        print("📌 Query result:")

        for row in result:
            # row 是 Row 对象（类似 Map）
            print(
                row.id,
                row.name,
                row.age,
                row.create_time,   # 👉 已经是 datetime.datetime
            )


# ================== 主函数 ==================
if __name__ == "__main__":
    sample_data = [
        {"name": "Alice", "age": 20, "create_time": datetime.now()},
        {"name": "Bob", "age": 25, "create_time": datetime.now()},
        {"name": "Charlie", "age": 30, "create_time": datetime.now()},
    ]

    batch_insert(sample_data)
    query_data()
