# THERMOS AI — Backend Engineering & Platform Architecture

**Integrated Urban Heat, Industrial & Vehicular Pollution Intelligence Platform**

THERMOS AI transforms fragmented environmental information — satellite thermal observations, industrial emission indicators, link-level vehicular traffic emissions, population vulnerability datasets, and statutory standards — into unified, explainable decision support for urban resilience and environmental compliance.

---

## 1. System Architecture & Tech Stack

```
                          ┌─────────────────────────────────────┐
                          │         THERMOS AI BACKEND          │
                          │   FastAPI (REST API - 55 Endpoints) │
                          └──────────────────┬──────────────────┘
                                             │
      ┌────────────────────┬─────────────────┼─────────────────┬───────────────────┐
      │                    │                 │                 │                   │
┌─────▼──────┐       ┌─────▼──────┐    ┌─────▼──────┐    ┌─────▼──────┐      ┌─────▼──────┐
│ Urban Heat │       │ Industrial │    │ Vehicular  │    │  Compound  │      │ ThermoSim  │
│  Module    │       │ Intelligence│   │ Intelligence│   │  Hotspots  │      │Intervention│
│(Landsat/LST│       │ (Tropomi/  │    │(CHETNA-Road│    │(Multi-Risk │      │ Simulator  │
│  Anomalies)│       │  MPCB CEMS)│    │ Link Flow) │    │ Synthesis) │      │  Engine    │
└─────┬──────┘       └─────┬──────┘    └─────┬──────┘    └─────┬──────┘      └─────┬──────┘
      │                    │                 │                 │                   │
      └────────────────────┼─────────────────┴─────────────────┼───────────────────┘
                           │                                   │
                ┌──────────▼──────────┐             ┌──────────▼──────────┐
                │   AI / ML Engine    │             │  Compliance & State │
                │ (RF & XGBoost LST)  │             │  Incident Workflow  │
                └──────────┬──────────┘             └──────────┬──────────┘
                           │                                   │
      ┌────────────────────┴───────────────────────────────────┴───────────────────┐
      │                         DATABASE & STORAGE LAYER                           │
      │  PostgreSQL 16 + PostGIS 3.4 (Production / Docker)                         │
      │  SQLite + Shapely Spatial Polymorphism (Local Development Standalone)      │
      └────────────────────────────────────────────────────────────────────────────┘
```

### Core Technologies
- **API Framework:** FastAPI 0.115+ (pure ASGI timing & request tracking, dependency injection)
- **Database ORM:** SQLAlchemy 2.0 with custom polymorphic `SpatialGeometry`
- **Spatial / GIS:** Shapely 2.0, GeoPandas, PyProj (UTM Zone 43N / EPSG:32643 metric projections)
- **Data Ingestion:** Pandas, Xarray, NetCDF4 (CHETNA-Road corridor netCDF grids)
- **Machine Learning:** Scikit-learn, XGBoost, Joblib
- **Testing:** Pytest (Unit, GIS, ML, API, and Unseen Data Integration test suites — 31 tests, 100% pass rate)
- **Containerization:** Docker Compose with `postgis/postgis:16-3.4`

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI entry point, ASGI middleware, exception handlers
│   ├── core/                    # Central settings, logging, security, domain exceptions
│   ├── api/                     # 11 REST API routers (55 endpoints)
│   ├── db/                      # Session factory, spatial polymorphic type, 37 ORM models
│   ├── schemas/                 # Pydantic v2 request/response schemas & GeoJSON types
│   ├── modules/                 # Domain business services (heat, industrial, risk, etc.)
│   └── data_pipeline/           # Ingestion pipelines (CSV, GeoJSON, NetCDF) & provenance
│
├── ml/
│   ├── training/                # RandomForest & XGBoost trainer with holdout validation
│   ├── inference/               # Explainable LST predictor with 95% confidence intervals
│   └── saved_models/            # Serialized joblib and json model artifacts
│
├── data/                        # Local SQLite database (thermos.db) and test assets
├── migrations/                  # Alembic database migrations
├── scripts/
│   ├── init_db.py               # Table creation & verification script
│   ├── seed_demo_data.py        # Pilot region (Panvel & Navi Mumbai) demo data seeder
│   └── train_models.py          # ML model training and validation pipeline
│
├── tests/
│   ├── unit/                    # Scientific calculation unit tests
│   ├── gis/                     # Spatial projection and buffer tests
│   ├── ml/                      # Prediction pipeline and feature importance tests
│   └── api/                     # End-to-end API integration tests
│
├── Dockerfile                   # Production container definition
├── docker-compose.yml           # PostGIS + FastAPI local orchestration
├── pytest.ini                   # Pytest runner configuration
└── requirements.txt             # Python dependency manifest
```

---

## 3. Quick Start & Local Setup

### Option A: Standalone Local Python (SQLite mode — Zero Docker Required)

1. **Activate Python Environment:**
   ```powershell
   # Ensure Python 3.11+ is installed
   python --version
   ```

2. **Install Dependencies:**
   ```powershell
   pip install -r backend/requirements.txt
   ```

3. **Initialize Database Tables:**
   ```powershell
   python backend/scripts/init_db.py
   ```

4. **Seed Pilot Region Demo Data (Panvel & Navi Mumbai):**
   ```powershell
   python backend/scripts/seed_demo_data.py
   ```

5. **Train AI/ML Predictive Models:**
   ```powershell
   python backend/scripts/train_models.py
   ```

6. **Start Backend Server:**
   ```powershell
   uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
   ```
   Open your browser at:
   - Interactive Swagger API Explorer: `http://localhost:8000/docs`
   - Redoc Documentation: `http://localhost:8000/redoc`
   - Health Check: `http://localhost:8000/health`

