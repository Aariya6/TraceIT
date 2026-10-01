import os
from pathlib import Path
TEST_DB=Path(__file__).resolve().parent / "test_traceit.db"
if TEST_DB.exists(): TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["AUTH_SECRET"] = 'test-secret-0123456789-0123456789-0123'
from fastapi.testclient import TestClient
from app.main import app
import uuid

def signup(client, email=None):
    email=email or f'tester-{uuid.uuid4().hex[:10]}@example.com'
    r=client.post('/api/auth/signup',json={'name':'Test Researcher','email':email,'password':'strongpass123'})
    assert r.status_code==200
    return r.json()['token']

def test_health_and_real_record():
    with TestClient(app) as client:
        h=client.get('/health'); assert h.status_code==200; assert h.json()['version']=='5.0.0'
        rivers=client.get('/api/rivers'); assert rivers.status_code==200; assert rivers.json()[0]['name']=='Man Sagar Lake'
        record=client.get('/api/rivers/1/record'); assert record.status_code==200
        body=record.json(); assert body['metrics']['observation_count']>=16; assert body['metrics']['site_count']==4
        assert body['timeline'][-1]['bod_mg_l'] > 3
        assert body['finding']['title'].startswith('Persistent oxygen')

def test_login_rejects_bad_password_and_accepts_good_one():
    with TestClient(app) as client:
        email=f"login-{uuid.uuid4().hex[:8]}@example.com"
        signup(client,email)
        bad=client.post('/api/auth/login',json={'email':email,'password':'wrongpass'})
        assert bad.status_code==401
        good=client.post('/api/auth/login',json={'email':email,'password':'strongpass123'})
        assert good.status_code==200 and good.json()['token']

def test_auth_and_bookmark():
    with TestClient(app) as client:
        token=signup(client)
        me=client.get('/api/auth/me',headers={'Authorization':f'Bearer {token}'})
        assert me.status_code==200 and me.json()['user']['name']=='Test Researcher'
        save=client.post('/api/rivers/1/bookmark',headers={'Authorization':f'Bearer {token}'})
        assert save.status_code==200 and save.json()['saved'] is True
        saved=client.get('/api/me/bookmarks',headers={'Authorization':f'Bearer {token}'})
        assert saved.json()['river_ids']==[1]

def test_triage_endpoint():
    with TestClient(app) as client:
        r=client.post('/api/triage',json={'water_stress':.9,'biodiversity_stress':.8,'human_signal':.75,'image_signal':.85,'recurrence':.8})
        assert r.status_code==200 and r.json()['severity']=='CRITICAL'

def test_observation_requires_auth_and_writes():
    with TestClient(app) as client:
        payload={'water_body_id':1,'observed_at':'2026-10-01T12:00:00Z','source':'field-note','site_code':'CITIZEN','note':'New surface change reported','lat':26.951,'lon':75.851,'ph':8.9,'do_mg_l':2.5,'bod_mg_l':18.0,'tds_mg_l':1600,'cod_mg_l':90,'biodiversity_signal':.68,'human_signal':.63,'image_signal':.67,'quality_score':.9}
        denied=client.post('/api/observations',json=payload); assert denied.status_code==401
        token=signup(client, f'writer-{uuid.uuid4().hex[:8]}@example.com')
        r=client.post('/api/observations',json=payload,headers={'Authorization':f'Bearer {token}'})
        assert r.status_code==200 and r.json()['observation_id']>0
        assert r.json()['triage']['severity'] in {'HIGH','CRITICAL'}

def test_data_source_catalog_and_neural_endpoint():
    with TestClient(app) as client:
        sources=client.get('/api/data-sources'); assert sources.status_code==200
        assert any(x['name']=='GBIF' for x in sources.json()['live'])
        neural=client.get('/api/neural/anomaly?ph=8.7&do=3.8&bod=20.8&tds=1592&cod=91.7')
        assert neural.status_code==200 and 'Transformer' in neural.json()['model'] and 0 <= neural.json()['ensemble_score'] <= 1

def test_component_endpoints():
    with TestClient(app) as client:
        p=client.get('/api/water-bodies/1/protocol'); assert p.status_code==200; assert len(p.json()['required_measurements'])>=6
        f=client.get('/api/fhir/Observation/1'); assert f.status_code==200; assert f.json()['resourceType']=='Observation'; assert len(f.json()['component'])>=3
        s=client.get('/api/data-sources'); assert s.status_code==200; assert any(x['name']=='USGS Water Data API' for x in s.json()['live'])
