"""
数据采集运行器

支持两种模式:
1. 全量初始化: 70个城市依次采集历史数据
2. 增量更新: 按月更新最新数据(用于定时任务)
"""
import sys
import os
import time
import random
import json
from datetime import datetime
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.models import init_db, get_session, DimCity
from data_collection.config import DEFAULT_START_YEAR, DEFAULT_END_YEAR, SLEEP_BETWEEN_CITIES
from data_collection.client import fetch_city_list, fetch_city_price_years, fetch_city_price
from data_collection.loader import (
    load_ods_city_list, load_dim_city,
    load_ods_price, load_dwd_price, load_dim_indicator_and_period
)
from data_collection.aggregator import aggregate_city_monthly, aggregate_city_trend, generate_report


def _sleep_between_cities():
    """城市之间的随机长间隔，避免触发风控"""
    seconds = random.uniform(*SLEEP_BETWEEN_CITIES)
    minutes = seconds / 60
    print(f"  [风控等待] 等待 {minutes:.1f} 分钟后采集下一个城市...")
    time.sleep(seconds)


def init_city_list(session):
    """初始化城市列表"""
    print("\n[Step 1] 采集并保存城市列表...")

    # 检查是否已有城市列表
    existing = session.query(DimCity).first()
    if existing:
        print(f"  -> DIM中已有 {session.query(DimCity).count()} 个城市，跳过接口1")
        return

    result = fetch_city_list()
    load_ods_city_list(session, result)

    cities = result["data"].get("data", [])
    load_dim_city(session, cities)

    print(f"  -> 获取到 {len(cities)} 个城市，已写入ODS和DIM")


def collect_city_historical(
    session,
    city_code: str,
    city_name: str,
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR
):
    """
    采集单个城市的历史数据并加载到数仓
    """
    print(f"\n[城市采集] {city_name}({city_code}) {start_year}-{end_year}")

    all_records = fetch_city_price_years(
        city_code=city_code,
        city_name=city_name,
        start_year=start_year,
        end_year=end_year,
        progress_callback=lambda year, result: load_ods_price(session, result)
    )

    if all_records:
        dwd_result = load_dwd_price(session, all_records)
        load_dim_indicator_and_period(session, all_records)
        aggregate_city_monthly(session, city_code, city_name)
        aggregate_city_trend(session, city_code, city_name)
        report_id = generate_report(session, city_code, city_name)
        print(f"  -> DWD: 新增 {dwd_result['new']} 条, 更新 {dwd_result['update']} 条")
        print(f"  -> ADS报告: {report_id}")
    else:
        print(f"  -> 警告: 未获取到 {city_name} 的数据")


