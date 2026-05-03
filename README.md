# Sinhala Call Analytics

A hybrid machine learning system that categorizes customer care call transcripts and detects sentiment in the Sinhala language, with a full analytics dashboard backend.

## Architecture

- **Teacher Phase:** Google Gemini generates labeled training data from raw transcripts
- **Student Phase:** XLM-RoBERTa embeddings + XGBoost classifiers for category and sentiment prediction
- **Backend:** FastAPI REST API with SQLite database for analytics storage
- **Frontend:** (Planned) React + Vite + Recharts dashboard

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Prepare Training Data

If you have raw labeled JSON files in `data/raw/`, combine them into a single dataset:

```bash
uv run src/01_datacombine.py
```

This reads all `data/raw/*.json` files and produces `data/processed/combined.json`.

> If you already have `data/processed/combined.json` checked out from this repo, skip this step.

### 3. Generate Embeddings and Train Models

This step produces the model files that `main.py` and the FastAPI server need:

```bash
uv run src/03_trainer.py
```

This script will:
1. Load `data/processed/combined.json`
2. Extract 768-dim XLM-RoBERTa embeddings for each transcript (cached to `data/embeddings/embeddings.npy`)
3. Encode category and sentiment labels
4. Train XGBoost classifiers with 5-fold cross-validation
5. Save trained models to `data/models/`:
   - `category_model.joblib`
   - `sentiment_model.joblib`
   - `label_encoders.joblib`
   - `training_summary.json`

> **First run takes a while** — embeddings are computed via the transformer model. Subsequent runs reuse cached embeddings unless you set `force_recompute=True`.

### 4. (Optional) Run Detailed Evaluation

```bash
uv run src/04_evaluator.py
```

Produces confusion matrices, classification reports, and a cross-validation summary.

### 5. Seed the Database (for API/Dashboard)

```bash
uv run src/database/seed.py
```

Creates the SQLite database (`data/analytics.db`), seeds sample agents, and runs inference on all transcripts in `combined.json` to populate call records.

### 6. Run the FastAPI Backend

```bash
uv run src/api/app.py
```

Starts the API server at `http://localhost:8000`. Swagger docs available at `http://localhost:8000/docs`.

### 7. Run Single Inference

```bash
# Interactive mode
uv run main.py

# Single transcript
uv run main.py -t "මට මගේ බිල්පත ගෙවන්න ඕනෙ"

# Batch from JSON file
uv run main.py -f path/to/transcripts.json
```

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
├── src/
│   ├── 01_datacombine.py        # Merge raw JSON into combined dataset
│   ├── 03_trainer.py            # Extract embeddings + train models
│   ├── 04_evaluator.py          # Model evaluation and reporting
│   ├── inference.py             # CallAnalyticsPredictor class
│   ├── preprocessor.py          # Sinhala text cleaning + XLM-RoBERTa embeddings
│   ├── api/app.py               # FastAPI REST API server
│   └── database/                # SQLAlchemy models, schemas, repository, seed
├── main.py                      # CLI entry point for inference
├── pyproject.toml
└── README.md
```

## Pipeline Summary

```
data/raw/*.json  →  01_datacombine.py  →  data/processed/combined.json
                                                    ↓
                                        03_trainer.py (embeddings + training)
                                                    ↓
                                        data/models/*.joblib
                                                    ↓
                                      main.py / FastAPI (inference)
                                                    ↓
                                        data/analytics.db (SQLite)
```
