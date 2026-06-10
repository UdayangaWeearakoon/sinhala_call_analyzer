import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
    f1_score
)
from sklearn.model_selection import cross_val_predict, StratifiedKFold, train_test_split
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ModelEvaluator:
    def __init__(self, models_dir="data/models"):
        self.models_dir = models_dir
        self.load_models()
        
    def load_models(self):
        print("Loading trained models...")
        
        self.category_model = joblib.load(
            os.path.join(self.models_dir, "category_model.joblib")
        )
        self.sentiment_model = joblib.load(
            os.path.join(self.models_dir, "sentiment_model.joblib")
        )
        self.label_encoders = joblib.load(
            os.path.join(self.models_dir, "label_encoders.joblib")
        )
        
        with open(os.path.join(self.models_dir, "training_summary.json"), "r") as f:
            self.summary = json.load(f)
        
        self.embeddings = np.load("data/embeddings/embeddings.npy")

        pca_path = os.path.join(self.models_dir, "pca.joblib")
        scaler_path = os.path.join(self.models_dir, "scaler.joblib")
        if os.path.exists(pca_path) and os.path.exists(scaler_path):
            pca = joblib.load(pca_path)
            scaler = joblib.load(scaler_path)
            self.embeddings = pca.transform(scaler.transform(self.embeddings))
            print(f"PCA applied: {self.embeddings.shape[1]} components")

        with open("data/processed/combined.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        if self.embeddings.shape[0] != len(data):
            raise ValueError(
                f"Embeddings count ({self.embeddings.shape[0]}) doesn't match "
                f"transcript count ({len(data)}). Re-run src/03_trainer.py to regenerate embeddings."
            )

        self.categories = [item["category"] for item in data]
        self.sentiments = [item["sentiment"] for item in data]
        
        self.y_category = self.label_encoders["category"].transform(self.categories)
        self.y_sentiment = self.label_encoders["sentiment"].transform(self.sentiments)
        
        print(f"Loaded embeddings shape: {self.embeddings.shape}")
        print(f"Category classes: {self.label_encoders['category'].classes_}")
        print(f"Sentiment classes: {self.label_encoders['sentiment'].classes_}")
        
    def evaluate_with_cv(self, n_splits=5):
        print("\n" + "=" * 60)
        print("CROSS-VALIDATION EVALUATION (5-Fold)")
        print("=" * 60)
        
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        
        results = {}
        
        for task, model in [("category", self.category_model), ("sentiment", self.sentiment_model)]:
            print(f"\n{'='*40}")
            print(f"{task.upper()} EVALUATION")
            print(f"{'='*40}")
            
            y_pred_cv = cross_val_predict(model, self.embeddings, 
                                          self.y_category if task == "category" else self.y_sentiment,
                                          cv=cv)
            
            y_true = self.y_category if task == "category" else self.y_sentiment
            labels = self.label_encoders[task].classes_
            
            acc = accuracy_score(y_true, y_pred_cv)
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_true, y_pred_cv, average="weighted", zero_division=0
            )
            
            print(f"\nAccuracy: {acc:.4f}")
            print(f"Precision (weighted): {precision:.4f}")
            print(f"Recall (weighted): {recall:.4f}")
            print(f"F1-Score (weighted): {f1:.4f}")
            
            print(f"\nDetailed Classification Report:")
            print(classification_report(y_true, y_pred_cv, target_names=labels, zero_division=0))
            
            results[task] = {
                "accuracy": acc,
                "precision": precision,
                "recall": recall,
                "f1": f1
            }
            
            cm = confusion_matrix(y_true, y_pred_cv)
            self.plot_confusion_matrix(cm, labels, task)
        
        return results
    
    def plot_confusion_matrix(self, cm, labels, task):
        os.makedirs("data/results", exist_ok=True)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                    xticklabels=labels, yticklabels=labels,
                    annot_kws={"size": 14})
        plt.title(f"Confusion Matrix - {task.title()}", fontsize=14, pad=20)
        plt.xlabel("Predicted", fontsize=12)
        plt.ylabel("Actual", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        filepath = os.path.join("data/results", f"confusion_matrix_{task}.png")
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"\nConfusion matrix saved to: {filepath}")
    
    def compare_models(self, X_train, y_train, X_test, y_test):
        print("\n" + "=" * 60)
        print("MODEL COMPARISON: XGBoost vs Random Forest")
        print("=" * 60)
        
        from sklearn.ensemble import RandomForestClassifier
        import xgboost as xgb
        
        models = {
            "XGBoost": xgb.XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8, random_state=42,
                use_label_encoder=False, eval_metric="mlogloss", n_jobs=-1
            ),
            "Random Forest": RandomForestClassifier(
                n_estimators=200, max_depth=15, min_samples_split=5,
                min_samples_leaf=2, random_state=42, n_jobs=-1
            )
        }
        
        comparison_results = {}
        
        for task_name, y in [("category", self.y_category), ("sentiment", self.y_sentiment)]:
            print(f"\n{'='*40}")
            print(f"{task_name.upper()} MODEL COMPARISON")
            print(f"{'='*40}")
            
            X_tr, X_te, y_tr, y_te = train_test_split(
                self.embeddings, y, test_size=0.2, random_state=42, stratify=y
            )
            
            best_model = None
            best_f1 = 0
            
            for model_name, model in models.items():
                model.fit(X_tr, y_tr)
                y_pred = model.predict(X_te)
                f1 = f1_score(y_te, y_pred, average="weighted", zero_division=0)
                acc = accuracy_score(y_te, y_pred)
                
                print(f"\n{model_name}:")
                print(f"  Test Accuracy: {acc:.4f}")
                print(f"  Test F1-Score: {f1:.4f}")
                
                if f1 > best_f1:
                    best_f1 = f1
                    best_model = model_name
                    comparison_results[task_name] = {
                        "best_model": model_name,
                        "best_f1": f1,
                        "accuracy": acc
                    }
            
            print(f"\nBest Model for {task_name}: {best_model} (F1: {best_f1:.4f})")
        
        return comparison_results
    
    def save_evaluation_report(self, cv_results, comparison_results=None):
        os.makedirs("data/results", exist_ok=True)
        
        report = {
            "evaluation_summary": cv_results,
            "embedding_dim": self.summary.get("embedding_dim"),
            "num_samples": self.summary.get("num_samples"),
            "category_classes": list(self.label_encoders["category"].classes_),
            "sentiment_classes": list(self.label_encoders["sentiment"].classes_),
        }
        
        if comparison_results:
            report["model_comparison"] = comparison_results
        
        report_path = os.path.join("data/results", "evaluation_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nEvaluation report saved to: {report_path}")
        return report
    
    def plot_class_distribution(self):
        os.makedirs("data/results", exist_ok=True)
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        categories = self.categories
        sentiments = self.sentiments
        
        axes[0].bar(*np.unique(categories, return_counts=True), color="steelblue")
        axes[0].set_title("Category Distribution", fontsize=12)
        axes[0].set_xlabel("Category")
        axes[0].set_ylabel("Count")
        axes[0].tick_params(axis="x", rotation=45)
        
        axes[1].bar(*np.unique(sentiments, return_counts=True), color="coral")
        axes[1].set_title("Sentiment Distribution", fontsize=12)
        axes[1].set_xlabel("Sentiment")
        axes[1].set_ylabel("Count")
        axes[1].tick_params(axis="x", rotation=45)
        
        plt.tight_layout()
        
        filepath = os.path.join("data/results", "class_distribution.png")
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Class distribution plot saved to: {filepath}")
    
    def run_full_evaluation(self):
        print("=" * 60)
        print("SINHALA CALL ANALYTICS - MODEL EVALUATION")
        print("=" * 60)
        
        self.plot_class_distribution()
        cv_results = self.evaluate_with_cv(n_splits=5)
        
        self.save_evaluation_report(cv_results)
        
        print("\n" + "=" * 60)
        print("EVALUATION COMPLETE!")
        print("=" * 60)
        print("\nOutput files in data/results/:")
        print("  - confusion_matrix_category.png")
        print("  - confusion_matrix_sentiment.png")
        print("  - class_distribution.png")
        print("  - evaluation_report.json")


def main():
    evaluator = ModelEvaluator()
    evaluator.run_full_evaluation()


if __name__ == "__main__":
    main()