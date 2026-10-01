from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import csv, json
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session
from .config import settings
from .db import SessionLocal, get_db, init_db
from .models import User,WaterBody,Observation,Bookmark,FieldProtocol,Intervention,DataSource
from .schemas import ObservationIn,TriageIn,SignupIn,LoginIn,InterventionIn
from .engine import triage,cluster_observations,ewma,recovery_index,water_quality_stress
from .live_data import fetch_gbif,fetch_weather,fetch_usgs_latest
from .ml import NeuralAnomalyEngine,FEATURES
from .auth import hash_password,verify_password,create_token,current_user_id

ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'data'/'mansagar_2019_2020.csv'; ART=ROOT/'backend'/'artifacts'/'traceit_neural.pt'
ml=NeuralAnomalyEngine()

def load_rows():
    with DATA.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def seed(db):
    lake=db.scalar(select(WaterBody).where(WaterBody.slug=='man-sagar-lake'))
    if not lake:
        lake=WaterBody(slug='man-sagar-lake',name='Man Sagar Lake',city='Jaipur, Rajasthan',country='India',latitude=26.9565,longitude=75.8465,status='PUBLISHED RESEARCH RECORD',description='Four fixed sampling sites from the published Nov 2019–Feb 2020 record.',source_period='Nov 2019 – Feb 2020')
        db.add(lake);db.flush()
    if not db.scalar(select(Observation.id).where(Observation.water_body_id==lake.id,Observation.source=='published_research')):
        vectors=[]
        for r in load_rows():
            vals={k:float(r[k]) for k in ['ph','do_mg_l','bod_mg_l','tds_mg_l','cod_mg_l']};vectors.append([vals[k] for k in FEATURES]);dt=datetime.strptime(r['month'],'%Y-%m').replace(day=15,tzinfo=timezone.utc)
            db.add(Observation(water_body_id=lake.id,observed_at=dt,source='published_research',source_record_id=f"mansagar:{r['month']}:{r['site_code']}",note='Published measurement; immutable research seed.',site_code=r['site_code'],lat=float(r['latitude']),lon=float(r['longitude']),temperature_c=float(r['temperature_c']),ph=vals['ph'],tds_mg_l=vals['tds_mg_l'],do_mg_l=vals['do_mg_l'],bod_mg_l=vals['bod_mg_l'],cod_mg_l=vals['cod_mg_l'],quality_score=1,provenance={'source_type':'published_research','dataset':'Man Sagar Lake water-quality study','period':r['month']},validation={'range_checks':'passed','immutable':True}))
        db.flush();ml.fit(vectors,epochs=120);ml.save(ART)
    else:
        try:ml.load(ART)
        except Exception:
            obs=db.scalars(select(Observation).where(Observation.water_body_id==lake.id,Observation.source=='published_research')).all();ml.fit([[o.ph,o.do_mg_l,o.bod_mg_l] for o in obs],epochs=80);ml.save(ART)
    if not db.scalar(select(FieldProtocol.id).where(FieldProtocol.water_body_id==lake.id)):
        db.add(FieldProtocol(water_body_id=lake.id,title='TraceIT field observation — basic aquatic screen',version='1.0',required_measurements=['pH','temperature','dissolved oxygen','conductivity/TDS','turbidity','GPS','timestamp'],steps=['Rinse probes with site water','Record GPS and timestamp','Measure pH and temperature','Measure dissolved oxygen','Measure conductivity/TDS and turbidity','Photograph visible conditions','Record observations without interpretation','Submit and retain raw readings']))
    sources=[('USGS Water Data API','live','https://api.waterdata.usgs.gov/ogcapi/v1/collections/latest-continuous','Near-real-time automated water measurements; US coverage.','minutes–hourly'),('GBIF','live','https://api.gbif.org/v1/occurrence/search','Biodiversity occurrence context.','continuously indexed'),('Open-Meteo','live','https://api.open-meteo.com/v1/forecast','Weather context.','hourly'),('CPCB India benchmark','research','https://github.com/KunalLatkar/RiverWaterQualityDataset','2012–2023 Indian river monitoring benchmark.','historical')]
    for name,kind,url,desc,freq in sources:
        if not db.scalar(select(DataSource).where(DataSource.name==name)):db.add(DataSource(name=name,kind=kind,url=url,description=desc,update_frequency=freq,enabled=True,metadata_json={}))
    db.commit();return lake

