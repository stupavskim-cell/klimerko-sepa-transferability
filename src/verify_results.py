from pathlib import Path
import pandas as pd, numpy as np, sys
from sklearn.metrics import r2_score, mean_squared_error
root=Path(__file__).resolve().parents[1]
out=root/'outputs'/'reproduced'
prog=pd.read_csv(out/'model_progression.csv')
checks={
 ('PM2.5','LOCO','+ full meteorology'):0.6959679216,
 ('PM10','LOCO','+ full meteorology'):0.5653857364,
}
ok=True
for key,expected in checks.items():
    p,v,m=key; got=prog[(prog.Pollutant==p)&(prog.Validation==v)&(prog.Model==m)].R2.iloc[0]
    print(key,'R2=',got,'expected=',expected)
    ok &= abs(got-expected)<5e-6
# Archived exact GBR LOCO predictions
for pol,file,expected in [('PM2.5','pm25_loco_gbr_predictions.csv',0.7067113855),('PM10','pm10_loco_gbr_predictions.csv',0.580)]:
    d=pd.read_csv(root/'data'/'analysis'/file); got=r2_score(d.SEPA,d.Pred); print(pol,'GBR LOCO R2=',got); ok &= abs(got-expected)<0.002
if not ok: sys.exit('Verification failed.')
print('Verification passed.')
