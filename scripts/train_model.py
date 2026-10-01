"""Train the TraceIT reconstruction model from a CSV with normalized stress columns.

Expected columns:
ph,do_mg_l,bod_mg_l,tds_mg_l,cod_mg_l

This script is intentionally optional. The deployed demo trains from its seed
record so the app has zero setup requirements.
"""
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.ml import EcosystemAutoencoder

src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'data' / 'training.csv'
rows=[]
with src.open(newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        try:
            rows.append([float(r[k]) for k in ('ph','do_mg_l','bod_mg_l','tds_mg_l','cod_mg_l')])
        except (KeyError, TypeError, ValueError):
            continue

if len(rows) < 8:
    raise SystemExit(f'Need at least 8 usable rows; found {len(rows)}')
model=EcosystemAutoencoder().fit(rows)
print(f'Trained MLP reconstruction model on {len(rows)} rows.')
print('The current v5 app retrains its lightweight model at startup; this script is the research extension point for a persisted artifact.')
