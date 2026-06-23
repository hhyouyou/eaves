"""
数据加载器: 将采集结果写入数仓各层
"""
import json
from datetime import datetime
from typing import Dict, List, Any

from sqlalchemy.orm import Session

from db.models import (
    OdsCityListRaw, OdsHousingPriceRaw,
    DwdHousingPriceDi,
    DimCity, DimIndicator, DimPeriod,
)


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


def load_ods_city_list(session: Session, result: Dict[str, Any]):
    """ODS层: 写入城市列表原始数据"""
    raw = OdsCityListRaw(
        raw_json=json.dumps(result["data"], ensure_ascii=False),
        api_url=result["api_url"],
        response_code=result["response_code"],
        data_source=result["data_source"],
    )
    session.add(raw)
    session.commit()


def load_dim_city(session: Session, city_data: List[Dict[str, Any]]):
    """DIM层: 写入/更新城市维度"""
    for city in city_data:
        code = city.get("name_value", "")
        if not code:
            continue

        existing = session.query(DimCity).filter(DimCity.city_code == code).first()
        prov_code = code[:2]
        prov_name = PROVINCE_MAP.get(prov_code, "")
        city_name = city.get("show_name", "")

        if existing:
            existing.city_name = city_name
            existing.city_full_name = city.get("name_text", "")
            existing.province_code = prov_code
            existing.province_name = prov_name
            existing.region = REGION_MAP.get(prov_name, "")
            existing.tier = TIER_MAP.get(city_name, "三线")
            existing.update_time = datetime.now()
        else:
            dim = DimCity(
                city_code=code,
                city_name=city_name,
                city_full_name=city.get("name_text", ""),
                province_code=prov_code,
                province_name=prov_name,
                region=REGION_MAP.get(prov_name, ""),
                tier=TIER_MAP.get(city_name, "三线"),
            )
            session.add(dim)
    session.commit()


def load_ods_price(session: Session, result: Dict[str, Any]):
    """ODS层: 写入价格数据原始数据"""
    raw = OdsHousingPriceRaw(
        raw_json=json.dumps(result["data"], ensure_ascii=False),
        request_params=json.dumps(result["request_params"], ensure_ascii=False),
        api_url=result["api_url"],
        response_code=result["response_code"],
        city_code=result["city_code"],
        period_range=result["period_range"],
        data_source=result["data_source"],
    )
    session.add(raw)
    session.commit()


def load_dwd_price(session: Session, records: List[Dict[str, Any]]) -> Dict[str, int]:
    """DWD层: 写入明细数据"""
    count_new = 0
    count_update = 0

    for item in records:
        city_code = item.get("da", "")
        indicator_id = item.get("_id", "")
        period_code = item.get("period_code", "")

        existing = session.query(DwdHousingPriceDi).filter(
            DwdHousingPriceDi.city_code == city_code,
            DwdHousingPriceDi.indicator_id == indicator_id,
            DwdHousingPriceDi.period_code == period_code,
        ).first()

        value = _parse_float(item.get("value"))

        if existing:
            existing.value = value
            existing.etl_time = datetime.now()
            count_update += 1
        else:
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
    return {"new": count_new, "update": count_update}


def load_dim_indicator_and_period(session: Session, records: List[Dict[str, Any]]):
    """DIM层: 写入/更新指标维度和时间维度"""
    indicators = {}
    periods = {}

    for item in records:
        iid = item.get("_id", "")
        if iid and iid not in indicators:
            indicators[iid] = {
                "indicator_id": iid,
                "indicator_name": item.get("_name", ""),
                "indicator_category": _parse_category(item.get("_name", "")),
                "indicator_type": "价格指数",
                "base_period": _parse_base_period(item.get("i_showname", "")),
                "unit": item.get("du_name", ""),
                "catalog_id": item.get("catalogid", ""),
                "sort_order": item.get("ds_order", 0),
            }

        pc = item.get("period_code", "")
        if pc and pc not in periods:
            yr = int(pc[:4]) if len(pc) >= 4 else 0
            mo = int(pc[4:6]) if len(pc) >= 6 else 0
            periods[pc] = {
                "period_code": pc,
                "period_name": item.get("period_name", ""),
                "year": yr,
                "month": mo,
                "quarter": (mo - 1) // 3 + 1,
                "year_month": f"{yr:04d}-{mo:02d}",
            }

    for indicator in indicators.values():
        existing = session.query(DimIndicator).filter(
            DimIndicator.indicator_id == indicator["indicator_id"]
        ).first()
        if existing:
            for k, v in indicator.items():
                setattr(existing, k, v)
            existing.update_time = datetime.now()
        else:
            session.add(DimIndicator(**indicator))

    for period in periods.values():
        existing = session.query(DimPeriod).filter(
            DimPeriod.period_code == period["period_code"]
        ).first()
        if not existing:
            session.add(DimPeriod(**period))

    session.commit()


def _parse_float(value) -> float:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_category(name: str) -> str:
    if "二手" in name:
        return "二手住宅"
    elif "新建商品住宅" in name:
        return "新建商品住宅"
    elif "新建住宅" in name:
        return "新建住宅"
    return "其他"


def _parse_base_period(showname: str) -> str:
    if "上月=100" in showname:
        return "上月=100"
    elif "上年同月=100" in showname:
        return "上年同月=100"
    elif "上年同期=100" in showname:
        return "上年同期=100"
    elif "当期基期年=100" in showname:
        return "当期基期年=100"
    return ""