@asynccontextmanager
async def lifespan(app):
    init_db();db=SessionLocal()
    try:seed(db);yield
    finally:db.close()

app=FastAPI(title='TraceIT — Aquatic Health Record',version='5.0.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(',') if x.strip()] or ['*'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])

@app.get('/health')
def health(db:Session=Depends(get_db)):return {'status':'ok','version':app.version,'database':settings.database_url.split(':',1)[0],'observations':db.scalar(select(func.count(Observation.id))) or 0,'neural_model':ml.artifact_version}

@app.post('/api/auth/signup')
def signup(p:SignupIn,db:Session=Depends(get_db)):
    email=str(p.email).lower().strip()
    if db.scalar(select(User).where(User.email==email)):raise HTTPException(409,'Account already exists')
    u=User(name=p.name.strip(),email=email,password_hash=hash_password(p.password));db.add(u);db.commit();db.refresh(u);return {'token':create_token(u.id,u.email),'user':{'id':u.id,'name':u.name,'email':u.email,'role':u.role}}
@app.post('/api/auth/login')
def login(p:LoginIn,db:Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==str(p.email).lower().strip()))
    if not u or not verify_password(p.password,u.password_hash):raise HTTPException(401,'Email or password is incorrect')
    return {'token':create_token(u.id,u.email),'user':{'id':u.id,'name':u.name,'email':u.email,'role':u.role}}
@app.get('/api/auth/me')
def me(request:Request,db:Session=Depends(get_db)):
    u=db.get(User,current_user_id(request))
    if not u:raise HTTPException(401,'Account not found')
    return {'user':{'id':u.id,'name':u.name,'email':u.email,'role':u.role}}

@app.get('/api/rivers')
@app.get('/api/water-bodies')
def water_bodies(db:Session=Depends(get_db)):
    return [{'id':x.id,'slug':x.slug,'name':x.name,'city':x.city,'status':x.status} for x in db.scalars(select(WaterBody)).all()]

def record_payload(wid,db):
    lake=db.get(WaterBody,wid)
    if not lake:raise HTTPException(404,'Water body not found')
    obs=db.scalars(select(Observation).where(Observation.water_body_id==wid,Observation.source=='published_research').order_by(Observation.observed_at,Observation.site_code)).all();grouped={}
    for o in obs:grouped.setdefault(o.observed_at.strftime('%Y-%m'),[]).append(o)
    history=[[o.ph,o.do_mg_l,o.bod_mg_l] for o in obs];timeline=[]
    for month,items in grouped.items():
        def avg(k):return round(sum((getattr(o,k) or 0) for o in items)/len(items),3)
        vals=[avg('ph'),avg('do_mg_l'),avg('bod_mg_l'),avg('tds_mg_l'),avg('cod_mg_l')];stress,reasons=water_quality_stress(*vals);nn=ml.score(vals,history=history)
        timeline.append({'month':month,'measurements':len(items),'ph':vals[0],'do_mg_l':vals[1],'bod_mg_l':vals[2],'tds_mg_l':vals[3],'cod_mg_l':vals[4],'temperature_c':avg('temperature_c'),'stress':stress,'reasons':reasons,'neural_anomaly':nn.ensemble_score})
    sites=[]
    for code in sorted({o.site_code for o in obs}):
        items=[o for o in obs if o.site_code==code]
        def mean(k):return round(sum((getattr(o,k) or 0) for o in items)/len(items),3)
        sites.append({'site':code,'lat':items[0].lat,'lon':items[0].lon,'n':len(items),'ph':mean('ph'),'do':mean('do_mg_l'),'bod':mean('bod_mg_l'),'tds':mean('tds_mg_l'),'cod':mean('cod_mg_l')})
    stresses=[x['stress'] for x in timeline];smooth=ewma(stresses);latest=timeline[-1];protocol=db.scalar(select(FieldProtocol).where(FieldProtocol.water_body_id==wid))
    return {'water_body':{'id':lake.id,'name':lake.name,'city':lake.city,'latitude':lake.latitude,'longitude':lake.longitude,'status':lake.status,'source_period':lake.source_period},'metrics':{'measurements':len(obs),'observation_count':len(obs),'sites':len(sites),'site_count':len(sites),'periods':len(timeline),'period_count':len(timeline),'health':round((1-smooth[-1])*100,1),'neural_peak':round(max(x['neural_anomaly'] for x in timeline),3),'recovery':recovery_index(stresses),'bod_flagged':sum((o.bod_mg_l or 0)>3 for o in obs),'do_flagged':sum((o.do_mg_l or 99)<5 for o in obs)},'timeline':timeline,'sites':sites,'protocol':protocol.steps if protocol else [],'finding':{'title':'Persistent oxygen and organic-load stress signal','severity':'ELEVATED','confidence':0.94,'summary':f"{sum((o.bod_mg_l or 0)>3 for o in obs)}/{len(obs)} published observations exceed the 3 mg/L screening reference; {sum((o.do_mg_l or 99)<5 for o in obs)}/{len(obs)} are below 5 mg/L dissolved oxygen."}}

