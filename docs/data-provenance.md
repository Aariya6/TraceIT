# TraceIT data provenance

## Primary record
Sharma, S. & Choudhary, M.P. (2021), *Assessment of Water Quality Parameters of Man Sagar Lake Jaipur, Rajasthan, India*.

Four fixed sampling spots, Nov 2019–Feb 2020. TraceIT preserves the measurements supplied in `data/mansagar_2019_2020.csv` and stores a provenance object for every seeded observation.

Source: https://www.researchgate.net/publication/352402146_Assessment_of_Water_Quality_Parameters_of_Man_Sagar_Lake_Jaipur_Rajasthan_India

## Later context study
Anamika et al. (2025), *Assessment of water quality using multivariate statistical techniques: Case study of the Man Sagar Lake, Jaipur, Rajasthan, India*.

The paper reports 576 samples over 2021–2023 from four fixed sites and uses multivariate methods including PCA, factor analysis and Ward clustering.

Source: https://ijzab.com/announce/download/653

## Live context
- USGS Water Data API — modern OGC API, latest continuous measurements: https://api.waterdata.usgs.gov/ogcapi/v1/collections/latest-continuous/items
- GBIF occurrence API: https://api.gbif.org/v1/occurrence/search
- Open-Meteo: https://api.open-meteo.com/v1/forecast

Live context is never written into the historical published record automatically.

## National benchmark
CPCB-derived Indian river dataset (2012–2023): https://github.com/KunalLatkar/RiverWaterQualityDataset

TraceIT does not silently vendor this third-party dataset. `scripts/download_cpcb_benchmark.py` downloads it explicitly and records it under `data/external/`.
