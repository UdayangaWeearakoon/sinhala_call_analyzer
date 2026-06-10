"""Robustness / edge-case tests for Sinhala Call Analytics."""
import os, sys, json, tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore

from src.preprocessor import SinhalaPreprocessor
from src.inference import CallAnalyticsPredictor


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


passed = 0
failed = 0


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}" + (f"  | {detail}" if detail else ""))


# ------------------------------------------------------------------
section("1. Preprocessor: edge-case inputs")

pre = SinhalaPreprocessor()

# Empty string
try:
    e = pre.get_embeddings("")
    check("Empty string", e.shape == (768,) and e.dtype == np.float32)
except Exception as ex:
    check("Empty string", False, str(ex))

# Whitespace only
try:
    e = pre.get_embeddings("   \t\n  ")
    check("Whitespace only", e.shape == (768,))
except Exception as ex:
    check("Whitespace only", False, str(ex))

# Punctuation only
try:
    e = pre.get_embeddings("!!! ??? ... ### $$$")
    check("Punctuation only", e.shape == (768,))
except Exception as ex:
    check("Punctuation only", False, str(ex))

# Non-Sinhala text (English)
try:
    e = pre.get_embeddings("Hello, this is a test call about my bill")
    check("English-only", e.shape == (768,))
except Exception as ex:
    check("English-only", False, str(ex))

# Mixed Sinhala + English
try:
    e = pre.get_embeddings("hello dada me kathawak")
    check("Mixed Sinhala+English", e.shape == (768,))
except Exception as ex:
    check("Mixed Sinhala+English", False, str(ex))

# Very long text (10k+ chars)
try:
    e = pre.get_embeddings("hello " * 5000)
    check("Very long text (10k+ chars)", e.shape == (768,))
except Exception as ex:
    check("Very long text (10k+ chars)", False, str(ex))

# Non-Sinhala Unicode + emoji
try:
    e = pre.get_embeddings("hello namaste")
    check("Non-Sinhala Unicode", e.shape == (768,))
except Exception as ex:
    check("Non-Sinhala Unicode", False, str(ex))

# Numeric string
try:
    e = pre.get_embeddings("12345 67890 111 222")
    check("Numeric only", e.shape == (768,))
except Exception as ex:
    check("Numeric only", False, str(ex))

# Newlines and tabs
try:
    e = pre.get_embeddings("line1\n\tline2\r\nline3")
    check("Newlines and tabs", e.shape == (768,))
except Exception as ex:
    check("Newlines and tabs", False, str(ex))


# ------------------------------------------------------------------
section("2. Predictor: edge-case transcripts")

predictor = CallAnalyticsPredictor()

edge_cases = [
    ("Empty string", ""),
    ("Whitespace only", "     "),
    ("Punctuation only", "!!! ??? ..."),
    ("English only", "I would like to check my account balance please"),
    ("Very short", "abc"),
    ("Numbers only", "123 456 789"),
]

for label, text in edge_cases:
    try:
        r = predictor.predict(text)
        ok = all(k in r for k in [
            "category", "sentiment", "category_confidence",
            "sentiment_confidence", "category_probabilities",
            "sentiment_probabilities",
        ])
        check(label, ok)
    except Exception as ex:
        check(label, False, str(ex))


# ------------------------------------------------------------------
section("3. Predictor: batch predict")

try:
    results = predictor.predict_batch(["hello", "test", ""])
    check("Batch predict (3 items)", len(results) == 3)
except Exception as ex:
    check("Batch predict (3 items)", False, str(ex))


# ------------------------------------------------------------------
section("4. Data integrity: embeddings / labels mismatch")

data_path = "data/processed/combined.json"
emb_path = "data/embeddings/embeddings.npy"

if os.path.exists(data_path) and os.path.exists(emb_path):
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    emb = np.load(emb_path)
    check("Embeddings count matches transcripts",
          emb.shape[0] == len(data),
          f"embeddings={emb.shape[0]}, labels={len(data)}")
else:
    check("Data files exist", False, "missing data/processed/combined.json or data/embeddings/embeddings.npy")


# ------------------------------------------------------------------
section("5. CLI entry points exist")

for name in ["01_datacombine.py", "03_trainer.py", "04_evaluator.py",
             "inference.py", "pipeline/main.py"]:
    check(f"File: src/{name}", os.path.exists(f"src/{name}"))


# ------------------------------------------------------------------
section("SUMMARY")
total = passed + failed
print(f"  Passed: {passed}/{total}")
print(f"  Failed: {failed}/{total}")
if failed:
    print("  ==> The system has robustness gaps. Review FAIL lines above.")
else:
    print("  ==> All edge cases handled correctly.")