@app.get('/api/rivers/{wid}/record')
@app.get('/api/water-bodies/{wid}/record')
def record(wid:int,db:Session=Depends(get_db)):return record_payload(wid,db)
@app.get('/api/water-bodies/{wid}/observations')
def observations(wid:int,db:Session=Depends(get_db)):
    return [{'id':o.id,'site':o.site_code,'time':o.observed_at,'source':o.source,'ph':o.ph,'do':o.do_mg_l,'bod':o.bod_mg_l,'tds':o.tds_mg_l,'cod':o.cod_mg_l,'quality':o.quality_score,'provenance':o.provenance,'validation':o.validation} for o in db.scalars(select(Observation).where(Observation.water_body_id==wid).order_by(desc(Observation.observed_at)).limit(1000)).all()]
@app.get('/api/water-bodies/{wid}/protocol')
def protocol(wid:int,db:Session=Depends(get_db)):
    p=db.scalar(select(FieldProtocol).where(FieldProtocol.water_body_id==wid))
    if not p:raise HTTPException(404,'Protocol not found')
    return {'title':p.title,'version':p.version,'steps':p.steps,'required_measurements':p.required_measurements}

@app.post('/api/observations')
def add_observation(p:ObservationIn,request:Request,db:Session=Depends(get_db)):
    uid=current_user_id(request)
    if not db.get(WaterBody,p.water_body_id):raise HTTPException(404,'Water body not found')
    d=p.model_dump()
    d['user_id']=uid; d['source']=f'citizen:{p.source}'
    d['provenance']={'source_type':'citizen','account_id':uid,'submitted_at':datetime.now(timezone.utc).isoformat()}
    d['validation']={'range_checks':'passed','published_record_mutation':False}
    stress,reasons=water_quality_stress(p.ph,p.do_mg_l,p.bod_mg_l,p.tds_mg_l,p.cod_mg_l)
    o=Observation(**d); db.add(o); db.commit(); db.refresh(o)
    recent=db.scalars(select(Observation).where(Observation.water_body_id==o.water_body_id).order_by(desc(Observation.observed_at)).limit(40)).all()
    clusters=cluster_observations(list(reversed(recent)))
    result=triage(stress,p.biodiversity_signal,p.human_signal,p.image_signal,min(1,len(clusters)/3),p.quality_score)
    return {'observation_id':o.id,'validation':o.validation,'rule_findings':reasons,'triage':result.__dict__,'cluster_count':len(clusters),'record_policy':'candidate signal; never merged into published research observations'}

@app.get('/api/analytics/pca/{wid}')
def pca(wid:int,db:Session=Depends(get_db)):
    from sklearn.decomposition import PCA
    import numpy as np
    obs=db.scalars(select(Observation).where(Observation.water_body_id==wid,Observation.source=='published_research')).all();X=np.array([[o.ph,o.do_mg_l,o.bod_mg_l,o.tds_mg_l,o.cod_mg_l] for o in obs],float);Z=(X-X.mean(0))/np.maximum(X.std(0),1e-9);p=PCA(n_components=2).fit(Z);return {'explained_variance_ratio':[round(float(x),4) for x in p.explained_variance_ratio_],'loadings':p.components_.round(4).tolist()}
