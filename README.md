# Sinhala Call Analytics

A hybrid ML system that categorizes customer care call transcripts and detects sentiment in Sinhala, with an analytics dashboard.

## Architecture

- **ML Pipeline:** XLM-RoBERTa embeddings + XGBoost classifiers for category and sentiment prediction
- **Backend:** FastAPI REST API with MySQL (SQLAlchemy async) for analytics storage
- **Folder Pipeline:** Automated background processor that watches a folder for transcript `.txt` files
- **Frontend:** React + Vite + Recharts + TailwindCSS dashboard

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- MySQL 8.x database
- Node.js 18+

## Setup

### 1. Environment Variables

```bash
cp .env.example .env
# Edit .env with your MySQL credentials
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
uv run python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8002
```

API runs at `http://localhost:8002`. Swagger docs at `/docs`.

### 5. Start Frontend (separate terminal)

```bash
cd frontend && npm run dev
```

Dashboard opens at `http://localhost:5173`.

## Folder Pipeline (Automated Transcript Processing)

The pipeline automatically watches a folder for `.txt` transcript files, processes them through ML, and saves results to MySQL — no manual upload needed.

### How It Works

```
data/transcripts/incoming/     ← Other team drops .txt files here
        │
        ▼ (pipeline polls every 30s)
  Read file → SHA-256 dedup → ML predict → Save to MySQL → Move to processed
        │
        ├── data/transcripts/processed/   ← Archived after success
        └── data/transcripts/error/       ← Failed files (bad transcript, etc.)
```

### Run Manually (One-Shot)

```bash
# Process all pending files in incoming/ and exit
uv run python -m src.pipeline.main

# Or with custom directories
uv run python -m src.pipeline.main --incoming D:\calls\transcripts --processed D:\calls\done --error D:\calls\errors
```

### Run as Background Service (Watch Mode)

```bash
# Polls incoming/ every 30s continuously
uv run python -m src.pipeline.main --watch
```

### Run at Startup (Windows Scheduled Task)

Use the provided setup script (run as Administrator):

```powershell
# In an Admin PowerShell terminal:
cd C:\path\to\sinhala_call_analytics
.\setup_pipeline_task.ps1
```

This creates a task named `SinhalaCallAnalytics-Pipeline` that:
- Starts automatically at every login
- Runs silently in the background (no window)
- Restarts up to 3 times if it crashes
- Polls `data/transcripts/incoming/` every 30 seconds

**Manual task management:**
```powershell
# Start immediately
Start-ScheduledTask -TaskName 'SinhalaCallAnalytics-Pipeline'

# Stop
Stop-ScheduledTask -TaskName 'SinhalaCallAnalytics-Pipeline'

# Check status
Get-ScheduledTask -TaskName 'SinhalaCallAnalytics-Pipeline' | Get-ScheduledTaskInfo
```

## How to Use (Web Dashboard)

1. Open the dashboard at `http://localhost:5173`
2. Paste a Sinhala call transcript into the **Ingest New Call** form, or upload a `.txt` file
3. Click **Analyze & Save** — the ML model categorizes it and detects sentiment
4. Results appear instantly in the dashboard KPIs, charts, and recent calls table
5. Calls processed by the folder pipeline also appear here automatically

## Project Structure

```
├── config/
│   └── config.yaml              # Application configuration
├── data/
│   ├── models/                  # Trained .joblib models
│   ├── transcripts/
│   │   ├── incoming/            # Drop .txt files here for auto-processing
│   │   ├── processed/           # Successfully processed files (archive)
│   │   └── error/               # Files that failed processing
│   └── ...
├── frontend/                    # React + Vite + TailwindCSS dashboard
├── src/
│   ├── pipeline/
│   │   ├── processor.py         # File scan → read → predict → save → archive
│   │   └── main.py              # CLI entry: one-shot or --watch mode
│   ├── inference.py             # CallAnalyticsPredictor class
│   ├── preprocessor.py          # Sinhala text cleaning + XLM-RoBERTa embeddings
│   ├── api/app.py               # FastAPI REST API server
│   └── database/                # SQLAlchemy models, repository, schemas
├── setup_pipeline_task.ps1      # Windows Task Scheduler installer
├── run_pipeline_hidden.vbs      # Silent VBS launcher (used by scheduled task)
├── .env.example
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
src/pipeline/main.py  ─── data/transcripts/incoming/  (auto-watch)
src/api/app.py         ─── POST /api/calls              (manual upload)
          ↓
MySQL (calls table)
          ↓
Frontend Dashboard (React)
```
