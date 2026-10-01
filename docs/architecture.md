# TraceIT v5 Architecture

## Product thesis

TraceIT treats an aquatic ecosystem as a longitudinal health record: measured history, citizen observations, derived analytics and live public context remain separate but queryable in one system.

## Stack

- Frontend: zero-build HTML, CSS and ES modules; no framework dependency for the public prototype.
- Backend: Python + FastAPI.
- Data layer: SQLAlchemy; SQLite locally; PostgreSQL/Supabase for deployment.
- Auth: scrypt password hashing + signed HS256 bearer sessions.
- Analytics: explainable stress index, EWMA smoothing, spatiotemporal clustering, recovery logic and an MLP reconstruction anomaly model.
- Live context: GBIF biodiversity occurrences + Open-Meteo weather.
- Standards direction: HL7 FHIR `Observation` for interoperability.

## Data layers

### Published record

The working Man Sagar record preserves the four-site Nov 2019–Feb 2020 observations in the repository. These are historical measurements and are never labelled as current.

### Derived layer

Stress and neural anomaly values are calculated from the published measurements and explicitly labelled as derived.

### Citizen layer

Authenticated users can submit observations. These are stored separately from the published study and enter the candidate-signal/triage layer.

### Live layer

GBIF and Open-Meteo are queried independently. Their current values never rewrite the historical record.

## Account logic

1. User signs up with name, email and password.
2. Password is stored as a salted scrypt hash; plaintext is never stored.
3. API returns a signed expiring bearer token.
4. Dashboard uses the token for account-specific actions.
5. Users can save an ecosystem record and submit citizen observations.
6. Public research records remain readable without an account.

## Decision logic

### Measured stress

The working index uses pH, dissolved oxygen, BOD, TDS and COD penalties. It is a prototype analytical layer, not a regulatory classification.

### Neural anomaly

An MLP reconstruction model is trained on the available study feature vectors. Reconstruction error becomes an anomaly signal; it is shown as model output rather than truth.

### Spatiotemporal corroboration

Citizen observations can be clustered when they occur within a short temporal window and geographic radius. Corroboration increases triage confidence; it does not prove causality.

## Production evolution

1. Connect OneAquaHealth datasets/API endpoints.
2. Map environmental measurements to FHIR `Observation`.
3. Add PostGIS geometry and watershed/flow topology.
4. Add domain-specific thresholds with provenance.
5. Add expert review and provenance signatures.
6. Train/calibrate models on labelled multi-year incident/recovery data.
7. Add role-based access for researchers, citizen moderators and administrators.
