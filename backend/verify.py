import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db.models import get_session, DwsCityPriceMonthly, DwsCityPriceTrend, AdsCityPriceReport

s = get_session()

print("=== Nanjing Monthly Price Summary (DWS) ===")
print(f"{'Period':>10} {'New_MoM':>8} {'New_YoY':>8} {'SH_MoM':>8} {'SH_YoY':>8}")
for r in s.query(DwsCityPriceMonthly).order_by(DwsCityPriceMonthly.period_code).all():
    print(f"{r.period_code:>10} {str(r.new_residential_mom):>8} {str(r.new_residential_yoy):>8} {str(r.second_hand_mom):>8} {str(r.second_hand_yoy):>8}")

print()
t = s.query(DwsCityPriceTrend).first()
if t:
    print("=== Trend Analysis ===")
    print(f"Latest Period: {t.latest_period}")
    print(f"New Residential MoM: {t.latest_new_residential_mom}")
    print(f"New Residential YoY: {t.latest_new_residential_yoy}")
    print(f"Second Hand MoM: {t.latest_second_hand_mom}")
    print(f"Second Hand YoY: {t.latest_second_hand_yoy}")
    print(f"Trend 3m: {t.trend_3m}")
    print(f"Trend 6m: {t.trend_6m}")
    print(f"Trend 12m: {t.trend_12m}")
    print(f"Max YoY: {t.max_yoy_period} = {t.max_yoy_value}")
    print(f"Min YoY: {t.min_yoy_period} = {t.min_yoy_value}")

print()
rpt = s.query(AdsCityPriceReport).first()
if rpt:
    print("=== ADS Report Summary ===")
    print(rpt.summary_text)

s.close()
