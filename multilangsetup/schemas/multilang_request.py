# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from typing import Optional, List


class PrepareRequest(BaseModel):
    text: str = Field(..., description="The input text to be processed.")
    lang: Optional[str] = Field(None, description="Language code (e.g., 'tr', 'en', 'de'). If not provided, auto-detection will be used.")
    pipeline: Optional[List[str]] = Field(
        default=["normalize", "detect_language", "lang_normalize", "analyze", "linguistics"],
        description="List of pipeline stages to execute. Default: normalize → detect_language → lang_normalize → analyze → linguistics."
    )
    apply_obfuscation_resolver: bool = Field(
        default=True,
        description="Whether to apply ObfuscationResolver for symbol and noise cleaning."
    )


class BulkRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to be processed.")
    lang: Optional[str] = Field(None, description="Language code (e.g., 'tr', 'en', 'de'). If not provided, auto-detection will be used.")
    apply_obfuscation_resolver: bool = Field(
        default=False,
        description="Whether to apply ObfuscationResolver for symbol and noise cleaning."
    )
