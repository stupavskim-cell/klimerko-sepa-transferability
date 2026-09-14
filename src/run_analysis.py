from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score


def ccc(y,p):
    y=np.asarray(y,float); p=np.asarray(p,float)
    return 2*np.cov(y,p,ddof=1)[0,1]/(np.var(y,ddof=1)+np.var(p,ddof=1)+(y.mean()-p.mean())**2)

def metrics(y,p):
    y=np.asarray(y,float); p=np.asarray(p,float)
    return {'n':len(y),'R2':r2_score(y,p),'RMSE':mean_squared_error(y,p)**0.5,
            'MAE':mean_absolute_error(y,p),'MBE':float(np.mean(p-y)),
            'Pearson':float(np.corrcoef(y,p)[0,1]),'CCC':float(ccc(y,p))}

def prepare(paired_path,met_path):
    paired=pd.read_csv(paired_path,parse_dates=['Date'])
    met=pd.read_csv(met_path,parse_dates=['Date'])
    cols=['City','Date','T2m_mean_C','RH2m_mean_pct','Wind10m_mean_ms','Precipitation_sum_mm']
    d=paired.merge(met[cols],on=['City','Date'],how='left',validate='many_to_one')
    if d[cols[2:]].isna().any().any(): raise ValueError('Missing meteorology after City+Date merge.')
    d['month']=d.Date.dt.month
    d['Heating']=d.Season.eq('Heating').astype(int)
    d['sin_month']=np.sin(2*np.pi*(d.month-1)/12)
    d['cos_month']=np.cos(2*np.pi*(d.month-1)/12)
    return d

