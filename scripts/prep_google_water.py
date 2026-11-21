"""Google FY2024 (2025 environmental report, p.110-111) US water use by data center location, million gallons.
Withdrawal, discharge, consumption are Google-reported operational (direct) figures; no indirect/electricity water.
Site->county mapping is by place name (inferred) with atlas cross-check where possible; see county_basis."""
import pandas as pd
R=[ # site, withdrawal, discharge, consumption, fips(list), county_basis
('Ashburn, VA',59.5,3.5,56.0,['51107'],'place name (Ashburn is in Loudoun County)'),
('Berkeley County, SC',853.8,77.3,776.5,['45015'],'named county'),
('Bristow, VA',105.7,21.3,84.4,['51153'],'place name (Bristow is in Prince William County)'),
('Council Bluffs, IA',1410.3,400.1,1010.2,['19155'],'place name (Pottawattamie County)'),
('The Dalles, OR',461.1,99.7,361.4,['41065'],'place name (Wasco County)'),
('Douglas County, GA',444.1,77.2,366.9,['13097'],'named county'),
('Henderson, NV',359.9,152.5,207.4,['32003'],'place name (Clark County)'),
('Jackson County, AL',201.6,18.8,182.8,['01071'],'named county'),
('Lancaster, OH',207.4,106.3,101.1,['39045'],'place name; atlas shows Google buildings in Fairfield County'),
('Leesburg, VA',246.7,55.1,191.6,['51107'],'place name (Loudoun County)'),
('Lenoir, NC',351.7,23.9,327.8,['37027'],'place name; atlas names Google Lenoir in Caldwell County'),
('Lockbourne, OH',177.3,34.0,143.3,['39049'],'atlas campus "Google Lockbourne, OH" is in Franklin County'),
('Mayes County, OK',1108.3,275.1,833.2,['40097'],'named county'),
('Midlothian, TX',221.0,38.7,182.3,['48139'],'place name (Ellis County); not checked in atlas'),
('Montgomery County, TN',387.9,66.1,321.8,['47125'],'named county'),
('New Albany, OH',405.3,52.6,352.7,['39049','39089'],'STRADDLES: atlas campus spans Franklin and Licking counties; volume not split'),
('Omaha, NE',44.3,12.2,32.1,['31055'],'place name (Douglas County)'),
('Papillion, NE',532.3,115.4,416.9,['31153'],'place name (Sarpy County)'),
('Pflugerville, TX',0.1,0.1,0.01,['48453'],'place name (Travis County)'),
('Phoenix, AZ',0.2,0.2,0.03,['04013'],'place name (Maricopa County)'),
('Sterling, VA',201.2,43.0,158.2,['51107'],'place name (Loudoun County)'),
('Storey County, NV',14.9,13.4,1.5,['32029'],'named county'),
('Wilmer, TX',1.9,1.7,0.2,['48113'],'place name (Dallas County)'),
]
rows=[dict(site=s,year=2024,withdrawal_mgal=w,discharge_mgal=d,consumption_mgal=c,county_fips='|'.join(f),county_basis=b,straddles=len(f)>1,operator='Google',water_type='direct operational (data center sites only)',source='Google 2025 Environmental Report (FY2024), water use by data center location, assured by third party') for s,w,d,c,f,b in R]
df=pd.DataFrame(rows); df.to_csv('data/datacenters/google_fy2024_us_site_water.csv',index=False)
chk=(df.withdrawal_mgal-df.discharge_mgal-df.consumption_mgal).abs()
print('sites',len(df),'| withdrawal-discharge-consumption max gap',round(chk.max(),2),'| US sum withdrawal',round(df.withdrawal_mgal.sum(),1),'consumption',round(df.consumption_mgal.sum(),1))
print('Google total all sites incl. non-US and Other: 9,866 withdrawal (report); US named sites cover',round(100*df.withdrawal_mgal.sum()/9866),'%')
# per county (straddler counted once at site level; shown in both counties' detail, never added)
g=df[~df.straddles].groupby('county_fips')[['withdrawal_mgal','consumption_mgal']].sum()
print(g.sort_values('withdrawal_mgal',ascending=False).head(8).round(1))
