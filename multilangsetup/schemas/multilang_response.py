# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

class PrepareResponse(BaseModel):
    raw_text: str = Field(..., description="Original raw text received from the client.")
    normalized_text: str = Field(..., description="Normalized and cleaned version of the text.")
    language: str = Field(..., description="Detected or user-provided language code.")
    language_supported: bool = Field(..., description="Indicates whether the detected language is supported by the system.")
    ready_for_detection: bool = Field(..., description="Indicates if the text is ready for downstream processing or analysis.")

    analysis: Optional[Dict[str, Any]] = Field(None, description="Basic text structure analysis (e.g., word count, sentence count, lexical diversity).")
    linguistic_features: Optional[Dict[str, Any]] = Field(None, description="Linguistic features such as lemmas, tokens, and named entities.")
    language_detection: Optional[Dict[str, Any]] = Field(None, description="Detailed language detection information including confidence and source.")
    keywords: Optional[Dict[str, Any]] = Field(None, description="Extracted keywords from the text with their scores.")
    errors: Optional[Dict[str, str]] = Field(None, description="Step errors if any.")
    steps_executed: Optional[List[str]] = Field(None, description="Executed pipeline steps.")