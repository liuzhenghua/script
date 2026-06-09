"""
user_token_usage_log 批次清理脚本
pip install sqlalchemy pymysql
"""

from sqlalchemy import create_engine, text
from datetime import datetime

# ================== 配置区 ==================

DB_URL = "mysql+pymysql://root:123456@localhost:3306/test_db?charset=utf8mb4"

# 表名
TABLE = "user_token_usage_log"

# 清理截止时间：event_time < 该日期的数据将被删除
CUTOFF_DATE = "2026-06-01"

# 每批次删除的行数
BATCH_SIZE = 5000

# ================== 引擎 ==================

engine = create_engine(DB_URL, echo=False, pool_size=5, max_overflow=10)


def get_purge_range():
    """查询待清理数据的 id 范围和数量"""
    sql = text(f"""
        SELECT MIN(id) AS min_id, MAX(id) AS max_id, COUNT(*) AS total
        FROM {TABLE}
        WHERE event_time < :cutoff
    """)
    with engine.connect() as conn:
        result = conn.execute(sql, {"cutoff": CUTOFF_DATE}).fetchone()

    min_id, max_id, total = result.min_id, result.max_id, result.total
    print(f"📌 待清理数据: id 范围 [{min_id}, {max_id}], 共 {total} 条")
    return min_id, max_id, total


def batch_purge(min_id: int, max_id: int):
    """按 id 范围批次删除数据"""
    batch_start = min_id
    total_deleted = 0
    batch_num = 0

    while batch_start <= max_id:
        batch_end = batch_start + BATCH_SIZE - 1
        batch_end = min(batch_end, max_id)

        batch_num += 1

        with engine.begin() as conn:
            delete_sql = text(f"""
                DELETE FROM {TABLE}
                WHERE id BETWEEN :start AND :end
                  AND event_time < :cutoff
            """)
            result = conn.execute(delete_sql, {
                "start": batch_start,
                "end": batch_end,
                "cutoff": CUTOFF_DATE,
            })
            deleted = result.rowcount
            total_deleted += deleted

        if batch_num % 10 == 0 or batch_end == max_id:
            print(f"  批次 {batch_num}: id [{batch_start}, {batch_end}], 本批删除 {deleted} 条, 累计删除 {total_deleted} 条")

        batch_start = batch_end + 1

    print(f"✅ 清理完成: 共删除 {total_deleted} 条")


def main():
    print(f"===== 清理任务开始 =====")
    print(f"表: {TABLE}")
    print(f"截止时间: event_time < '{CUTOFF_DATE}'")
    print(f"批次大小: {BATCH_SIZE}")
    print()

    # 1. 查询清理范围
    min_id, max_id, total = get_purge_range()
    if min_id is None or total == 0:
        print("⚠️  没有需要清理的数据，退出")
        return

    # 2. 确认
    confirm = input(f"⚠️  即将删除 {total} 条数据，是否继续？(y/N): ")
    if confirm.lower() != "y":
        print("已取消")
        return

    # 3. 批次清理
    batch_purge(min_id, max_id)

    print(f"\n===== 清理任务结束 =====")


if __name__ == "__main__":
    main()
