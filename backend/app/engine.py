from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from math import radians,sin,cos,asin,sqrt
from statistics import median
import numpy as np

# Screening thresholds used only as transparent analytical references.
# They are NOT a substitute for a regulatory classification.
LIMITS = {"ph_low":6.5,"ph_high":8.5,"do_min":5.0,"bod_max":3.0}

@dataclass
class TriageResult:
    severity:str; confidence:float; stress_score:float; health_score:float; label:str; rationale:list[str]

def robust_z(value:float,baseline:list[float])->float:
    if not baseline:return 0.0
    med=median(baseline); mad=median(abs(x-med) for x in baseline)
    return abs(value-med)/max(1.4826*mad,0.05)

def water_quality_stress(ph=None,do=None,bod=None,tds=None,cod=None):
    parts=[]
    if ph is not None: parts.append((np.clip(max(6.5-ph,ph-8.5)/1.5,0,1),.20,"pH outside 6.5–8.5"))
    if do is not None: parts.append((np.clip((5-do)/5,0,1),.28,"dissolved oxygen below 5 mg/L"))
    if bod is not None: parts.append((np.clip((bod-3)/27,0,1),.30,"BOD above 3 mg/L"))
    if tds is not None: parts.append((np.clip((tds-500)/1500,0,1),.10,"elevated TDS screening signal"))
    if cod is not None: parts.append((np.clip((cod-50)/100,0,1),.12,"elevated COD screening signal"))
    if not parts:return 0.0,[]
    w=sum(x[1] for x in parts); score=float(sum(v*wt for v,wt,_ in parts)/w)
    reasons=[reason for value,_,reason in sorted(parts,reverse=True) if value>=.15]
    return round(score,4),reasons

def triage(water:float,biodiversity:float,human:float,image:float,recurrence=.0,data_quality=1.0):
    vals=np.array([water,biodiversity,human,image],float)
    evidence=int(np.sum(vals>=.35))
    stress=float(np.clip(.62*water+.14*biodiversity+.12*human+.07*image+.05*recurrence,0,1))
    confidence=float(np.clip(.45+.10*evidence+.18*recurrence+.15*data_quality,0,.98))
    if stress>=.75: sev,label='CRITICAL','High-priority ecological signal'
    elif stress>=.55: sev,label='HIGH','Strong ecological stress signal'
    elif stress>=.30: sev,label='MODERATE','Emerging ecological stress signal'
    else: sev,label='LOW','No strong acute signal'
    reasons=[x for x,v in [('water chemistry',water),('biodiversity',biodiversity),('human observation',human),('visual evidence',image)] if v>=.35]
    if recurrence>=.5: reasons.append('signal has corroborating recurrence')
    return TriageResult(sev,round(confidence,3),round(stress,3),round((1-stress)*100,1),label,reasons)

def haversine_km(lat1,lon1,lat2,lon2):
    r=6371.; dlat=radians(lat2-lat1); dlon=radians(lon2-lon1)
    a=sin(dlat/2)**2+cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2*r*asin(sqrt(a))

def cluster_observations(observations,window_minutes=90,radius_km=2):
    clusters=[]
    for obs in sorted(observations,key=lambda x:x.observed_at):
        placed=False
        for cluster in clusters:
            ref=cluster[-1]; dt=abs((obs.observed_at-ref.observed_at).total_seconds())/60
            dist=haversine_km(obs.lat,obs.lon,ref.lat,ref.lon)
            if dt<=window_minutes and dist<=radius_km: cluster.append(obs); placed=True; break
        if not placed: clusters.append([obs])
    return [c for c in clusters if len(c)>=2]

def ewma(values,alpha=.35):
    if not values:return []
    out=[float(values[0])]
    for v in values[1:]:out.append(alpha*float(v)+(1-alpha)*out[-1])
    return out

def recovery_index(stress_series):
    if len(stress_series)<2:return 0.0
    baseline=float(np.median(stress_series[:max(1,len(stress_series)//4)])); peak=max(stress_series); latest=stress_series[-1]
    return round(float(np.clip((peak-latest)/max(peak-baseline,.05)*100,0,100)),1)
