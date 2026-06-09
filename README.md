# Sinhala Call Analytics

A hybrid ML system that categorizes customer care call transcripts and detects sentiment in Sinhala, with an analytics dashboard.

## Architecture

- **Embeddings:** XLM-RoBERTa (`xlm-roberta-base`) → 768-dim vectors
- **Dimensionality Reduction:** PCA (768 → 64 components)
- **Classifiers:** XGBoost for category and sentiment prediction
- **Backend:** FastAPI REST API with SQLite (SQLAlchemy async)
- **Folder Pipeline:** Automated background processor that watches a folder for transcript `.txt` files
- **Frontend:** React + Vite + Recharts + TailwindCSS dashboard

## Prerequisites

- Python 3.10+
- [Node.js](https://nodejs.org/) 18+

## Setup

### 1. Clone & Install Python Dependencies

```bash
git clone <repo-url>
cd sinhala_call_analytics
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work for local dev)
```

## Training Pipeline (One-Time)

Run these steps in order after placing labeled transcript JSON files in `data/raw/`.

### Step 1: Combine Raw Data

```bash
.venv\Scripts\activate
python src/01_datacombine.py
```

Combines all JSON files from `data/raw/` into `data/processed/combined.json`.

### Step 2: Train Models

```bash
python src/03_trainer.py
```

This does the following automatically:
1. Loads transcripts from `data/processed/combined.json`
2. Extracts 768-dim embeddings via XLM-RoBERTa
3. Encodes labels (category + sentiment)
4. Applies PCA (768 → 64 components, ~80% variance retained)
5. Trains XGBoost classifiers with 5-fold cross-validation
6. Saves models to `data/models/`:
   - `category_model.joblib`
   - `sentiment_model.joblib`
   - `label_encoders.joblib`
   - `pca.joblib`
   - `scaler.joblib`
   - `training_summary.json`

### Step 3: Evaluate (Optional)

```bash
python src/04_evaluator.py
```

Generates confusion matrices, classification reports, and class distribution plots in `data/results/`.

## Running the System

### Start Backend API

```bash
.venv\Scripts\activate
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8002
```

API runs at `http://localhost:8002`. Swagger docs at `http://localhost:8002/docs`.

### Start Frontend (separate terminal)

```bash
cd frontend
npm run dev
```

Dashboard opens at `http://localhost:5173`.

### Test Inference Interactively

```bash
.venv\Scripts\activate
python -m src.inference
```

Or predict a single transcript:

```bash
python -m src.inference -t "ආයුබෝවන්, මගේ බිල ගැන ප්රශ්නයක්."
```

Or batch predict from a JSON file:

```bash
python -m src.inference -f data/processed/combined.json
```

## Folder Pipeline (Automated Transcript Processing)

The pipeline watches a folder for `.txt` transcript files, processes them through ML, deduplicates via SHA-256, saves to the database, and archives the files.

### How It Works

```
data/transcripts/incoming/     ← Drop .txt files here
        │
        ▼ (pipeline polls every 30s)
  Read file → SHA-256 dedup → ML predict → Save to SQLite → Move to processed
        │
        ├── data/transcripts/processed/   ← Archived after success
        └── data/transcripts/error/       ← Failed files
```

### Run Manually (One-Shot)

```bash
.venv\Scripts\activate
python -m src.pipeline.main
```

### Run as Background Service (Watch Mode)

```bash
python -m src.pipeline.main --watch
```

Polls `data/transcripts/incoming/` every 30 seconds continuously.

### Run at Startup (Windows Scheduled Task)

Run this PowerShell as Administrator:

```powershell
.\setup_pipeline_task.ps1
```

This creates a task named `SinhalaCallAnalytics-Pipeline` that:
- Starts automatically at login
- Runs silently in the background (no window)
- Restarts up to 3 times if it crashes

**Manual task management:**

```powershell
Start-ScheduledTask -TaskName 'SinhalaCallAnalytics-Pipeline'
Stop-ScheduledTask -TaskName 'SinhalaCallAnalytics-Pipeline'
Get-ScheduledTask -TaskName 'SinhalaCallAnalytics-Pipeline' | Get-ScheduledTaskInfo
```

## How to Use (Web Dashboard)

1. Open the dashboard at `http://localhost:5173`
2. Paste a Sinhala call transcript into the **Ingest New Call** form, or upload a `.txt` file
3. Click **Analyze & Save** — the ML model categorizes it and detects sentiment
4. Results appear instantly in the dashboard KPIs, charts, and recent calls table
5. Calls processed by the folder pipeline also appear here automatically

## Data Format

### Training Data (`data/raw/*.json`)

```json
[
  {
    "transcript": "ආයුබෝවන්, මගේ බිල ගැන ප්රශ්නයක්.",
    "category": "Billing",
    "sentiment": "Neutral",
    "resolved": "Yes"
  }
]
```

### Pipeline Input (`data/transcripts/incoming/*.txt`)

Plain UTF-8 text files containing the full call transcript.

## Project Structure

```
├── config/
│   └── config.yaml              # Application configuration
├── data/
│   ├── models/                  # Trained .joblib models + PCA + scaler
│   ├── processed/
│   │   └── combined.json        # Combined training data
│   ├── transcripts/
│   │   ├── incoming/            # Drop .txt files here for auto-processing
│   │   ├── processed/           # Successfully processed files (archive)
│   │   └── error/               # Files that failed processing
│   └── raw/                     # Source training JSON files
├── frontend/                    # React + Vite + TailwindCSS dashboard
├── src/
│   ├── pipeline/
│   │   ├── processor.py         # File scan → read → predict → save → archive
│   │   └── main.py              # CLI entry: one-shot or --watch mode
│   ├── inference.py             # CallAnalyticsPredictor class
│   ├── preprocessor.py          # Sinhala text cleaning + XLM-RoBERTa embeddings
│   ├── 01_datacombine.py        # Combine raw JSONs
│   ├── 03_trainer.py            # Embeddings → PCA → XGBoost training
│   ├── 04_evaluator.py          # Evaluation + confusion matrices
│   ├── api/
│   │   └── app.py               # FastAPI REST API server
│   └── database/                # SQLAlchemy models, repository, schemas
├── setup_pipeline_task.ps1      # Windows Task Scheduler installer
├── run_pipeline_hidden.vbs      # Silent VBS launcher (used by scheduled task)
├── pyproject.toml
└── README.md
```

## Training Pipeline Summary

```
data/raw/*.json
       ↓
01_datacombine.py
       ↓
data/processed/combined.json
       ↓
03_trainer.py
  ├── XLM-RoBERTa embeddings (768-dim)
  ├── PCA reduction (64-dim)
  └── XGBoost training (5-fold CV)
       ↓
data/models/*.joblib
       ↓
src/inference.py  ─── Predictor class (used by API + pipeline)
src/api/app.py    ─── POST /api/calls (manual upload)
src/pipeline/     ─── Folder watcher (auto-upload)
       ↓
SQLite (analytics.db)
       ↓
Frontend Dashboard (React)
```
