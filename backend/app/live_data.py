"""Live public-context adapters. These are intentionally separate from the historical record."""
from __future__ import annotations
from datetime import datetime, timezone
import httpx
GBIF_URL="https://api.gbif.org/v1/occurrence/search"
OPEN_METEO_URL="https://api.open-meteo.com/v1/forecast"
async def fetch_gbif(lat:float,lon:float,radius_km:float=10.0,limit:int=20)->dict:
    params={"decimalLatitude":lat,"decimalLongitude":lon,"distance":radius_km*1000,"limit":limit,"hasCoordinate":"true"}
    async with httpx.AsyncClient(timeout=8.0) as client:
        response=await client.get(GBIF_URL,params=params); response.raise_for_status(); payload=response.json()
    records=[{"key":x.get("key"),"species":x.get("species") or x.get("scientificName"),"kingdom":x.get("kingdom"),"event_date":x.get("eventDate"),"basis":x.get("basisOfRecord")} for x in payload.get("results",[])]
    return {"source":"GBIF","retrieved_at":datetime.now(timezone.utc).isoformat(),"count":payload.get("count",0),"records":records}
async def fetch_weather(lat:float,lon:float)->dict:
    params={"latitude":lat,"longitude":lon,"current":"temperature_2m,precipitation,relative_humidity_2m,wind_speed_10m","hourly":"precipitation","forecast_days":2,"timezone":"auto"}
    async with httpx.AsyncClient(timeout=8.0) as client:
        response=await client.get(OPEN_METEO_URL,params=params); response.raise_for_status(); payload=response.json()
    return {"source":"Open-Meteo","retrieved_at":datetime.now(timezone.utc).isoformat(),"current":payload.get("current",{}),"hourly":payload.get("hourly",{})}

USGS_LATEST_URL='https://api.waterdata.usgs.gov/ogcapi/v1/collections/latest-continuous/items'
async def fetch_usgs_latest(limit:int=20, api_key:str|None=None)->dict:
    """Modern USGS Water Data OGC API. No legacy NWIS endpoint."""
    params={'f':'json','limit':min(limit,100)}
    if api_key: params['api_key']=api_key
    async with httpx.AsyncClient(timeout=12) as client:
        r=await client.get(USGS_LATEST_URL,params=params); r.raise_for_status(); payload=r.json()
    features=[]
    for f in payload.get('features',[]):
        p=f.get('properties',{}); features.append({'location':p.get('monitoring_location_name'),'location_id':p.get('monitoring_location_id'),'parameter_code':p.get('parameter_code'),'value':p.get('value'),'unit':p.get('unit_of_measure'),'time':p.get('time'),'state':p.get('state_name')})
    return {'source':'USGS Water Data API','retrieved_at':datetime.now(timezone.utc).isoformat(),'count':len(features),'records':features}
