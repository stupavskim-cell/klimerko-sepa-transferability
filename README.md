# Network-level PM measurement transferability framework

Reproducibility package for the manuscript **“A Reproducible Framework for Evaluating Network-Level Agreement and Spatial Transferability of Low-Cost Particulate Matter Monitoring Against Regulatory Networks.”**

## What this repository reproduces

The workflow evaluates **city-day network-scale agreement and transferability** between a low-cost PM network and a regulatory monitoring network. It is **not** an individual-sensor collocation calibration package. The archived analysis inputs reproduce the manuscript's temporal 70/30 validation, strict leave-one-city-out (LOCO) validation, city-cluster bootstrap uncertainty, common-calendar sensitivity analysis, and exploratory environmental-domain analysis.

## Reproduce the core analysis

1. Create the software environment.
2. From the repository root run:

```bash
python src/run_analysis.py
python src/verify_results.py
```

The default run reads `data/analysis/paired_primary.csv` and `data/analysis/era5_city_daily.csv` and writes regenerated result tables to `outputs/reproduced/`.

## Expected analysis-ready input schema

`paired_primary.csv` contains: `Date`, `City`, `Pollutant`, `Klimerko`, `SEPA_city_mean`, `SEPA_station_n`, `Season`.

The meteorological table contains: `City`, `Date`, `T2m_mean_C`, `RH2m_mean_pct`, `Wind10m_mean_ms`, `Precipitation_sum_mm`.

A synthetic demonstration file is provided in `data/example/`. It contains no real monitoring observations.

## Main modelling conventions

- Heating season: 15 October–15 April.
- Cyclic month: `sin(2π(month−1)/12)` and `cos(2π(month−1)/12)`.
- Primary transferable model: linear regression using low-cost PM, heating indicator, cyclic month, ERA5 temperature, relative humidity, wind speed and precipitation.
- Temporal validation: chronological 70/30 split within each city.
- Spatial validation: strict LOCO; the held-out city's observations never enter fitting.
- Predictive R²: `1 − SSE/SST` evaluated only on held-out observations.
- Bootstrap: resampling is by city, not by individual day.
- Gradient boosting is a secondary fixed-configuration benchmark, not a tuned primary model.

## Data provenance and redistribution

The Serbian Environmental Protection Agency exposes an Open Data section on its air-quality portal. Public download availability alone, however, does not by itself establish a redistribution licence for every historical workbook. The original SEPA annual workbooks and the original Klimerko export are therefore **not included in this pre-release package** until their redistribution terms are verified. The exact analysis-ready paired table used for the manuscript is included for reproducibility, but its public release should likewise be checked against the source-data terms before publication. See `data/source/README.md`.

## ERA5 reconstruction

`src/download_era5.py` reconstructs the meteorological table from `data/analysis/city_coordinates.csv` using the Open-Meteo Historical Weather API with ERA5 explicitly selected and Europe/Belgrade daily aggregation.

## Citation and archival release

Before manuscript submission:

1. Create the GitHub repository and upload this package.
2. Connect the repository to Zenodo.
3. Create a GitHub release, recommended tag `v1.0.0`.
4. Confirm the Zenodo record and version-specific DOI.
5. Repository: https://github.com/stupavskim-cell/klimerko-sepa-transferability. After Zenodo archiving, insert the version-specific DOI into the repository and manuscript files.

Do **not** invent a DOI. The archived DOI is inserted only after Zenodo creates or reserves the record.

## Software licence

Code is released under the MIT License. This software licence does not override licences or terms applying to third-party monitoring data.

## Measurement-paper framework

This release implements the five-level evaluation protocol used in the associated Measurement manuscript: (I) association, (II) numerical agreement, (III) temporal generalisation, (IV) strict leave-one-city-out spatial transferability, and (V) domain-specific failure diagnosis. The workflow evaluates network-level city-day relationships; it must not be interpreted as instrument-level metrological calibration when collocation and traceability information are unavailable.

The primary purpose of the repository is reproducibility and reuse. Users can map their own date, location, pollutant, low-cost concentration and regulatory/reference concentration fields to the documented input schema and run the same evaluation sequence.
