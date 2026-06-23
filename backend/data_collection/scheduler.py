"""
数据采集定时任务支持

使用方式:
1. 系统crontab / windows计划任务调用:
   python -m data_collection.scheduler --mode monthly

2. 使用TRAE Schedule工具创建自动化任务:
   - cron: 0 10 15 * *  (每月15日上午10点)
   - message: python -m data_collection.scheduler --mode monthly
"""
import argparse
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_collection.runner import run_monthly_update, run_full_initialization


def main():
    parser = argparse.ArgumentParser(description="屋檐 - 数据采集定时任务")
    parser.add_argument(
        "--mode",
        choices=["monthly", "full"],
        default="monthly",
        help="任务模式: monthly=月度增量, full=全量初始化"
    )
    parser.add_argument("--year", type=int, help="指定年份(月度模式)")
    parser.add_argument("--month", type=int, help="指定月份(月度模式)")
    parser.add_argument("--start-year", type=int, default=2020, help="全量起始年份")
    parser.add_argument("--end-year", type=int, default=2025, help="全量结束年份")

    args = parser.parse_args()

    print(f"[Scheduler] 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[Scheduler] 任务模式: {args.mode}")

    if args.mode == "monthly":
        run_monthly_update(args.year, args.month)
    elif args.mode == "full":
        run_full_initialization(args.start_year, args.end_year)

    print(f"[Scheduler] 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