---

### Option B: Docker Compose (Full PostgreSQL 16 + PostGIS 3.4)

1. **Start PostGIS and Backend Containers:**
   ```bash
   docker compose up -d --build
   ```

2. **Verify Containers:**
   ```bash
   docker compose ps
   ```

3. **Run Database Migrations & Seeding:**
   ```bash
   docker compose exec backend python scripts/seed_demo_data.py
   ```

---

## 4. Running the Automated Test Suite

The test suite validates:
1. **Unit Tests:** Normalized scoring, LST anomaly calculation, cooling efficiency metrics.
2. **GIS Tests:** Metric projection (UTM Zone 43N / EPSG:32643), spatial containment, distance calculation.
3. **ML Tests:** RandomForest and XGBoost inference, 95% confidence intervals, explainability ranking.
4. **API Integration Tests:** Health checks, dashboard summaries, GeoJSON layers, What-If simulation, statutory compliance screening, incident reporting workflows.
5. **Unseen Data Generalization Tests:** Model generalization on unseen microclimate extremes, raw CSV & GeoJSON parsing, UTM Zone 43N metric spatial calculations, and incident lifecycles on unseen geographic coordinates.

Run all tests:
```powershell
python -m pytest backend/tests
```
Expected output:
```
backend/tests/api/test_endpoints.py ..........                           [ 32%]
backend/tests/gis/test_spatial_operations.py .....                       [ 48%]
backend/tests/integration/test_unseen_data.py ........                   [ 74%]
backend/tests/ml/test_prediction_pipeline.py ...                         [ 83%]
backend/tests/unit/test_environmental_indicators.py .....                [100%]

============================= 31 passed in 24.80s =============================
```

---

## 5. Signature Features

### 1. ThermoSim — Intervention Scenario Simulator
- Empirically models microclimate cooling, NOx deposition, and capital cost across 5 mitigation typologies:
  - **Tree Canopy Retrofit:** $\approx 0.06^\circ\text{C}$ cooling per $1\%$ canopy increase + $0.4\%$ NOx reduction.
  - **High-Albedo Cool Roofs:** $\approx 0.08^\circ\text{C}$ surface cooling per $0.05$ albedo gain.
  - **Industrial Green Buffers:** $50\text{m}$ vegetation barrier between factories and residential settlements.
  - **Freight & EV Electrification:** Heavy goods vehicle rerouting along express corridors.
  - **Combined Scenarios:** Integrated multi-hazard mitigation plans with side-by-side trade-off comparisons.

### 2. Multi-Hazard Compound Hotspot Synthesis
- Synthesizes fragmented environmental pressures into an explainable 0–100 index:
  $$\text{Score} = w_{\text{heat}} \cdot S_{\text{heat}} + w_{\text{ind}} \cdot S_{\text{ind}} + w_{\text{veh}} \cdot S_{\text{veh}} + w_{\text{exp}} \cdot S_{\text{exp}}$$
- Classifies severity (`critical`, `high`, `moderate`, `low`) and assigns primary hazard attribution without over-claiming single-source causality.

### 3. Statutory Compliance Screening Engine
- Transparent screening of environmental parameters against CPCB/MPCB NAAQS 2009 statutory benchmarks.
- Explains whether an observation represents a *potential exceedance* or is *within statutory limits*, with explicit regulatory disclaimers.

### 4. Incident Management & Grievance Lifecycle
- Complete end-to-end workflow: Citizen Intake $\to$ Multi-Hazard Context Synthesis (3km spatial radius) $\to$ Corrective Action Assignment $\to$ Audit History $\to$ Formal Closure.

---

## 6. Comprehensive Documentation Index

- [Complete API Contract (55 Endpoints)](file:///e:/Hackathons/HackOps2.0/docs/API_CONTRACT.md)
- [Frontend Integration & UI Developer Guide](file:///e:/Hackathons/HackOps2.0/docs/FRONTEND_INTEGRATION_GUIDE.md)
- [API Examples & Curl Payloads](file:///e:/Hackathons/HackOps2.0/docs/API_EXAMPLES.md)
- [Database Schema & Data Dictionary](file:///e:/Hackathons/HackOps2.0/docs/DATA_DICTIONARY.md)

