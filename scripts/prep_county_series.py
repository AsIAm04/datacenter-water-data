import pandas as pd, numpy as np, json
YEARS=[1985,1990,1995,2000,2005,2010,2015]
def s(d,c): 
    return pd.to_numeric(d[c],errors='coerce') if c in d.columns else pd.Series(np.nan,index=d.index)
def comb(d,prefixes,kind):
    parts=[s(d,f'{p}-{kind}') for p in prefixes]
    df=pd.concat(parts,axis=1)
    return df.sum(axis=1,min_count=1)
SECT={'ps':{'all':['PS']},'dom':{'all':['DO']},'irr':{'all':['IR']},
      'ind':{'all':['IN']},'min':{'all':['MI']}}
rows=[]; qc=[]
for y in YEARS:
    d=pd.read_parquet(f'/home/claude/wu/{y}/all_data_parquet_format/{y}-Revised-County.parquet')
    d=d.copy(); d['fips']=d['ST'].astype(str).str.zfill(2)+d['CO'].astype(str).str.zfill(3)
    th=['PF','PG','PN'] if y<=1995 else ['PO','PC']
    lv=['LS','LA'] if y<=1995 else ['LI','AQ']
    spec={'ps':['PS'],'dom':['DO'],'irr':(['IR'] if y<=1995 else ['IR','IC','IG']),'th':th,'ind':['IN'],'min':['MI'],'lv':lv}
    out=pd.DataFrame({'fips':d['fips'],'state':d['State'],'county':d['County Name'],'year':y})
    for k,p in spec.items():
        out[k+'_gw']=comb(d,p,'WGWFr'); out[k+'_sw']=comb(d,p,'WSWFr')
    gwc=[k+'_gw' for k in spec]; swc=[k+'_sw' for k in spec]
    out['all_missing']=out[gwc+swc].isna().all(axis=1)
    out['total_gw']=out[gwc].sum(axis=1,min_count=1); out['total_sw']=out[swc].sum(axis=1,min_count=1)
    rows.append(out)
    qc.append({'year':y,'n':len(out),'dup_fips':int(out.fips.duplicated().sum()),'all_missing':int(out.all_missing.sum()),
               'nat_total':round(float((out.total_gw.fillna(0)+out.total_sw.fillna(0)).sum())),
               **{k:round(float((out[k+'_gw'].fillna(0)+out[k+'_sw'].fillna(0)).sum())) for k in spec}})
al=pd.concat(rows,ignore_index=True)
print(pd.DataFrame(qc).to_string())
al.drop(columns=['all_missing']).round(3).to_csv('/home/claude/out/county_water_raw.csv',index=False)
al.to_pickle('/home/claude/out/al.pkl')
