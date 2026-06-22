import requests
import json
import time
import random
import os
import sys
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db.models import (
    init_db, get_session,
    OdsCityListRaw, OdsHousingPriceRaw,
    DwdHousingPriceDi,
    DimCity, DimIndicator, DimPeriod,
    DwsCityPriceMonthly, DwsCityPriceTrend,
    AdsCityPriceReport, AdsCityPriceRank
)

# 常量
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}
BASE_URL = "https://data.stats.gov.cn/dg/website/publicrelease/web/external"

PROVINCE_MAP = {
    "11": "北京", "12": "天津", "13": "河北", "14": "山西", "15": "内蒙古",
    "21": "辽宁", "22": "吉林", "23": "黑龙江",
    "31": "上海", "32": "江苏", "33": "浙江", "34": "安徽", "35": "福建", "36": "江西", "37": "山东",
    "41": "河南", "42": "湖北", "43": "湖南",
    "44": "广东", "45": "广西", "46": "海南",
    "50": "重庆", "51": "四川", "52": "贵州", "53": "云南", "54": "西藏",
    "61": "陕西", "62": "甘肃", "63": "青海", "64": "宁夏", "65": "新疆",
}
REGION_MAP = {
    "北京": "华北", "天津": "华北", "河北": "华北", "山西": "华北", "内蒙古": "华北",
    "辽宁": "东北", "吉林": "东北", "黑龙江": "东北",
    "上海": "华东", "江苏": "华东", "浙江": "华东", "安徽": "华东", "福建": "华东", "江西": "华东", "山东": "华东",
    "河南": "华中", "湖北": "华中", "湖南": "华中",
    "广东": "华南", "广西": "华南", "海南": "华南",
    "重庆": "西南", "四川": "西南", "贵州": "西南", "云南": "西南", "西藏": "西南",
    "陕西": "西北", "甘肃": "西北", "青海": "西北", "宁夏": "西北", "新疆": "西北",
}
TIER_MAP = {
    "北京": "一线", "上海": "一线", "广州": "一线", "深圳": "一线",
    "成都": "新一线", "杭州": "新一线", "重庆": "新一线", "武汉": "新一线",
    "西安": "新一线", "苏州": "新一线", "南京": "新一线", "天津": "新一线",
    "郑州": "新一线", "长沙": "新一线", "东莞": "新一线", "青岛": "新一线",
}


def safe_sleep():
    time.sleep(random.uniform(2, 5))


def step1_collect_city_list(session) -> List[Dict]:
    """Step 1: 采集城市列表 -> ODS"""
    print("\n[Step 1] 采集城市列表...")

    url = f"{BASE_URL}/getDasByDaCatalogId?daCid=44016f1bffeb4ea49fe34e100c6415fb"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    data = resp.json()

    if data.get("data") and len(data["data"]) > 0:
        existing = session.query(OdsCityListRaw).first()
        if not existing:
            raw = OdsCityListRaw(
                raw_json=json.dumps(data, ensure_ascii=False),
                api_url=url,
                response_code=resp.status_code,
            )
            session.add(raw)
            session.commit()

        city_list = data["data"]
        print(f"  -> 获取到 {len(city_list)} 个城市")

        for city in city_list:
            dim = session.query(DimCity).filter(
                DimCity.city_code == city["name_value"]
            ).first()
            if not dim:
                prov_code = city["name_value"][:2]
                dim = DimCity(
                    city_code=city["name_value"],
                    city_name=city["show_name"],
                    city_full_name=city["name_text"],
                    province_code=prov_code,
                    province_name=PROVINCE_MAP.get(prov_code, ""),
                    region=REGION_MAP.get(PROVINCE_MAP.get(prov_code, ""), ""),
                    tier=TIER_MAP.get(city["show_name"], "三线"),
                )
                session.add(dim)
        session.commit()
        print(f"  -> DIM城市维度更新完成")
        return city_list

    return []