def run(paired_path,met_path,outdir,bootstrap=2000):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True)
    d=prepare(paired_path,met_path)
    full=['Klimerko','Heating','sin_month','cos_month','T2m_mean_C','RH2m_mean_pct','Wind10m_mean_ms','Precipitation_sum_mm']
    stages=[('Raw reading',None),('Linear PM',['Klimerko']),('+ season/month',['Klimerko','Heating','sin_month','cos_month']),('+ temperature/RH',['Klimerko','Heating','sin_month','cos_month','T2m_mean_C','RH2m_mean_pct']),('+ full meteorology',full)]
    stage_rows=[]; loco={}
    for pol in ['PM2.5','PM10']:
        x=d[d.Pollutant==pol].copy(); trs=[]; tes=[]
        for city,g in x.groupby('City'):
            g=g.sort_values('Date'); cut=int(np.floor(.7*len(g))); trs.append(g.iloc[:cut]); tes.append(g.iloc[cut:])
        tr=pd.concat(trs); te=pd.concat(tes)
        for name,feats in stages:
            pred=te.Klimerko.to_numpy() if feats is None else LinearRegression().fit(tr[feats],tr.SEPA_city_mean).predict(te[feats])
            stage_rows.append([pol,'Temporal 70/30',name,*metrics(te.SEPA_city_mean,pred).values()])
            blocks=[]
            for city in sorted(x.City.unique()):
                train=x[x.City!=city]; test=x[x.City==city]
                pp=test.Klimerko.to_numpy() if feats is None else LinearRegression().fit(train[feats],train.SEPA_city_mean).predict(test[feats])
                blocks.append(pd.DataFrame({'City':city,'y':test.SEPA_city_mean.to_numpy(),'p':pp}))
            pr=pd.concat(blocks,ignore_index=True); loco[(pol,name)]=pr
            stage_rows.append([pol,'LOCO',name,*metrics(pr.y,pr.p).values()])
    cols=['Pollutant','Validation','Model','n','R2','RMSE','MAE','MBE','Pearson','CCC']
    stage=pd.DataFrame(stage_rows,columns=cols); stage.to_csv(out/'model_progression.csv',index=False)

    # City-specific full-model LOCO
    city=[]
    for pol in ['PM2.5','PM10']:
        for c,g in loco[(pol,'+ full meteorology')].groupby('City'):
            city.append([pol,c,*metrics(g.y,g.p).values()])
    pd.DataFrame(city,columns=['Pollutant','City','n','R2','RMSE','MAE','MBE','Pearson','CCC']).to_csv(out/'city_loco.csv',index=False)

    # Bootstrap uncertainty and delta R2
    rng=np.random.default_rng(42); br=[]
    for pol in ['PM2.5','PM10']:
        f=loco[(pol,'+ full meteorology')]; s=loco[(pol,'+ season/month')]; cities=sorted(f.City.unique())
        fb={c:f[f.City==c] for c in cities}; sb={c:s[s.City==c] for c in cities}; rv=[]; dv=[]
        for _ in range(bootstrap):
            sample=rng.choice(cities,len(cities),replace=True); yy=[]; pf=[]; ps=[]
            for c in sample: yy.extend(fb[c].y); pf.extend(fb[c].p); ps.extend(sb[c].p)
            a=r2_score(yy,pf); b=r2_score(yy,ps); rv.append(a); dv.append(a-b)
        br.append([pol,r2_score(f.y,f.p),*np.quantile(rv,[.025,.975]),r2_score(f.y,f.p)-r2_score(s.y,s.p),*np.quantile(dv,[.025,.975])])
    pd.DataFrame(br,columns=['Pollutant','R2','R2_CI_low','R2_CI_high','Delta_R2','Delta_CI_low','Delta_CI_high']).to_csv(out/'bootstrap_summary.csv',index=False)

    # Common calendar sensitivity
    cr=[]
    for pol in ['PM2.5','PM10']:
        x=d[d.Pollutant==pol].copy(); tr=x[x.Date<'2023-01-01']; te=x[x.Date>='2023-01-01']; common=sorted(set(tr.City)&set(te.City)); tr=tr[tr.City.isin(common)]; te=te[te.City.isin(common)]
        pp=LinearRegression().fit(tr[full],tr.SEPA_city_mean).predict(te[full]); cr.append([pol,len(common),len(tr),*metrics(te.SEPA_city_mean,pp).values()])
    pd.DataFrame(cr,columns=['Pollutant','Cities','Train_n','n','R2','RMSE','MAE','MBE','Pearson','CCC']).to_csv(out/'common_calendar.csv',index=False)

    # Exploratory environmental domains
    er=[]
    for pol in ['PM2.5','PM10']:
        x=d[d.Pollutant==pol].copy(); rr=[]
        for c,g in x.groupby('City'):
            hh=g[g.Season=='Heating'].Klimerko.mean(); nn=g[g.Season!='Heating'].Klimerko.mean()
            rr.append([c,g.Klimerko.mean(),hh-nn,g.T2m_mean_C.mean(),g.RH2m_mean_pct.mean(),g.Wind10m_mean_ms.mean(),g.Precipitation_sum_mm.mean()])
        desc=pd.DataFrame(rr,columns=['City','PM_mean','Seasonal_contrast','T_mean','RH_mean','Wind_mean','Precip_mean']); X=StandardScaler().fit_transform(desc.iloc[:,1:]); sil={}
        for k in range(2,min(6,len(desc))): sil[k]=silhouette_score(X,KMeans(n_clusters=k,n_init=50,random_state=42).fit_predict(X))
        best=max(sil,key=sil.get); km=KMeans(n_clusters=best,n_init=50,random_state=42).fit_predict(X); ward=AgglomerativeClustering(n_clusters=best,linkage='ward').fit_predict(X)
        er.append([pol,best,sil[best],adjusted_rand_score(km,ward)])
    pd.DataFrame(er,columns=['Pollutant','Best_k','Silhouette','ARI_KMeans_Ward']).to_csv(out/'environmental_domains.csv',index=False)
    return stage

if __name__=='__main__':
    ap=argparse.ArgumentParser(description='Reproduce the Klimerko-SEPA transferability analysis from analysis-ready inputs.')
    ap.add_argument('--paired',default='data/analysis/paired_primary.csv'); ap.add_argument('--meteo',default='data/analysis/era5_city_daily.csv'); ap.add_argument('--outdir',default='outputs/reproduced'); ap.add_argument('--bootstrap',type=int,default=2000)
    a=ap.parse_args(); run(a.paired,a.meteo,a.outdir,a.bootstrap)
