import os
import platform

# Limit native thread pools only on macOS or when explicitly requested.
# This avoids Apple Silicon / XGBoost / sklearn threading conflicts
# without changing behavior for other platforms.
if platform.system() == "Darwin" or os.getenv("SINGLE_THREAD_EMBEDDING", "").lower() in {"1", "true", "yes"}:
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
import re
from sinling import SinhalaTokenizer
from transformers import AutoTokenizer, AutoModel
import numpy as np


class SinhalaPreprocessor:
    def __init__(self, model_name="xlm-roberta-base"):
        """
        Initializes the Sinhala Preprocessor.
        Uses XLM-RoBERTa as it is pre-trained on multiple languages including Sinhala.
        Downloads from Hugging Face if not cached locally.
        """
        print(f"Loading Transformer model: {model_name}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
        except Exception as e:
            raise RuntimeError(f"Failed to load model '{model_name}': {e}") from e

        self.sinhala_tokenizer = SinhalaTokenizer()

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        print(f"Model loaded on {self.device}")

    def clean_text(self, text):
        """
        Basic cleaning for Sinhala text and 'Singlish' terms.
        """
        if not text:
            return ""

        # Remove language tags like [SI], [EN]
        text = re.sub(r"\[(SI|EN|T)\]\s*", "", text)

        # 1. Remove URLs
        text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)

        # 2. Keep only alphanumeric (Sinhala + English) and whitespace
        text = re.sub(r"[^\w\s\u0D80-\u0DFF]", " ", text)
        text = re.sub(r"\s+", " ", text)

        # 3. Tokenize using Sinling (handles Sinhala punctuation better)
        tokens = self.sinhala_tokenizer.tokenize(text)

        # 3. Join back into a clean string
        return " ".join(tokens).strip()

    def get_embeddings(self, text):
        """
        Converts raw text into a 768-dimension vector.
        """
        cleaned_text = self.clean_text(text)

        # Tokenize for the Transformer
        inputs = self.tokenizer(
            cleaned_text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        ).to(self.device)

        # Extract features (Embeddings)
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Mean Pooling: average token embeddings to get one vector for the entire transcript
        embeddings = outputs.last_hidden_state.mean(dim=1)

        # Handle single input (batch_size=1) vs batched input
        squeeze_allowed = embeddings.shape[0] == 1
        result = (
            embeddings.squeeze().cpu().numpy()
            if squeeze_allowed
            else embeddings.cpu().numpy()
        )
        return result


# --- Internal Testing Block ---
if __name__ == "__main__":
    # Quick test to ensure everything is working locally
    preprocessor = SinhalaPreprocessor()
    test_transcript = "බොරු වැඩක්. මම payment එක කරා ඒත් තාම ඩිස්කනෙක්ට්."

    vector = preprocessor.get_embeddings(test_transcript)
    print(f"\nTest Transcript: {test_transcript}")
    print(f"Embedding Vector Shape: {vector.shape}")  # Should be (768,)
    print("Pre-processing Successful!")
