import re

def extract_placeholders(pattern: str):
    return re.findall(r"{(.*?)}", pattern)
