from datetime import datetime, timedelta
from types import SimpleNamespace
from app.engine import triage, cluster_observations, recovery_index, robust_z

def test_triage_scales_and_explains():
    low = triage(.1,.1,.1,.1)
    high = triage(.9,.9,.8,.9,recurrence=.8)
    assert low.severity == "LOW"
    assert high.severity == "CRITICAL"
    assert high.confidence > low.confidence
    assert 0 <= high.health_score <= 100

def test_cluster_spatiotemporal():
    t = datetime(2026,1,1,10,0)
    a = SimpleNamespace(observed_at=t, lat=26.95, lon=75.85)
    b = SimpleNamespace(observed_at=t+timedelta(minutes=20), lat=26.951, lon=75.851)
    c = SimpleNamespace(observed_at=t+timedelta(hours=5), lat=26.99, lon=75.90)
    clusters = cluster_observations([a,b,c])
    assert len(clusters) == 1
    assert len(clusters[0]) == 2

def test_recovery_improves_when_stress_falls():
    assert recovery_index([.2,.8,.7,.4,.25]) > recovery_index([.2,.8,.9,.95,.92])

def test_robust_z_handles_flat_baseline():
    assert robust_z(.5,[.5,.5,.5]) == 0