def step2_collect_price_data(session, city_code: str, city_name: str,
                              period_start: str, period_end: str) -> List[Dict]:
    """Step 2: 采集价格数据 -> ODS"""
    print(f"\n[Step 2] 采集 {city_name}({city_code}) 价格数据 {period_start}-{period_end}...")

    url = f"{BASE_URL}/stream/esData"
    body = {
        "cid": "3eb43764c74741469b745c396cf002d1",
        "indicatorIds": [
            "9445413888804ca8aa533b7ef859103b", "accb0def73524078a2f9517e6e39c628",
            "b536b34ad00c46c0832e0fb5e09ba686", "732f9cca00c84facb9bb8dd8365bc0e7",
            "fb43046325f64e3896a96b70b071d52b", "b61c4ef46f5a4d03a02b06d90fcf0980",
            "2e903b90641f453196dada70699f4e69", "05dd255eb4d54986a567d523b4403676",
            "11ad09962ea7497eb2ccdf2be5719a20", "97d66103d9524635b6aea7f136ac70c3",
            "3a6d0fb67cb74c148d371993672d26cd", "25205b9fb3054cc89ff1d1e0fc4bc110",
            "2624e01a782d4f47a23610bd056570ae", "6bf41d9c10ef495bb6369e82e824c218",
            "ab1186501035483fae81dc2d8c882e17", "73a8b0fe738a482491ed17e9b28e0d85",
            "cbcf12312fec43768ead1af77fd26ed0", "9314a623544b4d20ad27be3f962deebf",
            "d4850e3f460b4f1c84d71cf0a8900a0f", "93815f78b2d54fc98a34b9669be5467f",
            "757f2c9afc39420d89c47c30890d9de5", "18c087a18dc145e7b0501d1fc05959cb",
            "9f75757cb7d9438fbd11cccf89613028", "98fb96672e1c4666adb821e393499b46",
            "e9a41436e75841bc95eaadb21ab1f02e", "d5f4c9e221eb49bea23b5d1ca125f1f8",
            "20a5ed14619847f6b8638f942cdca4e6", "45871773323240bb91dddbfa5e2a1b55",
            "0a73708bfa9e45798883a9b186b7f703", "bf5eb59fa096441ea78f71073e0a288e",
            "af76711644c24b468fa8cb382b73da22", "3b970e6f7834459b909a2a9203242c2e",
            "dae265212c9f4e48bbbd9038362f628e", "a82be5ebd70945eeadbd0eec4ee4225c",
            "61aace5a8919489db2c22ab9e55050b9"
        ],
        "daCatalogId": "",
        "das": [{"text": city_name, "value": city_code}],
        "showType": "1",
        "dts": [f"{period_start}MM-{period_end}MM"],
        "rootId": "327ecbb2e6b14c669da1e99e39faa24c"
    }

    safe_sleep()
    resp = requests.post(url, headers=HEADERS, json=body, timeout=30)
    data = resp.json()

    raw = OdsHousingPriceRaw(
        raw_json=json.dumps(data, ensure_ascii=False),
        request_params=json.dumps({"city_name": city_name, "city_code": city_code, "period": f"{period_start}-{period_end}"}, ensure_ascii=False),
        api_url=url,
        response_code=resp.status_code,
        city_code=city_code,
        period_range=f"{period_start}-{period_end}",
    )
    session.add(raw)
    session.commit()

    records = []
    if data.get("data"):
        for period_item in data["data"]:
            period_code = period_item["code"]
            period_name = period_item["name"]
            for item in period_item.get("values", []):
                records.append({
                    **item,
                    "period_code": period_code,
                    "period_name": period_name,
                })

    print(f"  -> 获取到 {len(records)} 条数据记录")
    return records


def step3_load_dwd(session, records: List[Dict]):
    """Step 3: ODS -> DWD 明细数据"""
    print("\n[Step 3] 加载 DWD 明细数据层...")

    count_new = 0
    count_skip = 0
    for item in records:
        city_code = item.get("da", "")
        indicator_id = item.get("_id", "")
        period_code = item.get("period_code", "")

        existing = session.query(DwdHousingPriceDi).filter(
            DwdHousingPriceDi.city_code == city_code,
            DwdHousingPriceDi.indicator_id == indicator_id,
            DwdHousingPriceDi.period_code == period_code,
        ).first()

        if existing:
            existing.value = float(item["value"]) if item.get("value") and item["value"] != "" else None
            existing.etl_time = datetime.now()
            count_skip += 1
        else:
            value = float(item["value"]) if item.get("value") and item["value"] != "" else None
            dwd = DwdHousingPriceDi(
                city_code=city_code,
                city_name=item.get("da_name", ""),
                indicator_id=indicator_id,
                indicator_name=item.get("_name", ""),
                indicator_base=item.get("i_showname", "").strip(),
                period_code=period_code,
                period_name=item.get("period_name", ""),
                value=value,
                unit=item.get("du_name", ""),
                data_type=item.get("type", ""),
                catalog_id=item.get("catalogid", ""),
            )
            session.add(dwd)
            count_new += 1

    session.commit()
    print(f"  -> 新增 {count_new} 条, 更新 {count_skip} 条")


