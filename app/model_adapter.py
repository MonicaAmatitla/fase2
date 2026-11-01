"""Adapter for a pre-trained text classifier.

The production path loads a trusted Python pickle exposing predict([text]).
Without MODEL_PATH the application uses a deterministic demo classifier so the
API and UI can be exercised before the real model artifact is supplied.
"""
import os
import pickle
from pathlib import Path


class DemoModel:
    demo = True
    positive_words = {"bueno", "excelente", "feliz", "útil", "great", "good", "love"}

    def predict(self, values):
        text = str(values[0]).lower()
        return ["positivo" if any(word in text for word in self.positive_words) else "neutral/negativo"]


def load_model():
    model_path = os.getenv("MODEL_PATH", "")
    if not model_path:
        return DemoModel()
    path = Path(model_path)
    if not path.is_file():
        raise RuntimeError(f"MODEL_PATH no existe: {path}")
    # Only load model artifacts from a trusted source: pickle can execute code.
    with path.open("rb") as model_file:
        model = pickle.load(model_file)
    if not callable(getattr(model, "predict", None)):
        raise TypeError("El objeto del modelo debe exponer predict(list[str])")
    return model


MODEL = load_model()
IS_DEMO = bool(getattr(MODEL, "demo", False))


def predict(text):
    label = MODEL.predict([text])[0]
    response = {"prediction": str(label), "demo": IS_DEMO}
    predict_proba = getattr(MODEL, "predict_proba", None)
    if callable(predict_proba):
        try:
            response["probabilities"] = [float(value) for value in predict_proba([text])[0]]
        except (TypeError, ValueError, IndexError):
            pass
    return response
