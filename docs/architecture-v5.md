# TraceIT v5 — system architecture

TraceIT is intentionally **not an AI-first dashboard**. AI is one analytical layer in a source-first aquatic health system.

## Components

1. **Field kit** — repeatable site protocol: GPS, timestamp, pH, temperature, DO, conductivity/TDS, turbidity, photo and notes.
2. **Scientific record** — published measurements are immutable and carry provenance.
3. **Citizen science** — authenticated observations enter a candidate-signal layer and never mutate published measurements.
4. **Validation** — units, permitted ranges, missingness, duplicates and provenance are checked before analysis.
5. **Rules** — transparent screening thresholds and domain logic produce deterministic findings.
6. **Statistics** — descriptive statistics, EWMA, PCA and spatiotemporal clustering expose patterns before ML.
7. **ML** — a temporal Transformer autoencoder + Isolation Forest provides an independent anomaly signal. It is explicitly secondary to evidence.
8. **Live context** — USGS Water Data API, GBIF and Open-Meteo remain separate from historical measurements.
9. **Interoperability** — observations can be emitted as FHIR-like `Observation` resources.
10. **Action memory** — field checks, sampling, expert review and interventions are persisted and can be followed up.

## Data flow

`field/citizen/research/live -> validation -> provenance -> rules -> statistics -> ML -> explainable assessment -> action -> follow-up`

## Scientific boundary

The system does not claim to diagnose ecosystem health from a neural score. A score is accompanied by its source data, method, thresholds and caveats.
