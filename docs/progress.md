# TraceIT v5 progress log

## v5 — component architecture

- Replaced AI-centric dashboard framing with a source-first aquatic health system.
- Added field protocol persistence.
- Added intervention/action memory.
- Added data-source registry.
- Added observation validation + provenance.
- Added FHIR Observation export endpoint.
- Added PCA endpoint and explicit statistical layer.
- Added live USGS/GBIF/Open-Meteo adapters.
- Preserved published Man Sagar observations as immutable research seed data.
- Added authenticated citizen observation workflow.
- Added persistent users/bookmarks.
- Added actual SQLite development database and PostgreSQL production path.
- Added migration for new component tables.
- Reworked main website around six system components instead of generic SaaS sections.
- Added subtle continuous water-field motion.
- Reworked dashboard typography, density and analytical hierarchy.
- Added real SVG trajectory graph, site comparison, field-location visualization and PCA visualization.
- Verified backend suite: 11 tests passing.

## Known scientific limitation

The bundled Man Sagar record is small. The neural model is therefore a research/demo anomaly component, not a validated national classifier. The repository includes a separate CPCB-derived benchmark training path for future held-out evaluation.
