# 数据采集模块 (data_collection)

屋檐项目的数据采集模块，负责从国家统计局获取70个大中城市住宅销售价格数据，并写入数仓。

---

## 目录结构

```
data_collection/
├── __init__.py        # 模块标识
├── config.py          # 接口配置、常量、风控参数
├── client.py          # HTTP 客户端，封装带风控间隔的接口调用
├── loader.py          # 数据加载器，ODS/DWD/DIM 数据写入
├── aggregator.py      # 数据汇总器，DWS/ADS 数据生成
├── runner.py          # 采集运行器，支持全量/单月/单城市模式
├── scheduler.py       # 定时任务入口，供 crontab/TRAE Schedule 调用
└── README.md          # 本文件
```

---

## 使用方式

### 1. 全量初始化70城历史数据

```bash
python -m data_collection.runner full
```

参数：
- `--start-year`：起始年份，默认2020
- `--end-year`：结束年份，默认2025

示例：
```bash
python -m data_collection.runner full --start-year 2020 --end-year 2025
```

**注意：** 全量初始化会自动跳过南京市（假设已初始化），其他城市按城市编码顺序依次采集，城市之间间隔3-5分钟。

### 2. 单个城市历史数据补采

```bash
python -m data_collection.runner single --city 北京
```

### 3. 月度增量更新

```bash
python -m data_collection.runner monthly
```

参数：
- `--year`：指定年份
- `--month`：指定月份

默认更新上个月数据。

### 4. 定时任务

使用 `scheduler.py` 作为定时任务入口：

```bash
# 月度增量
python -m data_collection.scheduler --mode monthly

# 全量初始化
python -m data_collection.scheduler --mode full
```

---

## 风控策略

| 场景 | 间隔 |
|------|------|
| 每次API调用之间 | 1-5秒随机 |
| 每个城市之间 | 3-5分钟随机 |

可在 `config.py` 中调整：
- `SLEEP_BETWEEN_API_CALLS`
- `SLEEP_BETWEEN_CITIES`

---

## 数据源

国家统计局 - 70个大中城市住宅销售价格指数
- 接口1：城市列表
- 接口2：价格数据

---

## 数据流

```
国家统计局API
    ↓
client.py (带风控请求)
    ↓
loader.py (ODS → DWD/DIM)
    ↓
aggregator.py (DWD/DIM → DWS → ADS)
    ↓
SQLite 数据库
```
