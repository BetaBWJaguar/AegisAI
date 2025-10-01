from enum import Enum

class DatasetType(str, Enum):
    PROFANITY = "PROFANITY"
    SPAM = "SPAM"
    TOXICITY = "TOXICITY"
    SENTIMENT = "SENTIMENT"
