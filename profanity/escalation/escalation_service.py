# -*- coding: utf-8 -*-
import hashlib
import logging
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

import httpx
from pymongo import MongoClient, ReturnDocument

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
        uri = f"mongodb://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['authSource']}"
        self._client = MongoClient(uri)
        self._db = self._client[cfg["name"]]
        self._col = self._db["escalations"]
        self._rules_col = self._db["escalation_rules"]
        self._ttl_days = ttl_days
        self._cooldown_map: Dict[str, float] = {}
        self._cooldown_seconds = 5.0
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

        current_time = time.time()
        last_infraction_time = self._cooldown_map.get(fp, 0.0)

        if (current_time - last_infraction_time) < self._cooldown_seconds:
            logger.info(f"Cooldown active for fingerprint={fp}. Absorbing spam.")
            return self.get_escalation_state(ip, user_agent, accept_language, fingerprint=fp)

        self._cooldown_map[fp] = current_time

        expires = now + timedelta(days=self._ttl_days)

        infraction_entry = {
            "timestamp": now.isoformat(),
            "risk_level": risk_level,
            "category": category,
            "confidence": round(confidence, 4),
        }


        old_doc = self._col.find_one_and_update(
            {"fingerprint": fp},
            {
                "$push": {"infractions": {"$each": [infraction_entry], "$slice": -50}},
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
            return_document=ReturnDocument.BEFORE
        )

        old_count = 0
        if old_doc:
            old_count = old_doc.get("total_count", 0)

        new_count = old_count + 1
        old_tier_info = self._resolve_tier(old_count)
        new_tier_info = self._resolve_tier(new_count)

        if new_tier_info["tier"] > old_tier_info["tier"]:
            event_payload = self._generate_event_payload(
                fp, ip, old_tier_info["tier"], new_tier_info["tier"],
                new_tier_info["label"], new_count, category
            )
            self._dispatch_actions_async(new_tier_info["tier"], event_payload)

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
        if fingerprint in self._cooldown_map:
            del self._cooldown_map[fingerprint]
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


    @staticmethod
    def _generate_event_payload(fp, ip, old_tier, new_tier, new_label, total_infractions, category) -> Dict:
        return {
            "event_type": "ESCALATION_TIER_CHANGED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "fingerprint": fp,
                "ip": ip,
                "previous_tier": old_tier,
                "current_tier": new_tier,
                "label": new_label,
                "total_infractions": total_infractions,
                "latest_category": category,
                "action_required": new_tier >= 3
            }
        }

    def _dispatch_actions_async(self, tier: int, event_payload: Dict):
        rule_doc = self._rules_col.find_one({"tier": tier})

        if not rule_doc or "actions" not in rule_doc:
            return

        actions = rule_doc["actions"]

        thread = threading.Thread(
            target=self._execute_actions,
            args=(actions, event_payload),
            daemon=True
        )
        thread.start()

    def _execute_actions(self, actions: List[Dict], event_payload: Dict):
        fp = event_payload['data']['fingerprint']

        for action in actions:
            try:
                action_type = action.get("type", "").upper()

                if action_type == "LOG":
                    level = action.get("level", "INFO").lower()
                    log_msg = f"Action | Tier {event_payload['data']['current_tier']} | FP: {fp}"
                    getattr(logger, level, logger.info)(log_msg)

                elif action_type == "DB_UPDATE":
                    update_fields = action.get("update_fields", {})
                    if update_fields:
                        self._col.update_one(
                            {"fingerprint": fp},
                            {"$set": update_fields}
                        )
                        logger.info(f"DB Updated FP: {fp} -> {update_fields}")

                else:
                    logger.warning(f"Uknown Action Types {action_type}")

            except Exception as e:
                logger.error(f"Action not workin '{action.get('name')}': {str(e)}")

    def _send_webhook(self, action_config: Dict, event_payload: Dict):
        url = action_config.get("url")
        method = action_config.get("method", "POST").upper()
        headers = action_config.get("headers", {"Content-Type": "application/json"})
        template = action_config.get("payload_template", event_payload)

        payload = self._render_template(template, event_payload.get("data", {}))

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.request(
                    method=method,
                    url=url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                logger.info(f"Action '{action_config.get('name')}' dispatched successfully to {url}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Webhook failed (HTTP {e.response.status_code}) for action '{action_config.get('name')}': {e.response.text}")
        except Exception as e:
            logger.error(f"Webhook request failed for action '{action_config.get('name')}': {str(e)}")

    @staticmethod
    def _render_template(template: Dict, data: Dict) -> Dict:
        if not isinstance(template, dict):
            return template

        rendered = {}
        for key, value in template.items():
            if isinstance(value, str):
                for data_key, data_val in data.items():
                    placeholder = f"{{{{{data_key}}}}}"
                    if placeholder in value:
                        value = value.replace(placeholder, str(data_val))
                rendered[key] = value
            elif isinstance(value, dict):
                rendered[key] = EscalationService._render_template(value, data)
            elif isinstance(value, list):
                rendered[key] = [EscalationService._render_template(item, data) if isinstance(item, dict) else item for item in value]
            else:
                rendered[key] = value
        return rendered