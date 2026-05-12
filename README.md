# Sinhala Call Analytics

A hybrid machine learning system that categorizes customer care call transcripts and detects sentiment in the Sinhala language, with an analytics dashboard.

## Architecture

- **Teacher Phase:** Google Gemini generates labeled training data from raw transcripts
- **Student Phase:** XLM-RoBERTa embeddings + XGBoost classifiers for category and sentiment prediction
- **Backend:** FastAPI REST API with MongoDB Atlas (Beanie ODM) for analytics storage
- **Frontend:** React + Vite + Recharts + TailwindCSS dashboard

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- MongoDB Atlas cluster (or local MongoDB)
- Node.js 18+

## Setup

### 1. Environment Variables

```bash
cp .env.example .env
# Edit .env with your MongoDB Atlas URI
```

### 2. Install Dependencies

```bash
uv sync
cd frontend && npm install && cd ..
```

### 3. Train Models (one-time)

```bash
uv run src/03_trainer.py
```

Trains XGBoost classifiers and saves models to `data/models/`. Required before running inference.

### 4. Start Backend

```bash
uv run python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

API runs at `http://localhost:8000`. Swagger docs at `/docs`.

### 5. Start Frontend (separate terminal)

```bash
cd frontend && npm run dev
```

Dashboard opens at `http://localhost:5173`.

## How to Use

1. Open the dashboard at `http://localhost:5173`
2. Paste a Sinhala call transcript into the **Ingest New Call** form
3. Click **Analyze & Save** — the ML model categorizes it and detects sentiment
4. Results appear instantly in the dashboard KPIs, charts, and recent calls table

## Project Structure

```
├── config/
│   └── config.yaml              # Application configuration
├── data/
│   ├── processed/
│   │   └── combined.json        # Labeled training data
│   ├── raw/                     # Raw labeled batches (not tracked in git)
│   ├── embeddings/              # Cached XLM-RoBERTa embeddings (not tracked)
│   └── models/                  # Trained .joblib models (not tracked)
├── frontend/                    # React + Vite + TailwindCSS dashboard
├── src/
│   ├── 03_trainer.py            # Extract embeddings + train models
│   ├── 04_evaluator.py          # Model evaluation and reporting
│   ├── inference.py             # CallAnalyticsPredictor class
│   ├── preprocessor.py          # Sinhala text cleaning + XLM-RoBERTa embeddings
│   ├── api/app.py               # FastAPI REST API server
│   └── database/                # Beanie ODM models, repository
├── .env.example                 # Environment variables template
├── main.py                      # CLI entry point for inference
├── pyproject.toml
└── README.md
```

## Pipeline Summary

```
data/processed/combined.json
          ↓
03_trainer.py (embeddings + training)
          ↓
data/models/*.joblib
          ↓
FastAPI (inference via dashboard)
          ↓
MongoDB Atlas
```