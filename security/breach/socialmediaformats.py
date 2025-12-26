import re
from dataclasses import dataclass
from typing import List, Tuple


RE_DISCORD_ID = re.compile(r"<@\d{17,20}>")
RE_DISCORD_TAG = re.compile(r"\b\w{2,32}#\d{4}\b")

RE_TELEGRAM_USERNAME = re.compile(r"(?:https?://)?t\.me/\w{3,32}", re.I)
RE_TELEGRAM_HANDLE = re.compile(r"@\w{5,32}")

RE_TWITTER_PROFILE = re.compile(
    r"(?:https?://)?(?:www\.)?(twitter|x)\.com/\w{3,15}",
    re.I
)

RE_INSTAGRAM_PROFILE = re.compile(
    r"(?:https?://)?(?:www\.)?instagram\.com/\w{3,30}",
    re.I
)

RE_TIKTOK_PROFILE = re.compile(
    r"(?:https?://)?(?:www\.)?tiktok\.com/@\w{3,24}",
    re.I
)

RE_FACEBOOK_PROFILE = re.compile(
    r"(?:https?://)?(?:www\.)?facebook\.com/(?:profile\.php\?id=\d+|\w+)",
    re.I
)

RE_GITHUB_PROFILE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_-]{1,39}",
    re.I
)

RE_LINKEDIN_PROFILE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]{3,100}",
    re.I
)

RE_STEAM_PROFILE = re.compile(
    r"(?:https?://)?steamcommunity\.com/(id|profiles)/\w+",
    re.I
)


@dataclass
class SocialSignal:
    platform: str
    spans: List[Tuple[int, int]]


class SocialMediaDetector:

    @staticmethod
    def detect(text: str) -> List[SocialSignal]:
        signals: List[SocialSignal] = []

        def add(platform: str, regex: re.Pattern):
            spans = [(m.start(), m.end()) for m in regex.finditer(text)]
            if spans:
                signals.append(SocialSignal(platform, spans))

        add("discord_id", RE_DISCORD_ID)
        add("discord_tag", RE_DISCORD_TAG)
        add("telegram", RE_TELEGRAM_USERNAME)
        add("telegram_handle", RE_TELEGRAM_HANDLE)
        add("twitter", RE_TWITTER_PROFILE)
        add("instagram", RE_INSTAGRAM_PROFILE)
        add("tiktok", RE_TIKTOK_PROFILE)
        add("facebook", RE_FACEBOOK_PROFILE)
        add("github", RE_GITHUB_PROFILE)
        add("linkedin", RE_LINKEDIN_PROFILE)
        add("steam", RE_STEAM_PROFILE)

        return signals
