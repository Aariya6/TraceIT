# TraceIT v5 — Data & ML

## Data hierarchy

TraceIT keeps evidence tiers separate:

1. **Published Man Sagar measurements** — the seeded longitudinal record: 16 measurements from four sites, November 2019–February 2020.
2. **Later Man Sagar research** — 2021–2023 study summary used as contextual corroboration, not merged into the older time series.
3. **Citizen observations** — new, user-submitted signals that enter the triage layer and are clearly labelled as observations.
4. **GBIF** — live biodiversity occurrence context.
5. **Open-Meteo** — live weather/precipitation context.
6. **India OGD / CPCB datasets** — government water-quality sources and broader model-development benchmarks.
7. **GitHub/Kaggle benchmarks** — optional generalisation experiments; never treated as authoritative current measurements.

## Derived water-stress model

The prototype derives a transparent stress index from measured values:

```text
pH deviation        18%
DO below threshold  22%
BOD excess          30%
TDS context         15%
COD context         15%
                    ───
                    100%
```

The weights are an explicit prototype design choice, not a regulatory water-quality index. The UI therefore calls it a **derived stress index** rather than an official WQI.

## Neural component

The model is trained on the actual five-variable Man Sagar study vectors:

```text
[pH, DO, BOD, TDS, COD]
             │
       StandardScaler
             │
      MLP reconstruction
       5 → 8 → 4 → 8 → 5
             │
      reconstruction error
             │
        anomaly score
```

This is deliberately small enough for free hosting. It is a research signal, not a clinical or regulatory classifier.

## Research extension

With a larger labelled dataset:

```text
CPCB station history
       +
Man Sagar research
       +
Citizen observations
       +
GBIF biodiversity
       +
Weather
       ↓
Temporal model
       +
Spatial graph
       +
FHIR Observation layer
       ↓
Explainable ecosystem event graph
```

The 2025 Man Sagar study itself used PCA, factor analysis and cluster analysis, providing a useful methodological bridge for the next version.