def run_full_initialization(
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR,
    skip_nanjing: bool = True,
):
    """
    全量初始化模式: 依次采集70个城市历史数据

    Args:
        start_year: 起始年份
        end_year: 结束年份
        skip_nanjing: 是否跳过南京市(假设已初始化)
    """
    print("=" * 70)
    print("  屋檐 - 70城住宅销售价格数据全量初始化")
    print("=" * 70)
    print(f"  采集时间范围: {start_year}年 - {end_year}年")
    print(f"  城市间隔: {SLEEP_BETWEEN_CITIES[0]//60}-{SLEEP_BETWEEN_CITIES[1]//60}分钟")
    print(f"  API调用间隔: 1-5秒")
    print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    init_db()
    session = get_session()

    try:
        init_city_list(session)

        cities = session.query(DimCity).order_by(DimCity.city_code).all()
        total = len(cities)

        for idx, city in enumerate(cities, 1):
            print(f"\n  [{idx}/{total}] 开始处理城市: {city.city_name}")

            if skip_nanjing and city.city_name == "南京":
                print("  -> 跳过南京市(已初始化)")
                continue

            collect_city_historical(
                session,
                city.city_code,
                city.city_name,
                start_year,
                end_year
            )

            # 除了最后一个城市，其他都等待
            if idx < total:
                _sleep_between_cities()

        _print_summary(session)

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def run_monthly_update(
    year: Optional[int] = None,
    month: Optional[int] = None,
):
    """
    增量更新模式: 每月定时任务更新所有城市最新月份数据

    Args:
        year: 年份，默认当前年
        month: 月份，默认上个月
    """
    now = datetime.now()
    if year is None or month is None:
        if now.month == 1:
            year = now.year - 1
            month = 12
        else:
            year = now.year
            month = now.month - 1

    period = f"{year:04d}{month:02d}"

    print("=" * 70)
    print("  屋檐 - 月度房价数据增量更新")
    print("=" * 70)
    print(f"  更新期间: {year}年{month}月 ({period})")
    print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    init_db()
    session = get_session()

    try:
        cities = session.query(DimCity).order_by(DimCity.city_code).all()
        total = len(cities)

        for idx, city in enumerate(cities, 1):
            print(f"\n  [{idx}/{total}] 更新城市: {city.city_name}")

            # 查询该期间数据
            result = fetch_city_price(
                city_code=city.city_code,
                city_name=city.city_name,
                start_period=period,
                end_period=period
            )

            load_ods_price(session, result)

            if result["records"]:
                load_dwd_price(session, result["records"])
                load_dim_indicator_and_period(session, result["records"])
                aggregate_city_monthly(session, city.city_code, city.city_name)
                aggregate_city_trend(session, city.city_code, city.city_name)
                print(f"  -> 更新 {len(result['records'])} 条记录")
            else:
                print(f"  -> 该月无数据")

            if idx < total:
                _sleep_between_cities()

        _print_summary(session)

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def _print_summary(session):
    """打印数据统计"""
    from db.models import (
        OdsCityListRaw, OdsHousingPriceRaw, DwdHousingPriceDi,
        DwsCityPriceMonthly, DwsCityPriceTrend, AdsCityPriceReport,
        DimCity, DimIndicator, DimPeriod
    )

    print("\n" + "=" * 70)
    print("  数据统计摘要")
    print("=" * 70)
    print(f"  ODS 城市列表原始记录: {session.query(OdsCityListRaw).count()}")
    print(f"  ODS 价格原始记录:     {session.query(OdsHousingPriceRaw).count()}")
    print(f"  DWD 明细记录:         {session.query(DwdHousingPriceDi).count()}")
    print(f"  DIM 城市维度:         {session.query(DimCity).count()}")
    print(f"  DIM 指标维度:         {session.query(DimIndicator).count()}")
    print(f"  DIM 时间维度:         {session.query(DimPeriod).count()}")
    print(f"  DWS 月度汇总:         {session.query(DwsCityPriceMonthly).count()}")
    print(f"  DWS 趋势汇总:         {session.query(DwsCityPriceTrend).count()}")
    print(f"  ADS 分析报告:         {session.query(AdsCityPriceReport).count()}")
    print("=" * 70)


def collect_single_city(
    city_name: str,
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR
):
    """
    采集单个城市(用于测试或补充)
    """
    print("=" * 70)
    print(f"  采集单个城市: {city_name}")
    print("=" * 70)

    init_db()
    session = get_session()

    try:
        init_city_list(session)

        city = session.query(DimCity).filter(DimCity.city_name == city_name).first()
        if not city:
            print(f"  -> 错误: 城市 {city_name} 不存在")
            return

        collect_city_historical(
            session,
            city.city_code,
            city.city_name,
            start_year,
            end_year
        )

        _print_summary(session)

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="屋檐 - 国家统计局70城房价数据采集")
    parser.add_argument(
        "mode",
        choices=["full", "monthly", "single"],
        help="运行模式: full=全量初始化, monthly=月度增量更新, single=单个城市"
    )
    parser.add_argument("--city", help="single模式下的城市名称")
    parser.add_argument("--start-year", type=int, default=DEFAULT_START_YEAR, help="起始年份")
    parser.add_argument("--end-year", type=int, default=DEFAULT_END_YEAR, help="结束年份")
    parser.add_argument("--year", type=int, help="月度更新模式-年份")
    parser.add_argument("--month", type=int, help="月度更新模式-月份")

    args = parser.parse_args()

    if args.mode == "full":
        run_full_initialization(args.start_year, args.end_year)
    elif args.mode == "monthly":
        run_monthly_update(args.year, args.month)
    elif args.mode == "single":
        if not args.city:
            print("错误: single模式需要 --city 参数")
            sys.exit(1)
        collect_single_city(args.city, args.start_year, args.end_year)
