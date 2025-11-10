import re
import langdetect
import spacy
from functools import lru_cache
import yake
from multilangsetup.normalizers.turkish_normalizer import TurkishNormalizer


SUPPORTED_LANGUAGES = ["tr"]
NORMALIZERS = {
    "tr": TurkishNormalizer,
}

@lru_cache(maxsize=len(SUPPORTED_LANGUAGES))
def get_spacy_model(lang: str):
    model_map = {}
    model_name = model_map.get(lang)
    if model_name:
        try:
            return spacy.load(model_name)
        except OSError:
            return None
    return None


class MultiLangProcessor:

    @staticmethod
    def normalize(text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def detect_language(text: str) -> dict:
        try:
            detections = langdetect.detect_langs(text)
            if not detections:
                raise langdetect.lang_detect_exception.LangDetectException
            best_detection = detections[0]
            return {
                "lang": best_detection.lang.lower(),
                "confidence": round(best_detection.prob, 4)
            }
        except:
            return {"lang": "unknown", "confidence": 0.0}

    @staticmethod
    def analyze_text_structure(text: str) -> dict:
        words = text.split()
        word_count = len(words)
        unique_words = set(words)
        sentences = [s for s in re.split(r'[.!?]+', text) if s]

        return {
            "char_count": len(text),
            "word_count": word_count,
            "sentence_count": len(sentences),
            "unique_word_count": len(unique_words),
            "lexical_diversity": len(unique_words) / word_count if word_count > 0 else 0,
            "avg_word_length": sum(len(w) for w in words) / word_count if word_count > 0 else 0,
            "contains_numbers": any(ch.isdigit() for ch in text),
            "contains_emojis": bool(re.search(r"[\U0001F600-\U0001F64F]", text)),
            "contains_punctuation": bool(re.search(r"[^\w\s]", text))
        }

    @staticmethod
    def normalize_by_language(text: str, lang: str) -> str:
        normalizer_class = NORMALIZERS.get(lang)
        if normalizer_class:
            return normalizer_class.normalize_all(text)
        return text

    @staticmethod
    def extract_linguistic_features(text: str, lang: str) -> dict:
        nlp = get_spacy_model(lang)
        if not nlp:
            return {"error": f"Linguistic model for language '{lang}' not available."}

        doc = nlp(text)

        entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
        tokens = [token.text for token in doc]
        lemmas = [token.lemma_ for token in doc]

        return {
            "tokens": tokens,
            "lemmas": lemmas,
            "entities": entities
        }

    @staticmethod
    def extract_keywords(text: str, lang: str) -> dict:
        kw_extractor = yake.KeywordExtractor(lan=lang, n=1, dedupLim=0.9, top=10)
        keywords = kw_extractor.extract_keywords(text)
        return {"keywords": [{"term": kw, "score": score} for kw, score in keywords]}