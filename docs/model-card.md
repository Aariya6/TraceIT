# TraceIT v5 Neural Model Card

## Purpose
TraceIT uses neural reconstruction as one signal in an explainable aquatic anomaly-screening ensemble. It is **not** a regulatory classifier, medical model, or pollution-source attribution system.

## Architecture
- 3 common chemistry features for cross-dataset compatibility: pH, dissolved oxygen, BOD.
- RobustScaler.
- 3-layer Transformer encoder, 48-dimensional latent representation, 4 attention heads.
- Reconstruction head.
- Next-step forecasting head.
- Auxiliary domain-health head.
- IsolationForest branch.
- Transparent chemistry-stress branch using published screening thresholds.
- Ensemble: neural reconstruction + forecast error + isolation signal + domain signal.

## Why only three neural features?
The Man Sagar study has pH, DO and BOD in common with the national CPCB-derived benchmark. TDS and COD are retained in TraceIT's local domain model but are not falsely mapped to different national variables merely to make the neural model look larger.

## Data limitation
The bundled site-specific record has 16 observations (4 sites × 4 months). That is insufficient to claim a statistically validated deep-learning model. TraceIT therefore ships a training pipeline for the CPCB-derived 2012–2023 benchmark and keeps the bundled artifact explicitly in **research/demo screening mode** until trained on the larger benchmark.

## Reproducibility
1. `python scripts/download_cpcb_benchmark.py`
2. `python scripts/train_research_model.py`
3. The artifact is written to `backend/artifacts/traceit_neural.pt`.

Source benchmark repository: https://github.com/KunalLatkar/RiverWaterQualityDataset
The repository states that its data were gathered from CPCB's NWMP data portal and documents its preprocessing and thresholds.

## Safety / interpretation
A high score means the observed vector is unusual relative to the model's training distribution and/or violates transparent screening signals. It does not establish cause, legal responsibility, ecological diagnosis, or human-health risk.
