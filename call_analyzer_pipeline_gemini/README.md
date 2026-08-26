# Call Analyzer Pipeline (Gemini)

Automated call transcript classification pipeline for SLT customer service. Watches a directory for incoming transcripts, classifies them into business intent categories using **Google Gemini 2.5 Flash** (via OpenRouter), and persists results to MySQL.

## Prerequisites

- Python 3.14+
- MySQL 8.0+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
- OpenRouter API key ([get one here](https://openrouter.ai/keys))

## Project Structure

```
├── main.py                  # Entry point (spawns watcher + workers)
├── watcher.py               # Filesystem watcher with deduplication
├── worker.py                # Classification worker loop
├── classifier.py            # OpenRouter/Gemini API client
├── db.py                    # SQLAlchemy database session factory
├── schema.sql               # MySQL DDL for transcripts table
├── pyproject.toml           # Python dependencies (uv)
├── requirements.txt         # Pinned dependencies (pip fallback)
├── chaos_test.py            # Resilience/integration tests
├── deployment_and_ops.md    # Deployment & operations guide
├── docs/                    # BRD, SRS, SDD
├── incoming/                # Drop zone for new transcripts
├── processing/              # Files being classified
├── archive/                 # Successfully classified transcripts
└── error/                   # Dead-lettered (failed) transcripts
```

## Setup

### 1. Install dependencies

```bash
uv sync
```

Or with pip:

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 2. Database setup

Create the database and table:

```sql
CREATE DATABASE IF NOT EXISTS call_analyzer;
USE call_analyzer;
SOURCE schema.sql;
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Database (defaults shown)
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=call_analyzer

# Optional
OPENROUTER_MODEL=google/gemini-2.5-flash
WORKERS=1
BATCH_SIZE=5
BATCH_WAIT_SECONDS=60
```

## Usage

### Start the pipeline

```bash
uv run python main.py
```

Or with pip:

```bash
python main.py
```

### Classify transcripts

Drop `.txt` files into the `incoming/` directory. The pipeline will:

1. **Watch** `incoming/` for new files
2. **Deduplicate** using SHA-256 content hashing
3. **Classify** via Gemini 2.5 Flash into one of 6 categories
4. **Archive** successfully classified transcripts
5. **Dead-letter** failures after 5 retries

### Classification categories

| Category | Description |
|---|---|
| Billing | Balances, arrears, payment updates |
| Fault Reporting | Malfunctioning services, logged tickets |
| Products | Package updates, data allowances |
| Technical Assistance | Over-the-phone troubleshooting |
| Directory Inquiries | Phone number, address requests |
| Extra GB | Data balance checks, add-on purchases |

### Run tests

```bash
uv run python chaos_test.py
```

Tests cover: duplicate handling, empty file handling, rate-limit retries, and partial batch responses.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | - | **Required.** OpenRouter API key |
| `OPENROUTER_MODEL` | `google/gemini-2.5-flash` | Model to use |
| `OPENROUTER_MAX_TOKENS` | `256` | Max output tokens per request |
| `WORKERS` | `1` | Number of concurrent worker threads |
| `BATCH_SIZE` | `5` | Max transcripts per API call |
| `BATCH_WAIT_SECONDS` | `60` | Max wait for partial batch before flushing |
| `DB_HOST` | `127.0.0.1` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | `""` | MySQL password |
| `DB_NAME` | `call_analyzer` | MySQL database name |

## Architecture

```
incoming/ ──> [Watcher] ──> processing/ ──> [Worker] ──> [Classifier] ──> MySQL
                                                                            │
                                                              ┌─────────────┤
                                                              ▼             ▼
                                                          archive/      error/
```

- **Watcher**: Monitors `incoming/` using `watchdog`, deduplicates via content hash, inserts pending DB rows
- **Worker**: Polls DB for pending rows, claims them with row-level locking, batches them for classification
- **Classifier**: Calls OpenRouter API with structured JSON output, validates with Pydantic, retries on transient failures

## Further Reading

- [`deployment_and_ops.md`](deployment_and_ops.md) - Full deployment & operations guide
- [`docs/brd.md`](docs/brd.md) - Business Requirements Document
- [`docs/srs.md`](docs/srs.md) - Software Requirements Specification
- [`docs/sdd.md`](docs/sdd.md) - Solution Design Document
