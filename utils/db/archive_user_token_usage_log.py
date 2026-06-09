"""
user_token_usage_log 归档脚本
pip install sqlalchemy pymysql
"""

from sqlalchemy import create_engine, text

# ================== 配置区 ==================

DB_URL = "mysql+pymysql://root:123456@localhost:3306/test_db?charset=utf8mb4"

# 原表名
SOURCE_TABLE = "user_token_usage_log"

# 归档表名（按月份命名，如 user_token_usage_log_2604 表示 2026年4月）
ARCHIVE_TABLE = "user_token_usage_log_2604"

# 归档截止时间：event_time < 该日期的数据将被归档
CUTOFF_DATE = "2026-05-01"

# 每批次处理的行数
BATCH_SIZE = 10000

# ================== 引擎 ==================

engine = create_engine(DB_URL, echo=False, pool_size=5, max_overflow=10)


def create_archive_table():
    """创建归档表（如果不存在）"""
    sql = text(f"CREATE TABLE IF NOT EXISTS {ARCHIVE_TABLE} LIKE {SOURCE_TABLE}")
    with engine.begin() as conn:
        conn.execute(sql)
    print(f"✅ 归档表 {ARCHIVE_TABLE} 已就绪")


def get_archive_range():
    """查询待归档数据的 id 范围和数量"""
    sql = text(f"""
        SELECT MIN(id) AS min_id, MAX(id) AS max_id, COUNT(*) AS total
        FROM {SOURCE_TABLE}
        WHERE event_time < :cutoff
    """)
    with engine.connect() as conn:
        result = conn.execute(sql, {"cutoff": CUTOFF_DATE}).fetchone()

    min_id, max_id, total = result.min_id, result.max_id, result.total
    print(f"📌 待归档数据: id 范围 [{min_id}, {max_id}], 共 {total} 条")
    return min_id, max_id, total


def batch_archive(min_id: int, max_id: int):
    """按 id 范围批次归档数据"""
    batch_start = min_id
    total_archived = 0
    total_deleted = 0
    batch_num = 0

    while batch_start <= max_id:
        batch_end = batch_start + BATCH_SIZE - 1
        # 防止超过最大 id
        batch_end = min(batch_end, max_id)

        batch_num += 1

        with engine.begin() as conn:
            # 1. 插入归档表
            insert_sql = text(f"""
                INSERT INTO {ARCHIVE_TABLE}
                SELECT * FROM {SOURCE_TABLE}
                WHERE id BETWEEN :start AND :end
                  AND event_time < :cutoff
            """)
            result = conn.execute(insert_sql, {
                "start": batch_start,
                "end": batch_end,
                "cutoff": CUTOFF_DATE,
            })
            inserted = result.rowcount

            # 2. 只有插入了数据才删除原表
            if inserted > 0:
                delete_sql = text(f"""
                    DELETE FROM {SOURCE_TABLE}
                    WHERE id BETWEEN :start AND :end
                      AND event_time < :cutoff
                """)
                conn.execute(delete_sql, {
                    "start": batch_start,
                    "end": batch_end,
                    "cutoff": CUTOFF_DATE,
                })
                total_deleted += inserted

            total_archived += inserted

        if batch_num % 10 == 0 or batch_end == max_id:
            print(f"  批次 {batch_num}: id [{batch_start}, {batch_end}], 本批插入 {inserted} 条, 累计归档 {total_archived} 条")

        batch_start = batch_end + 1

    print(f"✅ 归档完成: 共归档 {total_archived} 条, 删除原表 {total_deleted} 条")


def main():
    print(f"===== 归档任务开始 =====")
    print(f"原表: {SOURCE_TABLE}")
    print(f"归档表: {ARCHIVE_TABLE}")
    print(f"截止时间: event_time < '{CUTOFF_DATE}'")
    print(f"批次大小: {BATCH_SIZE}")
    print()

    # 1. 创建归档表
    create_archive_table()

    # 2. 查询归档范围
    min_id, max_id, total = get_archive_range()
    if min_id is None or total == 0:
        print("⚠️  没有需要归档的数据，退出")
        return

    # 3. 批次归档
    batch_archive(min_id, max_id)

    print(f"\n===== 归档任务结束 =====")


if __name__ == "__main__":
    main()
