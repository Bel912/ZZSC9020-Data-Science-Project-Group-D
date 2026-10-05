# Welcome to ZZSC9020 GitHub repository for group D.
# ZZSC9020 Group D: Rooftop PV and NSW Demand Forecasting

## Group and project information

## Research question
To what extent does adding recent rooftop PV information improve next-half-hour forecasts of NSW operational-demand change compared with otherwise matched non-PV models, and when is any improvement greatest?

### Group members and zIDs
- Bel Zhou (z5537223) - Data Engineer / Researcher
- Anders Appel (z5568978) - Data Engineer / Analyst
- William Sivieng (z3023671) - Project Lead

### Brief project description

Quantify the impact of rooftop solar generation on grid demand across different times of the day and under varying weather conditions.

## What this repository contains
- Week 1 to Week 6 project evidence and decision log
- End-to-end, commented Python pipeline for data preparation, EDA, modelling, benchmark alignment, validation and graph generation
- Final report in Word and PDF
- Exported report figures and machine-readable tables
- A reproducible notebook that calls the same pipeline functions
- A SHA-256 manifest and smoke tests

## Raw input files
Place the following source workbooks in `data/raw/` before a clean rerun:

1. `Rooftop PV Actual 2017-2026.xlsx`
2. `Operational Demand 202408 - 202608.xlsx`
3. `Operational Demand Forecast 202408 - 202608.xlsx`
4. `Daily Max Temperature.xlsx`
5. `Daily Min Temperature.xlsx`
6. `Daily Rainfall.xlsx`
7. `Daily Solar Exposure.xlsx`

Raw source workbooks are intentionally not duplicated in this ZIP because the available project source files are managed separately. `data/raw/README.md` records the required schemas and provenance. The processed outputs and final evidence shipped here remain auditable through the report, tables, figures and manifest.

## Reproduce the analysis
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_all.py
```

Optional notebook workflow:
```bash
jupyter lab notebooks/Weeks_1_to_6_Reproducible_Analysis.ipynb
```

## Pipeline order
1. `01_prepare_data.py`: validate schemas, standardise timestamps, consolidate duplicates, join AEMO and BoM inputs, and create lag/change/calendar features.
2. `02_generate_eda.py`: write data-quality tables and EDA figures.
3. `03_fit_models.py`: fit matched OLS, spline and histogram-gradient-boosted models with and without PV.
4. `04_validate_aemo_and_subgroups.py`: align the AEMO POE50 benchmark, calculate subgroup errors, paired-day bootstrap uncertainty and residual diagnostics.
5. `run_all.py`: run the complete sequence.

## Reproducibility rules
- Time order is preserved. No random train/test split is used.
- The first 80% of valid rows is training data and the final 20% is holdout data.
- Training-set medians are used for missing weather predictors.
- The target is next-half-hour operational-demand change.
- With-PV and without-PV models use identical holdout rows and identical non-PV predictors.
- The AEMO benchmark is retained only where a forecast version predates the target interval.
- Random seeds are fixed at 42.

## Main reported result
The final report records tree MAE of 62.13 MW with PV, 63.07 MW without PV, and 58.21 MW for the aligned AEMO benchmark. The largest reported tree-model improvement from PV is 2.01 MW during 06:00-12:00. These are modest predictive gains and are not interpreted causally.

## Repository map
- `docs/weeks/`: Week 1 to 6 work log
- `docs/methodology/`: data dictionary, assumptions, validation design and figure map
- `scripts/`: complete commented analysis code
- `notebooks/`: lecturer-facing runnable notebook
- `outputs/figures/`: report and supporting PNG charts
- `outputs/tables/`: CSV evidence tables
- `outputs/models/`: fixed model settings
- `report/`: final submission files
- `MANIFEST.sha256`: integrity checks

## Data licence and attribution
AEMO and Bureau of Meteorology data remain subject to their original terms. Do not commit restricted or oversized source data if repository rules or source licences prohibit redistribution.