def step4_load_dim(session, records: List[Dict]):
    """Step 4: 加载 DIM 维度层"""
    print("\n[Step 4] 加载 DIM 维度层...")

    indicator_set = {}
    period_set = {}

    for item in records:
        iid = item.get("_id", "")
        if iid and iid not in indicator_set:
            indicator_set[iid] = {
                "indicator_id": iid,
                "indicator_name": item.get("_name", ""),
                "indicator_category": _parse_category(item.get("_name", "")),
                "indicator_type": "价格指数",
                "base_period": item.get("i_showname", "").strip().rstrip(") ").split("(")[-1] if "(" in item.get("i_showname", "") else "",
                "unit": item.get("du_name", ""),
                "catalog_id": item.get("catalogid", ""),
                "sort_order": item.get("ds_order", 0),
            }

        pc = item.get("period_code", "")
        if pc and pc not in period_set:
            yr = int(pc[:4]) if len(pc) >= 4 else 0
            mo = int(pc[4:6]) if len(pc) >= 6 else 0
            period_set[pc] = {
                "period_code": pc,
                "period_name": item.get("period_name", ""),
                "year": yr,
                "month": mo,
                "quarter": (mo - 1) // 3 + 1,
                "year_month": f"{yr:04d}-{mo:02d}",
            }

    for indicator in indicator_set.values():
        existing = session.query(DimIndicator).filter(
            DimIndicator.indicator_id == indicator["indicator_id"]
        ).first()
        if not existing:
            dim = DimIndicator(**indicator)
            session.add(dim)

    for period in period_set.values():
        existing = session.query(DimPeriod).filter(
            DimPeriod.period_code == period["period_code"]
        ).first()
        if not existing:
            dim = DimPeriod(**period)
            session.add(dim)

    session.commit()
    print(f"  -> DIM指标维度: {len(indicator_set)} 个")
    print(f"  -> DIM时间维度: {len(period_set)} 个")


def _parse_category(name: str) -> str:
    if "二手" in name:
        return "二手住宅"
    elif "新建商品住宅" in name:
        return "新建商品住宅"
    elif "新建住宅" in name:
        return "新建住宅"
    return "其他"


