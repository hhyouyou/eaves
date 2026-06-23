"""
数据汇总器: DWD + DIM -> DWS/ADS
"""
from datetime import datetime
from typing import List, Dict

from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import (
    DwdHousingPriceDi, DwsCityPriceMonthly, DwsCityPriceTrend,
    AdsCityPriceReport
)


def _get_val_by_base(records: List[DwdHousingPriceDi], base_keyword: str) -> float:
    """根据基期关键词查找指标值"""
    for r in records:
        if base_keyword in (r.indicator_base or ""):
            return r.value
    return None


def aggregate_city_monthly(session: Session, city_code: str, city_name: str):
    """DWS层: 按城市+月份汇总房价指标"""
    rows = session.query(DwdHousingPriceDi).filter(
        DwdHousingPriceDi.city_code == city_code
    ).order_by(DwdHousingPriceDi.period_code).all()

    if not rows:
        return

    # 按期间分组
    monthly_map: Dict[str, List[DwdHousingPriceDi]] = {}
    for r in rows:
        monthly_map.setdefault(r.period_code, []).append(r)

    count_new = 0
    for period_code, records in sorted(monthly_map.items()):
        existing = session.query(DwsCityPriceMonthly).filter(
            DwsCityPriceMonthly.city_code == city_code,
            DwsCityPriceMonthly.period_code == period_code,
        ).first()

        yr = int(period_code[:4]) if len(period_code) >= 4 else 0
        mo = int(period_code[4:6]) if len(period_code) >= 6 else 0

        data = {
            "city_code": city_code,
            "city_name": city_name,
            "period_code": period_code,
            "year": yr,
            "month": mo,
            "new_house_mom": _get_val_by_base(records, "新建住宅销售价格指数 (上月=100)"),
            "new_house_yoy": _get_val_by_base(records, "新建住宅销售价格指数 (上年同月=100)"),
            "new_house_ytd": _get_val_by_base(records, "新建住宅销售价格指数 (上年同期=100)"),
            "new_house_base": _get_val_by_base(records, "新建住宅销售价格指数 (当期基期年=100)"),
            "new_residential_mom": _get_val_by_base(records, "新建商品住宅销售价格指数 (上月=100)"),
            "new_residential_yoy": _get_val_by_base(records, "新建商品住宅销售价格指数 (上年同月=100)"),
            "new_residential_ytd": _get_val_by_base(records, "新建商品住宅销售价格指数 (上年同期=100)"),
            "new_residential_base": _get_val_by_base(records, "新建商品住宅销售价格指数 (当期基期年=100)"),
            "second_hand_mom": _get_val_by_base(records, "二手住宅销售价格指数 (上月=100)"),
            "second_hand_yoy": _get_val_by_base(records, "二手住宅销售价格指数 (上年同月=100)"),
            "second_hand_ytd": _get_val_by_base(records, "二手住宅销售价格指数 (上年同期=100)"),
            "second_hand_base": _get_val_by_base(records, "二手住宅销售价格指数 (当期基期年=100)"),
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
    return {"new": count_new}


def _calc_trend(vals: List[float], n: int) -> str:
    """计算最近n个值的趋势"""
    non_null = [v for v in vals[-n:] if v is not None]
    if len(non_null) < 2:
        return "数据不足"
    recent = non_null[-1] - non_null[0]
    if recent > 0.5:
        return "上升"
    elif recent < -0.5:
        return "下降"
    return "平稳"


def aggregate_city_trend(session: Session, city_code: str, city_name: str):
    """DWS层: 计算城市房价趋势特征"""
    monthly_rows = session.query(DwsCityPriceMonthly).filter(
        DwsCityPriceMonthly.city_code == city_code
    ).order_by(DwsCityPriceMonthly.period_code).all()

    if not monthly_rows:
        return

    latest = monthly_rows[-1]
    yoy_vals = [r.new_residential_yoy for r in monthly_rows if r.new_residential_yoy is not None]

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

    existing = session.query(DwsCityPriceTrend).filter(
        DwsCityPriceTrend.city_code == city_code
    ).first()

    if existing:
        for k, v in trend_data.items():
            setattr(existing, k, v)
        existing.etl_time = datetime.now()
    else:
        session.add(DwsCityPriceTrend(**trend_data))

    session.commit()


def _build_chart_data(session: Session, city_code: str) -> Dict:
    """构建图表数据"""
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


def generate_report(session: Session, city_code: str, city_name: str) -> str:
    """ADS层: 生成城市房价分析报告"""
    trend = session.query(DwsCityPriceTrend).filter(
        DwsCityPriceTrend.city_code == city_code
    ).first()

    if not trend:
        return None

    report_id = f"RPT_{city_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    report_title = f"{city_name}市住宅销售价格分析报告"

    summary = (f"{city_name}市最新新建商品住宅环比为{trend.latest_new_residential_mom}（上月=100），"
               f"同比为{trend.latest_new_residential_yoy}（上年同月=100）；"
               f"二手住宅环比{trend.latest_second_hand_mom}，同比{trend.latest_second_hand_yoy}。"
               f"近3月趋势：{trend.trend_3m}，近12月趋势：{trend.trend_12m}。")

    def _mom_text(val):
        if val is None:
            return "数据缺失"
        if val > 100:
            return "价格较上月上涨"
        elif val < 100:
            return "价格较上月下跌"
        return "价格与上月持平"

    def _yoy_text(val):
        if val is None:
            return "数据缺失"
        if val > 100:
            return "价格较上年同月上涨，市场整体呈升温态势"
        elif val < 100:
            return "价格较上年同月下跌，市场存在调整压力"
        return "价格与上年同月持平"

    mom_text = f"新建商品住宅环比指数为{trend.latest_new_residential_mom}，{_mom_text(trend.latest_new_residential_mom)}。"
    yoy_text = f"新建商品住宅同比指数为{trend.latest_new_residential_yoy}，{_yoy_text(trend.latest_new_residential_yoy)}。"
    trend_text = f"近12月新建商品住宅价格指数同比趋势为{trend.trend_12m}，近6月为{trend.trend_6m}，近3月为{trend.trend_3m}。"

    import json
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
    return report_id
