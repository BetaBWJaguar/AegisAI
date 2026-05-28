# -*- coding: utf-8 -*-
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from pymongo import MongoClient

from config_loader import ConfigLoader

logger = logging.getLogger(__name__)

ESCALATION_TIERS: List[Dict] = [
    {"tier": 0, "min_infractions": 0, "multiplier": 1.0, "label": "CLEAN"},
    {"tier": 1, "min_infractions": 1, "multiplier": 1.0, "label": "FLAGGED"},
    {"tier": 2, "min_infractions": 2, "multiplier": 1.5, "label": "ESCALATED"},
    {"tier": 3, "min_infractions": 3, "multiplier": 2.0, "label": "HIGH_RISK"},
    {"tier": 4, "min_infractions": 5, "multiplier": 3.0, "label": "CRITICAL"},
]

DEFAULT_TTL_DAYS = 30


class EscalationService:
    def __init__(self, config_file: str = "config.json", ttl_days: int = DEFAULT_TTL_DAYS):
        cfg = ConfigLoader(config_file).get_database_config()
        uri = (
            f"mongodb://{cfg['username']}:{cfg['password']}@"
            f"{cfg['host']}:{cfg['port']}/{cfg['authSource']}"
        )
        self._client = MongoClient(uri)
        self._db = self._client[cfg["name"]]
        self._col = self._db["escalations"]
        self._ttl_days = ttl_days
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self._col.create_index("fingerprint", unique=True)
        self._col.create_index("ip")
        self._col.create_index("expires_at", expireAfterSeconds=0)


    @staticmethod
    def generate_fingerprint(ip: str, user_agent: str = "", accept_language: str = "") -> str:
        raw = f"{ip}|{user_agent}|{accept_language}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]

    def record_infraction(
        self,
        ip: str,
        risk_level: str,
        category: Optional[str] = None,
        confidence: float = 1.0,
        user_agent: str = "",
        accept_language: str = "",
        fingerprint: Optional[str] = None,
    ) -> Dict:
        fp = fingerprint or self.generate_fingerprint(ip, user_agent, accept_language)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=self._ttl_days)

        infraction_entry = {
            "timestamp": now.isoformat(),
            "risk_level": risk_level,
            "category": category,
            "confidence": round(confidence, 4),
        }

        self._col.update_one(
            {"fingerprint": fp},
            {
                "$push": {"infractions": infraction_entry},
                "$inc": {"total_count": 1},
                "$set": {
                    "last_infraction_at": now.isoformat(),
                    "expires_at": expires,
                    "ip": ip,
                },
                "$setOnInsert": {
                    "user_agent": user_agent,
                    "first_infraction_at": now.isoformat(),
                },
            },
            upsert=True,
        )

        return self.get_escalation_state(ip, user_agent, accept_language, fingerprint=fp)


    def get_escalation_state(
        self,
        ip: str,
        user_agent: str = "",
        accept_language: str = "",
        fingerprint: Optional[str] = None,
    ) -> Dict:
        fp = fingerprint or self.generate_fingerprint(ip, user_agent, accept_language)
        doc = self._col.find_one({"fingerprint": fp})

        if not doc:
            return self._build_state(fp, 0, [], ip)

        return self._build_state(fp, doc.get("total_count", 0), doc.get("infractions", []), ip)


    def get_escalation_multiplier(
        self,
        ip: str,
        user_agent: str = "",
        accept_language: str = "",
        fingerprint: Optional[str] = None,
    ) -> float:
        state = self.get_escalation_state(ip, user_agent, accept_language, fingerprint)
        return state["multiplier"]


    def get_by_fingerprint(self, fingerprint: str) -> Optional[Dict]:
        doc = self._col.find_one({"fingerprint": fingerprint})
        if not doc:
            return None
        return self._build_state(
            fingerprint,
            doc.get("total_count", 0),
            doc.get("infractions", []),
            doc.get("ip", ""),
        )

    def list_all(self, limit: int = 100) -> List[Dict]:
        cursor = self._col.find({}, {"_id": 0}).sort("total_count", -1).limit(limit)
        results = []
        for doc in cursor:
            results.append(self._build_state(
                doc["fingerprint"],
                doc.get("total_count", 0),
                doc.get("infractions", []),
                doc.get("ip", ""),
            ))
        return results

    def reset(self, fingerprint: str) -> bool:
        result = self._col.delete_one({"fingerprint": fingerprint})
        return result.deleted_count > 0

    @staticmethod
    def _resolve_tier(count: int) -> Dict:
        matched = ESCALATION_TIERS[0]
        for tier in ESCALATION_TIERS:
            if count >= tier["min_infractions"]:
                matched = tier
        return matched

    def _build_state(self, fingerprint: str, count: int, infractions: List[Dict], ip: str) -> Dict:
        tier_info = self._resolve_tier(count)

        category_breakdown: Dict[str, int] = {}
        risk_breakdown: Dict[str, int] = {}
        for inf in infractions:
            cat = inf.get("category") or "UNCATEGORIZED"
            category_breakdown[cat] = category_breakdown.get(cat, 0) + 1
            rl = inf.get("risk_level", "LOW")
            risk_breakdown[rl] = risk_breakdown.get(rl, 0) + 1

        return {
            "fingerprint": fingerprint,
            "ip": ip,
            "total_infractions": count,
            "tier": tier_info["tier"],
            "label": tier_info["label"],
            "multiplier": tier_info["multiplier"],
            "category_breakdown": category_breakdown,
            "risk_breakdown": risk_breakdown,
            "last_infraction_at": infractions[-1]["timestamp"] if infractions else None,
        }