def step5_aggregate_dws(session, city_code: str, city_name: str):
    """Step 5: DWD -> DWS 汇总层"""
    print("\n[Step 5] 汇总 DWS 数据层...")

    rows = session.query(DwdHousingPriceDi).filter(
        DwdHousingPriceDi.city_code == city_code
    ).order_by(DwdHousingPriceDi.period_code).all()

    if not rows:
        print("  -> 无数据可汇总")
        return

    monthly_map = {}
    for r in rows:
        key = r.period_code
        if key not in monthly_map:
            monthly_map[key] = {}
        monthly_map[key][r.indicator_base] = r

    count_new = 0
    for period_code, indicators in sorted(monthly_map.items()):
        existing = session.query(DwsCityPriceMonthly).filter(
            DwsCityPriceMonthly.city_code == city_code,
            DwsCityPriceMonthly.period_code == period_code,
        ).first()

        yr = int(period_code[:4]) if len(period_code) >= 4 else 0
        mo = int(period_code[4:6]) if len(period_code) >= 6 else 0

        def _get_val(base_keyword: str) -> float:
            for k, v in indicators.items():
                if base_keyword in k:
                    return v.value
            return None

        data = {
            "city_code": city_code,
            "city_name": city_name,
            "period_code": period_code,
            "year": yr, "month": mo,
            "new_house_mom": _get_val("新建住宅销售价格指数 (上月=100)"),
            "new_house_yoy": _get_val("新建住宅销售价格指数 (上年同月=100)"),
            "new_house_ytd": _get_val("新建住宅销售价格指数 (上年同期=100)"),
            "new_house_base": _get_val("新建住宅销售价格指数 (当期基期年=100)"),
            "new_residential_mom": _get_val("新建商品住宅销售价格指数 (上月=100)"),
            "new_residential_yoy": _get_val("新建商品住宅销售价格指数 (上年同月=100)"),
            "new_residential_ytd": _get_val("新建商品住宅销售价格指数 (上年同期=100)"),
            "new_residential_base": _get_val("新建商品住宅销售价格指数 (当期基期年=100)"),
            "second_hand_mom": _get_val("二手住宅销售价格指数 (上月=100)"),
            "second_hand_yoy": _get_val("二手住宅销售价格指数 (上年同月=100)"),
            "second_hand_ytd": _get_val("二手住宅销售价格指数 (上年同期=100)"),
            "second_hand_base": _get_val("二手住宅销售价格指数 (当期基期年=100)"),
        }

        if existing:
            for k, v in data.items():
                if k not in ("city_code", "city_name", "period_code", "year", "month"):
                    setattr(existing, k, v)
            existing.etl_time = datetime.now()
        else:
            session.add(DwsCityPriceMonthly(**data))
            count_new += 1

    session.commit()
    print(f"  -> DWS月度汇总: 新增 {count_new} 条")

    # 趋势汇总
    monthly_rows = session.query(DwsCityPriceMonthly).filter(
        DwsCityPriceMonthly.city_code == city_code
    ).order_by(DwsCityPriceMonthly.period_code).all()

    if monthly_rows:
        latest = monthly_rows[-1]

        def _calc_trend(vals, n):
            non_null = [v for v in vals[-n:] if v is not None]
            if len(non_null) < 2:
                return "数据不足"
            recent = non_null[-1] - non_null[0]
            if recent > 0.5:
                return "上升"
            elif recent < -0.5:
                return "下降"
            return "平稳"

        yoy_vals = [r.new_residential_yoy for r in monthly_rows if r.new_residential_yoy is not None]

        trend = session.query(DwsCityPriceTrend).filter(
            DwsCityPriceTrend.city_code == city_code
        ).first()

        trend_data = {
            "city_code": city_code,
            "city_name": city_name,
            "latest_period": latest.period_code,
            "latest_new_residential_mom": latest.new_residential_mom,
            "latest_new_residential_yoy": latest.new_residential_yoy,
            "latest_second_hand_mom": latest.second_hand_mom,
            "latest_second_hand_yoy": latest.second_hand_yoy,
            "trend_3m": _calc_trend(yoy_vals, 3),
            "trend_6m": _calc_trend(yoy_vals, 6),
            "trend_12m": _calc_trend(yoy_vals, 12),
            "max_yoy_period": monthly_rows[yoy_vals.index(max(yoy_vals))].period_code if yoy_vals else None,
            "max_yoy_value": max(yoy_vals) if yoy_vals else None,
            "min_yoy_period": monthly_rows[yoy_vals.index(min(yoy_vals))].period_code if yoy_vals else None,
            "min_yoy_value": min(yoy_vals) if yoy_vals else None,
        }

        if trend:
            for k, v in trend_data.items():
                setattr(trend, k, v)
            trend.etl_time = datetime.now()
        else:
            session.add(DwsCityPriceTrend(**trend_data))
        session.commit()
        print(f"  -> DWS趋势汇总: 已更新")


def step6_generate_ads(session, city_code: str, city_name: str):
    """Step 6: DWS -> ADS 应用层"""
    print("\n[Step 6] 生成 ADS 应用数据层...")

    trend = session.query(DwsCityPriceTrend).filter(
        DwsCityPriceTrend.city_code == city_code
    ).first()

    if not trend:
        print("  -> 无趋势数据，跳过报告生成")
        return

    # 生成报告
    report_id = f"RPT_{city_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    report_title = f"{city_name}市住宅销售价格分析报告"

    summary = f"{city_name}市最新新建商品住宅环比为{trend.latest_new_residential_mom}（上月=100），" \
              f"同比为{trend.latest_new_residential_yoy}（上年同月=100）；" \
              f"二手住宅环比{trend.latest_second_hand_mom}，同比{trend.latest_second_hand_yoy}。" \
              f"近3月趋势：{trend.trend_3m}，近12月趋势：{trend.trend_12m}。"

    mom_text = f"新建商品住宅环比指数为{trend.latest_new_residential_mom}，" \
               f"{'价格较上月上涨' if trend.latest_new_residential_mom and trend.latest_new_residential_mom > 100 else '价格较上月下跌' if trend.latest_new_residential_mom and trend.latest_new_residential_mom < 100 else '价格与上月持平'}。"

    yoy_text = f"新建商品住宅同比指数为{trend.latest_new_residential_yoy}，" \
               f"{'价格较上年同月上涨，市场整体呈升温态势' if trend.latest_new_residential_yoy and trend.latest_new_residential_yoy > 100 else '价格较上年同月下跌，市场存在调整压力' if trend.latest_new_residential_yoy and trend.latest_new_residential_yoy < 100 else '价格与上年同月持平'}。"

    trend_text = f"近12月新建商品住宅价格指数同比趋势为{trend.trend_12m}，近6月为{trend.trend_6m}，近3月为{trend.trend_3m}。"

    chart_data = json.dumps(_build_chart_data(session, city_code), ensure_ascii=False)

    report = AdsCityPriceReport(
        report_id=report_id,
        city_code=city_code,
        city_name=city_name,
        report_title=report_title,
        report_period=trend.latest_period or "",
        summary_text=summary,
        mom_analysis=mom_text,
        yoy_analysis=yoy_text,
        trend_analysis=trend_text,
        chart_data_json=chart_data,
        report_status="published",
    )
    session.add(report)
    session.commit()
    print(f"  -> ADS报告: {report_id}")


