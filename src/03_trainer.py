import os
import sys
import json
import numpy as np
import joblib
from tqdm import tqdm

import torch
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import xgboost as xgb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.preprocessor import SinhalaPreprocessor


class ModelTrainer:
    def __init__(self, data_path="data/processed/combined.json", embeddings_dir="data/embeddings"):
        self.data_path = data_path
        self.embeddings_dir = embeddings_dir
        os.makedirs(embeddings_dir, exist_ok=True)
        
        self.preprocessor = SinhalaPreprocessor()
        self.label_encoders = {}
        self.models = {}
        
    def load_data(self):
        print("Loading data...")
        with open(self.data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        
        self.transcripts = [item["transcript"] for item in self.data]
        self.categories = [item["category"] for item in self.data]
        self.sentiments = [item["sentiment"] for item in self.data]
        
        print(f"Loaded {len(self.transcripts)} transcripts")
        return self
    
    def extract_embeddings(self, batch_size=16, force_recompute=False):
        embeddings_path = os.path.join(self.embeddings_dir, "embeddings.npy")
        
        if os.path.exists(embeddings_path) and not force_recompute:
            cached = np.load(embeddings_path)
            if cached.shape[0] == len(self.transcripts):
                self.embeddings = cached
                print(f"Embeddings shape: {self.embeddings.shape}")
                return self
            print(f"Cache stale: {cached.shape[0]} embeddings for {len(self.transcripts)} transcripts. Recomputing...")
        
        print("Extracting embeddings...")
        self.embeddings = []
        
        for i in tqdm(range(0, len(self.transcripts), batch_size)):
            batch = self.transcripts[i:i + batch_size]
            
            for transcript in batch:
                try:
                    embedding = self.preprocessor.get_embeddings(transcript)
                except Exception:
                    embedding = np.zeros((768,), dtype=np.float32)
                if embedding.ndim == 1:
                    embedding = embedding.reshape(1, -1)
                self.embeddings.append(embedding)
        
        self.embeddings = np.vstack(self.embeddings)
        np.save(embeddings_path, self.embeddings)
        print(f"Embeddings shape: {self.embeddings.shape}")
        print(f"Embeddings saved to {embeddings_path}")
        return self
    
    def encode_labels(self):
        self.label_encoders["category"] = LabelEncoder()
        self.label_encoders["sentiment"] = LabelEncoder()
        
        self.y_category = self.label_encoders["category"].fit_transform(self.categories)
        self.y_sentiment = self.label_encoders["sentiment"].fit_transform(self.sentiments)
        
        print("\nCategory classes:", self.label_encoders["category"].classes_)
        print("Sentiment classes:", self.label_encoders["sentiment"].classes_)
        
        print("\nCategory distribution:")
        for label, count in zip(*np.unique(self.categories, return_counts=True)):
            print(f"  {label}: {count}")
        
        print("\nSentiment distribution:")
        for label, count in zip(*np.unique(self.sentiments, return_counts=True)):
            print(f"  {label}: {count}")
        
        return self
    
    def reduce_dimensions(self, n_components=64):
        print(f"\nReducing dimensions: 768 -> {n_components} via PCA...")
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=n_components, random_state=42)

        scaled = self.scaler.fit_transform(self.embeddings)
        self.embeddings = self.pca.fit_transform(scaled)

        variance = self.pca.explained_variance_ratio_.sum()
        print(f"Explained variance: {variance:.2%}")
        print(f"Reduced embeddings shape: {self.embeddings.shape}")

        pca_path = os.path.join("data/models", "pca.joblib")
        scaler_path = os.path.join("data/models", "scaler.joblib")
        joblib.dump(self.pca, pca_path)
        joblib.dump(self.scaler, scaler_path)
        print(f"PCA saved to: {pca_path}")
        print(f"Scaler saved to: {scaler_path}")
        return self

    def train_model(self, model_type="xgboost", n_splits=5):
        X = self.embeddings
        
        results = {}
        
        for task, y in [("category", self.y_category), ("sentiment", self.y_sentiment)]:
            print(f"\n{'='*50}")
            print(f"Training {task.upper()} classifier...")
            print(f"{'='*50}")
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            if model_type == "xgboost":
                model = xgb.XGBClassifier(
                    n_estimators=200,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    use_label_encoder=False,
                    eval_metric="mlogloss",
                    n_jobs=1
                )
            else:
                model = RandomForestClassifier(
                    n_estimators=200,
                    max_depth=15,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=1
                )
            
            print(f"\nRunning {n_splits}-fold cross-validation...")
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1_weighted")
            
            print(f"CV Scores: {cv_scores}")
            print(f"Mean CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
            
            print("\nTraining final model on full training set...")
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_test)
            test_acc = accuracy_score(y_test, y_pred)
            print(f"\nTest Accuracy: {test_acc:.4f}")
            
            print(f"\nClassification Report (Test Set):")
            print(classification_report(
                y_test, y_pred,
                target_names=self.label_encoders[task].classes_
            ))
            
            self.models[task] = model
            
            results[task] = {
                "cv_mean": cv_scores.mean(),
                "cv_std": cv_scores.std(),
                "test_accuracy": test_acc
            }
            
            model_path = os.path.join("data/models", f"{task}_model.joblib")
            os.makedirs("data/models", exist_ok=True)
            joblib.dump(model, model_path)
            print(f"Model saved to: {model_path}")
        
        encoders_path = os.path.join("data/models", "label_encoders.joblib")
        joblib.dump(self.label_encoders, encoders_path)
        print(f"Label encoders saved to: {encoders_path}")
        
        return results
    
    def save_summary(self, results):
        summary = {
            "embedding_dim": self.embeddings.shape[1],
            "num_samples": len(self.transcripts),
            "results": results,
            "category_classes": list(self.label_encoders["category"].classes_),
            "sentiment_classes": list(self.label_encoders["sentiment"].classes_)
        }
        
        summary_path = os.path.join("data/models", "training_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\nTraining summary saved to: {summary_path}")
        
        return summary


def main():
    print("=" * 60)
    print("SINHALA CALL ANALYTICS - MODEL TRAINING")
    print("=" * 60)
    
    trainer = ModelTrainer()
    
    trainer.load_data()
    trainer.extract_embeddings(force_recompute=False)
    trainer.encode_labels()
    trainer.reduce_dimensions(n_components=64)
    results = trainer.train_model(model_type="xgboost", n_splits=5)
    summary = trainer.save_summary(results)
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\nModels saved in: data/models/")
    print(f"Embeddings saved in: data/embeddings/")
    print("\nNext step: Run src/04_evaluator.py for detailed evaluation")


if __name__ == "__main__":
    main()