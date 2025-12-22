import re
import langdetect
import spacy
from functools import lru_cache
import hashlib
import yake
from multilangsetup.normalizers.turkish_normalizer import TurkishNormalizer
from multilangsetup.normalizers.english_normalizer import EnglishNormalizer


SUPPORTED_LANGUAGES = ["tr", "en"]

NORMALIZERS = {
    "tr": TurkishNormalizer,
    "en": EnglishNormalizer
}

@lru_cache(maxsize=len(SUPPORTED_LANGUAGES))
def get_spacy_model(lang: str):
    model_map = {
        "en": "en_core_web_sm",
        "tr": None
    }
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
    def _get_text_hash(text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    _language_cache = {}
    
    @classmethod
    def detect_language(cls, text: str) -> dict:
        if not isinstance(text, str) or not text.strip():
            return {"lang": "unknown", "confidence": 0.0}

        text_hash = cls._get_text_hash(text)

        if text_hash in cls._language_cache:
            return cls._language_cache[text_hash]
        
        try:
            detections = langdetect.detect_langs(text)
            if not detections:
                raise langdetect.lang_detect_exception.LangDetectException
            best_detection = detections[0]
            result = {
                "lang": best_detection.lang.lower(),
                "confidence": round(best_detection.prob, 4)
            }

            cls._language_cache[text_hash] = result
            return result
        except:
            result = {"lang": "unknown", "confidence": 0.0}
            cls._language_cache[text_hash] = result
            return result
    
    @classmethod
    def clear_language_cache(cls):
        cls._language_cache.clear()

    @staticmethod
    def analyze_text_structure(text: str, lang: str = None) -> dict:
        words = text.split()
        word_count = len(words)
        unique_words = set(words)
        sentences = [s for s in re.split(r'[.!?]+', text) if s]

        base_analysis = {
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

        if lang == "en":
            from multilangsetup.normalizers.english_normalizer import EnglishNormalizer

            contraction_count = sum(1 for word in words if "'" in word.lower())

            complex_words = [w for w in words if len(w) > 6]

            capitalized_words = [w for w in words if w[0].isupper() if w]
            all_caps_words = [w for w in words if w.isupper() if w]

            avg_sentence_length = word_count / len(sentences) if len(sentences) > 0 else 0
            syllable_count = sum(EnglishNormalizer._count_syllables(w) for w in words)
            avg_syllables_per_word = syllable_count / word_count if word_count > 0 else 0

            readability_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
            readability_score = max(0, min(100, readability_score))
            
            base_analysis.update({
                "contraction_count": contraction_count,
                "complex_word_count": len(complex_words),
                "complex_word_ratio": len(complex_words) / word_count if word_count > 0 else 0,
                "capitalized_word_count": len(capitalized_words),
                "capitalization_ratio": len(capitalized_words) / word_count if word_count > 0 else 0,
                "all_caps_word_count": len(all_caps_words),
                "readability_score": round(readability_score, 2),
                "avg_sentence_length": round(avg_sentence_length, 2),
                "syllable_count": syllable_count,
                "avg_syllables_per_word": round(avg_syllables_per_word, 2)
            })

        return base_analysis

    @staticmethod
    def normalize_by_language(text: str, lang: str) -> str:
        normalizer_class = NORMALIZERS.get(lang)
        if normalizer_class:
            return normalizer_class.normalize_all(text)
        return text

    @staticmethod
    def extract_linguistic_features(text: str, lang: str) -> dict:
        MAX_SPACY_LENGTH = 2000

        if not isinstance(text, str):
            return {"error": "Invalid text"}

        entropy = 0.0
        normalizer = NORMALIZERS.get(lang)
        if normalizer and hasattr(normalizer, "calculate_entropy"):
            entropy = normalizer.calculate_entropy(text)

        if lang == "en":
            from multilangsetup.normalizers.english_normalizer import EnglishNormalizer
            preprocessed_text = EnglishNormalizer.preprocess_for_analysis(text)
        else:
            preprocessed_text = text

        if len(preprocessed_text) > MAX_SPACY_LENGTH:
            return {
                "warning": "Text too long for linguistic analysis",
                "length": len(preprocessed_text),
                "entropy": entropy
            }

        nlp = get_spacy_model(lang)
        if not nlp:
            return {
                "error": f"Linguistic model for language '{lang}' not available.",
                "entropy": entropy
            }

        doc = nlp(preprocessed_text)

        entities = [{"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char} for ent in doc.ents]
        tokens = [token.text for token in doc]
        lemmas = [token.lemma_ for token in doc]
        pos_tags = [{"token": token.text, "pos": token.pos_, "tag": token.tag_} for token in doc]

        features = {
            "tokens": tokens,
            "lemmas": lemmas,
            "entities": entities,
            "pos_tags": pos_tags,
            "entropy": entropy
        }
        
        if lang == "en":
            noun_phrases = [chunk.text for chunk in doc.noun_chunks]
            verb_phrases = []

            for i, token in enumerate(doc):
                if token.pos_ == "VERB":
                    verb_phrase = token.text
                    j = i - 1
                    while j >= 0 and doc[j].pos_ in ["AUX", "ADV"]:
                        verb_phrase = doc[j].text + " " + verb_phrase
                        j -= 1
                    verb_phrases.append(verb_phrase)
            
            features.update({
                "noun_phrases": noun_phrases,
                "verb_phrases": verb_phrases,
                "sentence_count": len(list(doc.sents)),
                "dependency_parse": [{"token": token.text, "dep": token.dep_, "head": token.head.text} for token in doc]
            })

        return features

    @staticmethod
    def extract_keywords(text: str, lang: str) -> dict:
        if lang == "en":
            from multilangsetup.normalizers.english_normalizer import EnglishNormalizer
            preprocessed_text = EnglishNormalizer.preprocess_for_keywords(text)
            kw_extractor = yake.KeywordExtractor(lan=lang, n=2, dedupLim=0.7, top=15)
        else:
            preprocessed_text = text
            kw_extractor = yake.KeywordExtractor(lan=lang, n=1, dedupLim=0.9, top=10)
        
        keywords = kw_extractor.extract_keywords(preprocessed_text)

        filtered_keywords = []
        for kw, score in keywords:
            if len(kw.strip()) > 2:
                filtered_keywords.append({
                    "term": kw.strip(),
                    "score": round(score, 4),
                    "normalized_score": round(1 - score, 4)
                })
        
        return {"keywords": filtered_keywords}