def _build_chart_data(session, city_code: str) -> Dict:
    monthly = session.query(DwsCityPriceMonthly).filter(
        DwsCityPriceMonthly.city_code == city_code
    ).order_by(DwsCityPriceMonthly.period_code).all()

    return {
        "xAxis": [m.period_code for m in monthly],
        "series": [
            {"name": "新建商品住宅环比", "data": [m.new_residential_mom for m in monthly]},
            {"name": "新建商品住宅同比", "data": [m.new_residential_yoy for m in monthly]},
            {"name": "二手住宅环比", "data": [m.second_hand_mom for m in monthly]},
            {"name": "二手住宅同比", "data": [m.second_hand_yoy for m in monthly]},
        ]
    }


def run_pipeline(city_names: List[str] = None):
    """运行完整 ETL 流水线"""
    print("=" * 60)
    print("  屋檐 ETL 数据流水线")
    print("=" * 60)

    init_db()
    session = get_session()

    try:
        print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        step1_collect_city_list(session)
        safe_sleep()

        if city_names:
            cities = [
                {"show_name": n, "name_value": _get_city_code(n)}
                for n in city_names
            ]
        else:
            cities = session.query(DimCity).all()
            cities = [{"show_name": c.city_name, "name_value": c.city_code} for c in cities]

        for city in cities:
            if not city["name_value"]:
                print(f"\n  [跳过] {city['show_name']}: 未找到城市编码")
                continue

            records = step2_collect_price_data(
                session, city["name_value"], city["show_name"],
                "202506", "202605"
            )
            safe_sleep()

            if records:
                step3_load_dwd(session, records)
                step4_load_dim(session, records)
                step5_aggregate_dws(session, city["name_value"], city["show_name"])
                step6_generate_ads(session, city["name_value"], city["show_name"])

        print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        _print_summary(session)

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def _get_city_code(city_name: str) -> str:
    session = get_session()
    try:
        city = session.query(DimCity).filter(
            (DimCity.city_name == city_name)
        ).first()
        if city:
            return city.city_code

        # 从 city_list_raw 查
        raw = session.query(OdsCityListRaw).first()
        if raw:
            data = json.loads(raw.raw_json)
            for item in data.get("data", []):
                if item["show_name"] == city_name:
                    return item["name_value"]
    finally:
        session.close()
    return ""


def _print_summary(session):
    print("\n" + "=" * 60)
    print("  数据统计摘要")
    print("=" * 60)
    print(f"  ODS 城市列表原始记录: {session.query(OdsCityListRaw).count()}")
    print(f"  ODS 价格原始记录:     {session.query(OdsHousingPriceRaw).count()}")
    print(f"  DWD 明细记录:         {session.query(DwdHousingPriceDi).count()}")
    print(f"  DIM 城市维度:         {session.query(DimCity).count()}")
    print(f"  DIM 指标维度:         {session.query(DimIndicator).count()}")
    print(f"  DIM 时间维度:         {session.query(DimPeriod).count()}")
    print(f"  DWS 月度汇总:         {session.query(DwsCityPriceMonthly).count()}")
    print(f"  DWS 趋势汇总:         {session.query(DwsCityPriceTrend).count()}")
    print(f"  ADS 分析报告:         {session.query(AdsCityPriceReport).count()}")
    print(f"  ADS 排名数据:         {session.query(AdsCityPriceRank).count()}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="屋檐 ETL 数据流水线")
    parser.add_argument("--cities", nargs="*", help="要采集的城市名称列表")
    args = parser.parse_args()
    run_pipeline(args.cities)
