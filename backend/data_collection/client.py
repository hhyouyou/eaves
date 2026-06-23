"""
国家统计局 HTTP 客户端
封装带风控间隔的接口调用
"""
import json
import time
import random
import requests
from typing import Dict, List, Any, Optional

from data_collection.config import (
    HEADERS, CITY_LIST_API, CITY_LIST_DA_CID,
    PRICE_API, PRICE_CID, PRICE_ROOT_ID, PRICE_INDICATOR_IDS,
    SLEEP_BETWEEN_API_CALLS, DATA_SOURCE
)


def _safe_api_sleep():
    """每次API调用后的随机间隔，避免触发反爬"""
    seconds = random.uniform(*SLEEP_BETWEEN_API_CALLS)
    time.sleep(seconds)


def fetch_city_list() -> Dict[str, Any]:
    """
    接口1: 获取70个大中城市列表
    """
    url = f"{CITY_LIST_API}?daCid={CITY_LIST_DA_CID}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    _safe_api_sleep()
    return {
        "data": data,
        "api_url": url,
        "response_code": resp.status_code,
        "data_source": DATA_SOURCE,
    }


def fetch_city_price(
    city_code: str,
    city_name: str,
    start_period: str,
    end_period: str
) -> Dict[str, Any]:
    """
    接口2: 获取指定城市指定时间范围的住宅销售价格数据

    Args:
        city_code: 城市编码，如 "320100000000"
        city_name: 城市名称，如 "南京"
        start_period: 起始期间，如 "202001"
        end_period: 结束期间，如 "202012"
    """
    body = {
        "cid": PRICE_CID,
        "indicatorIds": PRICE_INDICATOR_IDS,
        "daCatalogId": "",
        "das": [
            {"text": city_name, "value": city_code}
        ],
        "showType": "1",
        "dts": [f"{start_period}MM-{end_period}MM"],
        "rootId": PRICE_ROOT_ID,
    }

    resp = requests.post(PRICE_API, headers=HEADERS, json=body, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    _safe_api_sleep()

    # 提取并拍平记录
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

    return {
        "data": data,
        "records": records,
        "api_url": PRICE_API,
        "request_params": body,
        "response_code": resp.status_code,
        "city_code": city_code,
        "city_name": city_name,
        "period_range": f"{start_period}-{end_period}",
        "data_source": DATA_SOURCE,
    }


def fetch_city_price_years(
    city_code: str,
    city_name: str,
    start_year: int,
    end_year: int,
    progress_callback=None,
) -> List[Dict[str, Any]]:
    """
    按年份分段采集一个城市的数据

    Args:
        city_code: 城市编码
        city_name: 城市名称
        start_year: 起始年份
        end_year: 结束年份
        progress_callback: 可选回调函数(year, result)

    Returns:
        所有年份合并后的记录列表
    """
    all_records = []
    for year in range(start_year, end_year + 1):
        start = f"{year:04d}01"
        end = f"{year:04d}12"
        result = fetch_city_price(city_code, city_name, start, end)
        all_records.extend(result["records"])

        if progress_callback:
            progress_callback(year, result)

    return all_records
