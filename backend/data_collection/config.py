"""
数据采集配置
"""
import os

# 国家统计局接口地址
STATS_BASE_URL = os.getenv("STATS_BASE_URL", "https://data.stats.gov.cn/dg/website/publicrelease/web/external")

# 接口1: 获取70个城市列表
CITY_LIST_API = f"{STATS_BASE_URL}/getDasByDaCatalogId"
CITY_LIST_DA_CID = "44016f1bffeb4ea49fe34e100c6415fb"

# 接口2: 获取城市住宅销售价格数据
PRICE_API = f"{STATS_BASE_URL}/stream/esData"
PRICE_CID = "3eb43764c74741469b745c396cf002d1"
PRICE_ROOT_ID = "327ecbb2e6b14c669da1e99e39faa24c"

# 70个大中城市住宅销售价格指数的35个指标ID
PRICE_INDICATOR_IDS = [
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
]

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# 风控间隔配置(秒)
SLEEP_BETWEEN_API_CALLS = (1, 5)      # 每次API调用之间
SLEEP_BETWEEN_CITIES = (180, 300)     # 每个城市之间(3-5分钟)

# 默认采集时间范围
DEFAULT_START_YEAR = 2020
DEFAULT_END_YEAR = 2025

# 数据源标识
DATA_SOURCE = "国家统计局"
