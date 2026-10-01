"""Train TraceIT's neural anomaly model.

Preferred path: supply the CPCB-derived benchmark downloaded by
scripts/download_cpcb_benchmark.py. The local Man Sagar record is retained as
an evaluation/site-specific context, not silently treated as a national corpus.
"""
from pathlib import Path
import csv,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.ml import NeuralAnomalyEngine
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'data/external/cpcb_india_2012_2023.csv'
rows=[]
with p.open(encoding='utf-8',newline='') as f:
    for r in csv.DictReader(f):
        def pair(a,b=None):
            try:
                x=float(r[a]); y=float(r[b]) if b and r.get(b) not in ('',None) else x; return (x+y)/2
            except: return None
        v=[pair('pH Min','pH Max'),pair('Dissolved Oxygen Min','Dissolved Oxygen Max'),pair('BOD Min','BOD Max')]
        if all(x is not None for x in v): rows.append(v)
if len(rows)<100: raise SystemExit(f'Need >=100 benchmark rows; found {len(rows)}')
model=NeuralAnomalyEngine().fit(rows,epochs=300)
model.save(ROOT/'backend/artifacts/traceit_neural.pt')
print(f'trained {len(rows)} benchmark rows; artifact written')
