"""Bel Zhou - reproducible Weeks 1-4 data engineering workflow.
See README.md for required inputs and scope boundary.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
ROOT=Path('.')
OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)

def clean_columns(df):
    x=df.copy(); x.columns=[c.strip().replace('\\_','_') for c in x.columns]; return x

def load_aemo():
    pv=clean_columns(pd.read_csv(ROOT/'Rooftop_PV_202501_to_202608_Combined.csv'))
    dm=clean_columns(pd.read_csv(ROOT/'Operational_Demand_202501_to_202608_Combined.csv'))
    pv=pv[(pv.REGIONID=='NSW1') & (pv.TYPE.astype(str).str.upper()=='MEASUREMENT')].copy()
    dm=dm[dm.REGIONID=='NSW1'].copy()
    pv['DATETIME']=pd.to_datetime(pv.INTERVAL_DATETIME,dayfirst=True,errors='coerce')
    dm['DATETIME']=pd.to_datetime(dm.INTERVAL_DATETIME,dayfirst=True,errors='coerce')
    pv=pv[['DATETIME','POWER_MW','QUALITY_INDICATOR']].rename(columns={'POWER_MW':'ROOFTOP_PV_MW','QUALITY_INDICATOR':'PV_QUALITY_INDICATOR'})
    dm=dm[['DATETIME','OPERATIONAL_DEMAND','OPERATIONAL_DEMAND_ADJUSTMENT','WDR_ESTIMATE']].rename(columns={'OPERATIONAL_DEMAND':'OPERATIONAL_DEMAND_MW'})
    return pv.sort_values('DATETIME').drop_duplicates('DATETIME'),dm.sort_values('DATETIME').drop_duplicates('DATETIME')

def load_weather():
    w=clean_columns(pd.read_csv(ROOT/'Sydney_Airport_Weather_202508_to_202608_Combined.csv'))
    w['DATE']=pd.to_datetime(w.Date,dayfirst=True,errors='coerce').dt.normalize()
    rename={'Minimum temperature (°C)':'MIN_TEMP_C','Maximum temperature (°C)':'MAX_TEMP_C','Rainfall (mm)':'RAINFALL_MM','Sunshine (hours)':'SUNSHINE_HOURS','9am relative humidity (%)':'RH_9AM_PCT','9am cloud amount (oktas)':'CLOUD_9AM_OKTAS','3pm relative humidity (%)':'RH_3PM_PCT','3pm cloud amount (oktas)':'CLOUD_3PM_OKTAS'}
    w=w[['DATE']+[c for c in rename if c in w]].rename(columns=rename).drop_duplicates('DATE')
    s=pd.concat([clean_columns(pd.read_csv(ROOT/'Sydney Airport North Daily Solar Exposure 2025.csv')),clean_columns(pd.read_csv(ROOT/'Sydney Airport North Daily Solar Exposure 2026.csv'))],ignore_index=True)
    s['DATE']=pd.to_datetime(dict(year=s.Year,month=s.Month,day=s.Day))
    val=[c for c in s if 'solar exposure' in c.lower()][0]
    return w.merge(s[['DATE',val]].rename(columns={val:'SOLAR_EXPOSURE_MJ_M2'}),on='DATE',how='left')

def add_features(df):
    df=df.sort_values('DATETIME').copy(); dt=df.DATETIME
    df['DATE']=dt.dt.normalize(); df['YEAR']=dt.dt.year; df['MONTH']=dt.dt.month; df['MONTH_NAME']=dt.dt.month_name(); df['QUARTER']='Q'+dt.dt.quarter.astype(str)
    df['DAY_OF_WEEK']=dt.dt.day_name(); df['WEEKEND_FLAG']=(dt.dt.dayofweek>=5).astype(int); df['HOUR']=dt.dt.hour; df['MINUTE']=dt.dt.minute; df['HALF_HOUR_SLOT']=dt.dt.strftime('%H:%M')
    df['SEASON']=df.MONTH.map({12:'Summer',1:'Summer',2:'Summer',3:'Autumn',4:'Autumn',5:'Autumn',6:'Winter',7:'Winter',8:'Winter',9:'Spring',10:'Spring',11:'Spring'})
    for lag in [1,2,4]:
        df[f'PV_LAG_{lag}']=df.ROOFTOP_PV_MW.shift(lag); df[f'DEMAND_LAG_{lag}']=df.OPERATIONAL_DEMAND_MW.shift(lag)
    df['DELTA_PV_MW']=df.ROOFTOP_PV_MW.diff(); df['DELTA_DEMAND_MW']=df.OPERATIONAL_DEMAND_MW.diff()
    df['PV_RAMP_DIRECTION']=np.select([df.DELTA_PV_MW>0,df.DELTA_PV_MW<0],['Increase','Decrease'],'No change'); df.loc[df.DELTA_PV_MW.isna(),'PV_RAMP_DIRECTION']=np.nan
    holidays={'2025-10-06':'Labour Day','2025-12-25':'Christmas Day','2025-12-26':'Boxing Day','2026-01-01':"New Year’s Day",'2026-01-26':'Australia Day','2026-04-03':'Good Friday','2026-04-04':'Easter Saturday','2026-04-05':'Easter Sunday','2026-04-06':'Easter Monday','2026-04-25':'Anzac Day','2026-04-27':'Additional public holiday for Anzac Day','2026-06-08':"King’s Birthday"}
    key=dt.dt.strftime('%Y-%m-%d'); df['NSW_PUBLIC_HOLIDAY_FLAG']=key.isin(holidays).astype(int); df['NSW_PUBLIC_HOLIDAY_NAME']=key.map(holidays).fillna('')
    return df

def validate(df):
    exp=pd.date_range(df.DATETIME.min(),df.DATETIME.max(),freq='30min')
    return pd.DataFrame({'Metric':['Rows','Start','End','Duplicate timestamps','Missing half-hours','Missing PV','Missing demand'],'Value':[len(df),df.DATETIME.min(),df.DATETIME.max(),df.DATETIME.duplicated().sum(),len(exp.difference(df.DATETIME)),df.ROOFTOP_PV_MW.isna().sum(),df.OPERATIONAL_DEMAND_MW.isna().sum()]})

def create_eda(df):
    monthly=df.set_index('DATETIME').resample('MS').agg(Avg_PV_MW=('ROOFTOP_PV_MW','mean'),Avg_Demand_MW=('OPERATIONAL_DEMAND_MW','mean')).reset_index(); monthly.to_csv(OUT/'monthly_summary.csv',index=False)
    corr=df[['ROOFTOP_PV_MW','OPERATIONAL_DEMAND_MW','SOLAR_EXPOSURE_MJ_M2','SUNSHINE_HOURS','MAX_TEMP_C','MIN_TEMP_C','RAINFALL_MM','DELTA_PV_MW','DELTA_DEMAND_MW']].corr(); corr.to_csv(OUT/'correlation_matrix.csv')
    for col,title,name in [('Avg_PV_MW','Monthly average NSW1 rooftop PV','monthly_pv.png'),('Avg_Demand_MW','Monthly average NSW1 operational demand','monthly_demand.png')]:
        plt.figure(figsize=(10,5)); plt.plot(monthly.DATETIME,monthly[col]); plt.title(title); plt.xlabel('Month'); plt.ylabel('MW'); plt.xticks(rotation=45); plt.tight_layout(); plt.savefig(OUT/name,dpi=160); plt.close()

def main():
    pv,dm=load_aemo(); weather=load_weather(); core=pv.merge(dm,on='DATETIME',how='inner',validate='one_to_one'); core['DATE']=core.DATETIME.dt.normalize()
    df=core.merge(weather,on='DATE',how='left'); df=df[(df.DATE>=weather.DATE.min())&(df.DATE<=weather.DATE.max())]; df=add_features(df)
    validate(df).to_csv(OUT/'data_quality_summary.csv',index=False); create_eda(df); df.to_csv(OUT/'NSW1_Historical_Modelling_Dataset_Week4_v2.csv',index=False,date_format='%Y-%m-%d %H:%M:%S')
if __name__=='__main__': main()
