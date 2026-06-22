from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

# ==================== ODS 层 ====================

class OdsCityListRaw(Base):
    """城市列表原始数据"""
    __tablename__ = "ods_city_list_raw"

    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_json = Column(Text, nullable=False)
    api_url = Column(String(500), nullable=False)
    response_code = Column(Integer)
    etl_time = Column(DateTime, default=datetime.now)
    data_source = Column(String(100), default="国家统计局")

class OdsHousingPriceRaw(Base):
    """住宅销售价格原始数据"""
    __tablename__ = "ods_housing_price_raw"

    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_json = Column(Text, nullable=False)
    request_params = Column(Text)
    api_url = Column(String(500), nullable=False)
    response_code = Column(Integer)
    city_code = Column(String(50))
    period_range = Column(String(100))
    etl_time = Column(DateTime, default=datetime.now)
    data_source = Column(String(100), default="国家统计局")

# ==================== DWD 层 ====================

class DwdHousingPriceDi(Base):
    """住宅销售价格明细表"""
    __tablename__ = "dwd_housing_price_di"
    __table_args__ = (
        UniqueConstraint("city_code", "indicator_id", "period_code", name="uq_dwd_price"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_code = Column(String(50), nullable=False, index=True)
    city_name = Column(String(100), nullable=False)
    indicator_id = Column(String(100), nullable=False, index=True)
    indicator_name = Column(String(200), nullable=False)
    indicator_base = Column(String(100))
    period_code = Column(String(20), nullable=False, index=True)
    period_name = Column(String(50))
    value = Column(Float)
    unit = Column(String(50))
    data_type = Column(String(50))
    catalog_id = Column(String(100))
    etl_time = Column(DateTime, default=datetime.now)
    data_source = Column(String(100), default="国家统计局")

# ==================== DIM 层 ====================

class DimCity(Base):
    """城市维度表"""
    __tablename__ = "dim_city"

    city_code = Column(String(50), primary_key=True)
    city_name = Column(String(100), nullable=False)
    city_full_name = Column(String(200))
    province_code = Column(String(20))
    province_name = Column(String(100))
    region = Column(String(50))
    tier = Column(String(20))
    is_active = Column(Integer, default=1)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class DimIndicator(Base):
    """指标维度表"""
    __tablename__ = "dim_indicator"

    indicator_id = Column(String(100), primary_key=True)
    indicator_name = Column(String(200), nullable=False)
    indicator_category = Column(String(100))
    indicator_type = Column(String(50))
    base_period = Column(String(100))
    unit = Column(String(50))
    catalog_id = Column(String(100))
    sort_order = Column(Integer)
    is_active = Column(Integer, default=1)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class DimPeriod(Base):
    """时间维度表"""
    __tablename__ = "dim_period"

    period_code = Column(String(20), primary_key=True)
    period_name = Column(String(50))
    year = Column(Integer)
    month = Column(Integer)
    quarter = Column(Integer)
    year_month = Column(String(10))
    is_current_month = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    create_time = Column(DateTime, default=datetime.now)

# ==================== DWS 层 ====================

class DwsCityPriceMonthly(Base):
    """城市房价月度汇总"""
    __tablename__ = "dws_city_price_monthly"
    __table_args__ = (
        UniqueConstraint("city_code", "period_code", name="uq_dws_price"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_code = Column(String(50), nullable=False, index=True)
    city_name = Column(String(100), nullable=False)
    period_code = Column(String(20), nullable=False)
    year = Column(Integer)
    month = Column(Integer)
    new_house_mom = Column(Float)
    new_house_yoy = Column(Float)
    new_house_ytd = Column(Float)
    new_house_base = Column(Float)
    new_residential_mom = Column(Float)
    new_residential_yoy = Column(Float)
    new_residential_ytd = Column(Float)
    new_residential_base = Column(Float)
    second_hand_mom = Column(Float)
    second_hand_yoy = Column(Float)
    second_hand_ytd = Column(Float)
    second_hand_base = Column(Float)
    etl_time = Column(DateTime, default=datetime.now)

class DwsCityPriceTrend(Base):
    """城市房价趋势汇总"""
    __tablename__ = "dws_city_price_trend"
    __table_args__ = (
        UniqueConstraint("city_code", name="uq_dws_trend"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_code = Column(String(50), nullable=False, index=True)
    city_name = Column(String(100), nullable=False)
    latest_period = Column(String(20))
    latest_new_residential_mom = Column(Float)
    latest_new_residential_yoy = Column(Float)
    latest_second_hand_mom = Column(Float)
    latest_second_hand_yoy = Column(Float)
    trend_3m = Column(String(20))
    trend_6m = Column(String(20))
    trend_12m = Column(String(20))
    max_yoy_period = Column(String(20))
    max_yoy_value = Column(Float)
    min_yoy_period = Column(String(20))
    min_yoy_value = Column(Float)
    etl_time = Column(DateTime, default=datetime.now)

# ==================== ADS 层 ====================

class AdsCityPriceReport(Base):
    """城市房价分析报告"""
    __tablename__ = "ads_city_price_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(100), unique=True, nullable=False)
    city_code = Column(String(50), nullable=False, index=True)
    city_name = Column(String(100), nullable=False)
    report_title = Column(String(500))
    report_period = Column(String(100))
    summary_text = Column(Text)
    mom_analysis = Column(Text)
    yoy_analysis = Column(Text)
    trend_analysis = Column(Text)
    chart_data_json = Column(Text)
    report_status = Column(String(50), default="published")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class AdsCityPriceRank(Base):
    """城市房价排名"""
    __tablename__ = "ads_city_price_rank"
    __table_args__ = (
        UniqueConstraint("rank_period", "rank_type", "city_code", name="uq_ads_rank"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    rank_period = Column(String(20), nullable=False)
    rank_type = Column(String(50), nullable=False)
    rank_scope = Column(String(50), default="全部")
    city_code = Column(String(50), nullable=False)
    city_name = Column(String(100), nullable=False)
    rank_num = Column(Integer)
    indicator_value = Column(Float)
    change_pct = Column(Float)
    change_direction = Column(String(20))
    create_time = Column(DateTime, default=datetime.now)

class AdsCityPriceComparison(Base):
    """城市对比数据"""
    __tablename__ = "ads_city_price_comparison"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comparison_id = Column(String(100), nullable=False)
    period_code = Column(String(20), nullable=False)
    city_a_code = Column(String(50), nullable=False)
    city_a_name = Column(String(100), nullable=False)
    city_b_code = Column(String(50), nullable=False)
    city_b_name = Column(String(100), nullable=False)
    indicator_type = Column(String(50))
    city_a_value = Column(Float)
    city_b_value = Column(Float)
    diff_value = Column(Float)
    diff_pct = Column(Float)
    winner_city = Column(String(100))
    create_time = Column(DateTime, default=datetime.now)

# ==================== 数据库配置 ====================

DB_PATH = os.path.join(os.path.dirname(__file__), "eaves.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_session():
    return SessionLocal()