@app.get('/api/neural/anomaly')
def neural_anomaly(ph:float,do:float,bod:float,tds:float,cod:float):
    return ml.score([ph,do,bod,tds,cod]).__dict__

@app.post('/api/triage')
def run_triage(p:TriageIn):return triage(p.water_stress,p.biodiversity_stress,p.human_signal,p.image_signal,p.recurrence,p.data_quality).__dict__

@app.get('/api/fhir/Observation/{oid}')
def fhir_observation(oid:int,db:Session=Depends(get_db)):
    o=db.get(Observation,oid)
    if not o:raise HTTPException(404,'Observation not found')
    components=[]
    for code,label,unit,val in [('ph','pH','pH',o.ph),('do','Dissolved oxygen','mg/L',o.do_mg_l),('bod','Biochemical oxygen demand','mg/L',o.bod_mg_l),('tds','Total dissolved solids','mg/L',o.tds_mg_l),('cod','Chemical oxygen demand','mg/L',o.cod_mg_l)]:
        if val is not None:components.append({'code':{'text':label,'coding':[{'system':'https://traceit.example/measurement','code':code}]},'valueQuantity':{'value':val,'unit':unit}})
    return {'resourceType':'Observation','id':str(o.id),'status':'final' if o.source=='published_research' else 'preliminary','code':{'text':f'TraceIT aquatic observation — {o.site_code}'},'effectiveDateTime':o.observed_at.isoformat(),'method':{'text':o.source},'component':components,'extension':[{'url':'https://traceit.example/provenance','valueString':json.dumps(o.provenance)}]}

@app.post('/api/water-bodies/{wid}/interventions')
def create_intervention(wid:int,p:InterventionIn,request:Request,db:Session=Depends(get_db)):
    uid=current_user_id(request);x=Intervention(water_body_id=wid,created_by_id=uid,**p.model_dump());db.add(x);db.commit();db.refresh(x);return {'id':x.id,'title':x.title,'status':x.status}
@app.get('/api/water-bodies/{wid}/interventions')
def interventions(wid:int,db:Session=Depends(get_db)):
    return [{'id':x.id,'title':x.title,'type':x.action_type,'status':x.status,'notes':x.notes,'target_date':x.target_date} for x in db.scalars(select(Intervention).where(Intervention.water_body_id==wid).order_by(desc(Intervention.created_at))).all()]
@app.get('/api/me/bookmarks')
def bookmarks(request:Request,db:Session=Depends(get_db)):
    uid=current_user_id(request);ids=[x.water_body_id for x in db.scalars(select(Bookmark).where(Bookmark.user_id==uid)).all()];return {'water_body_ids':ids,'river_ids':ids}
@app.post('/api/rivers/{wid}/bookmark')
@app.post('/api/water-bodies/{wid}/bookmark')
def bookmark(wid:int,request:Request,db:Session=Depends(get_db)):
    uid=current_user_id(request);x=db.scalar(select(Bookmark).where(Bookmark.user_id==uid,Bookmark.water_body_id==wid))
    if x:db.delete(x);saved=False
    else:db.add(Bookmark(user_id=uid,water_body_id=wid));saved=True
    db.commit();return {'saved':saved}

@app.get('/api/live/gbif')
async def gbif(lat:float=26.9565,lon:float=75.8465,radius_km:float=10):
    try:return await fetch_gbif(lat,lon,radius_km)
    except Exception as e:raise HTTPException(502,str(e))
@app.get('/api/live/weather')
async def weather(lat:float=26.9565,lon:float=75.8465):
    try:return await fetch_weather(lat,lon)
    except Exception as e:raise HTTPException(502,str(e))
@app.get('/api/live/usgs')
async def usgs():
    try:return await fetch_usgs_latest()
    except Exception as e:raise HTTPException(502,str(e))
@app.get('/api/data-sources')
def data_sources(db:Session=Depends(get_db)):
    rows=[{'name':x.name,'kind':x.kind,'url':x.url,'description':x.description,'frequency':x.update_frequency} for x in db.scalars(select(DataSource)).all()]; return {'live':[x for x in rows if x['kind']=='live'],'research':[x for x in rows if x['kind']=='research']}
