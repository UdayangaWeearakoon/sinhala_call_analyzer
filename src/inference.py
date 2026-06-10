import os
import sys
import argparse
import json
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preprocessor import SinhalaPreprocessor


class CallAnalyticsPredictor:
    def __init__(self, models_dir="data/models"):
        print("Loading models...")
        self.preprocessor = SinhalaPreprocessor()

        self.category_model = joblib.load(
            os.path.join(models_dir, "category_model.joblib")
        )
        self.sentiment_model = joblib.load(
            os.path.join(models_dir, "sentiment_model.joblib")
        )
        self.label_encoders = joblib.load(
            os.path.join(models_dir, "label_encoders.joblib")
        )

        pca_path = os.path.join(models_dir, "pca.joblib")
        scaler_path = os.path.join(models_dir, "scaler.joblib")
        if os.path.exists(pca_path) and os.path.exists(scaler_path):
            self.pca = joblib.load(pca_path)
            self.scaler = joblib.load(scaler_path)
            print(f"PCA loaded: {self.pca.n_components_} components")
        else:
            self.pca = None
            self.scaler = None
            print("No PCA found — using raw 768-dim embeddings")

        print("Models loaded successfully!\n")

    def predict(self, transcript):
        embedding = self.preprocessor.get_embeddings(transcript)

        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)

        if self.pca is not None and self.scaler is not None:
            embedding = self.pca.transform(self.scaler.transform(embedding))

        category_encoded = self.category_model.predict(embedding)[0]
        sentiment_encoded = self.sentiment_model.predict(embedding)[0]

        category = self.label_encoders["category"].inverse_transform([category_encoded])[0]
        sentiment = self.label_encoders["sentiment"].inverse_transform([sentiment_encoded])[0]

        category_proba = self.category_model.predict_proba(embedding)[0]
        sentiment_proba = self.sentiment_model.predict_proba(embedding)[0]

        category_confidence = category_proba[category_encoded]
        sentiment_confidence = sentiment_proba[sentiment_encoded]

        return {
            "transcript": transcript,
            "category": category,
            "category_confidence": round(float(category_confidence), 3),
            "category_probabilities": {
                cls: round(float(prob), 3)
                for cls, prob in zip(self.label_encoders["category"].classes_, category_proba)
            },
            "sentiment": sentiment,
            "sentiment_confidence": round(float(sentiment_confidence), 3),
            "sentiment_probabilities": {
                cls: round(float(prob), 3)
                for cls, prob in zip(self.label_encoders["sentiment"].classes_, sentiment_proba)
            }
        }

    async def predict_and_save(self, transcript, metadata=None):
        result = self.predict(transcript)
        try:
            from src.database.models import Call
            from src.database.repository import create_call

            call_data = {
                "transcript": transcript,
                "category": result["category"],
                "sentiment": result["sentiment"],
                "category_confidence": result["category_confidence"],
                "sentiment_confidence": result["sentiment_confidence"],
                "call_duration": metadata.get("call_duration") if metadata else None,
                "agent_id": metadata.get("agent_id") if metadata else None,
                "customer_phone": metadata.get("customer_phone") if metadata else None,
                "resolved": metadata.get("resolved", False) if metadata else False,
                "notes": metadata.get("notes") if metadata else None,
            }
            call = await create_call(call_data)
            result["db_id"] = str(call.id)
            print(f"Saved to DB: call_id={call.id}")
        except Exception as e:
            print(f"Warning: Failed to save to DB: {e}")
        return result

    def predict_batch(self, transcripts):
        results = []
        for transcript in transcripts:
            results.append(self.predict(transcript))
        return results


def print_result(result):
    print("=" * 60)
    print("PREDICTION RESULT")
    print("=" * 60)
    print(f"\nTranscript: {result['transcript'][:100]}...")
    print(f"\nCategory: {result['category']}")
    print(f"   Confidence: {result['category_confidence']:.1%}")
    print("   Probabilities:")
    for cls, prob in result["category_probabilities"].items():
        marker = ">" if cls == result["category"] else " "
        print(f"     {marker} {cls}: {prob:.1%}")

    print(f"\nSentiment: {result['sentiment']}")
    print(f"   Confidence: {result['sentiment_confidence']:.1%}")
    print("   Probabilities:")
    for cls, prob in result["sentiment_probabilities"].items():
        marker = ">" if cls == result["sentiment"] else " "
        print(f"     {marker} {cls}: {prob:.1%}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Sinhala Call Analytics Predictor")
    parser.add_argument("-t", "--transcript", type=str, help="Single transcript to predict")
    parser.add_argument("-f", "--file", type=str, help="JSON file with transcripts")
    parser.add_argument("-m", "--models-dir", type=str, default="data/models",
                        help="Directory containing trained models")

    args = parser.parse_args()

    predictor = CallAnalyticsPredictor(models_dir=args.models_dir)

    if args.transcript:
        result = predictor.predict(args.transcript)
        print_result(result)

    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)

        transcripts = [item["transcript"] if isinstance(item, dict) else item
                       for item in data]

        results = predictor.predict_batch(transcripts)

        for i, result in enumerate(results, 1):
            print(f"\n{'='*60}")
            print(f"RESULT {i}/{len(results)}")
            print_result(result)

    else:
        print("Interactive Mode - Enter transcript (Ctrl+C to exit):\n")
        while True:
            try:
                transcript = input("Transcript: ")
                if transcript.strip():
                    result = predictor.predict(transcript)
                    print_result(result)
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break


if __name__ == "__main__":
    main()