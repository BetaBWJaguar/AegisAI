from dataclasses import dataclass, field, asdict
from typing import Dict, Optional
from enum import Enum


class DoxxingAction(Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"


@dataclass
class DoxxingPIIConfig:
    enabled: bool = True
    weight: Optional[float] = None


@dataclass
class DoxxingContextConfig:
    enabled: bool = True
    weight: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DoxxingSettings:
    enabled: bool = False
    threshold: float = 1.20
    pii_config: Dict[str, DoxxingPIIConfig] = field(default_factory=lambda: {
        "email": DoxxingPIIConfig(enabled=True, weight=0.30),
        "phone": DoxxingPIIConfig(enabled=True, weight=0.45),
        "ipv4": DoxxingPIIConfig(enabled=True, weight=0.25),
        "coord": DoxxingPIIConfig(enabled=True, weight=0.55),
        "maps": DoxxingPIIConfig(enabled=True, weight=0.55),
        "id_number": DoxxingPIIConfig(enabled=True, weight=0.60),
        "iban": DoxxingPIIConfig(enabled=True, weight=0.65),
        "credit_card": DoxxingPIIConfig(enabled=True, weight=0.95),
        "url": DoxxingPIIConfig(enabled=True, weight=0.20),
        "birthdate": DoxxingPIIConfig(enabled=True, weight=0.35),
        "vin": DoxxingPIIConfig(enabled=True, weight=0.55),
        "health": DoxxingPIIConfig(enabled=True, weight=0.40),
    })
    context_config: Dict[str, DoxxingContextConfig] = field(default_factory=lambda: {
        "has_person": DoxxingContextConfig(enabled=True, weight=0.35),
        "has_target": DoxxingContextConfig(enabled=True, weight=0.25),
        "has_address_hint": DoxxingContextConfig(enabled=True, weight=0.35),
        "has_expose_intent": DoxxingContextConfig(enabled=True, weight=0.45),
        "has_social": DoxxingContextConfig(enabled=True, weight=0.30),
        "has_health": DoxxingContextConfig(enabled=True, weight=0.30),
        "has_vehicle": DoxxingContextConfig(enabled=True, weight=0.30),
    })

    detect_social_media: bool = True

    allow_self_disclosure: bool = True
    self_disclosure_penalty: float = 0.40

    risk_actions: Dict[str, str] = field(default_factory=lambda: {
        "LOW": "ALLOW",
        "MEDIUM": "WARN",
        "HIGH": "WARN",
        "CRITICAL": "BLOCK"
    })

    notify_user: bool = True
    notify_admin: bool = True

    log_violations: bool = True

    mask_content: bool = True
    
    def get_pii_weight(self, pii_type: str, default_weight: float) -> float:
        config = self.pii_config.get(pii_type)
        if config and config.enabled and config.weight is not None:
            return config.weight
        return default_weight
    
    def get_context_weight(self, context_type: str, default_weight: float) -> float:
        config = self.context_config.get(context_type)
        if config and config.enabled and config.weight is not None:
            return config.weight
        return default_weight
    
    def is_pii_enabled(self, pii_type: str) -> bool:
        config = self.pii_config.get(pii_type)
        return config.enabled if config else True
    
    def is_context_enabled(self, context_type: str) -> bool:
        config = self.context_config.get(context_type)
        return config.enabled if config else True
    
    def get_action_for_risk(self, risk_tier: str) -> str:
        return self.risk_actions.get(risk_tier.upper(), "ALLOW")
    
    def set_action_for_risk(self, risk_tier: str, action: str):
        valid_risks = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        valid_actions = {"ALLOW", "WARN", "WARN", "BLOCK"}
        
        risk_upper = risk_tier.upper()
        action_upper = action.upper()
        
        if risk_upper not in valid_risks:
            raise ValueError(f"Invalid risk '{risk_tier}'. Allowed: {valid_risks}")
        if action_upper not in valid_actions:
            raise ValueError(f"Invalid action '{action}'. Allowed: {valid_actions}")
        
        self.risk_actions[risk_upper] = action_upper
    
    def update_pii_config(self, pii_type: str, enabled: bool = None, weight: float = None):
        if pii_type not in self.pii_config:
            self.pii_config[pii_type] = DoxxingPIIConfig()
        
        if enabled is not None:
            self.pii_config[pii_type].enabled = enabled
        if weight is not None:
            self.pii_config[pii_type].weight = weight
    
    def update_context_config(self, context_type: str, enabled: bool = None, weight: float = None):
        if context_type not in self.context_config:
            self.context_config[context_type] = DoxxingContextConfig()
        
        if enabled is not None:
            self.context_config[context_type].enabled = enabled
        if weight is not None:
            self.context_config[context_type].weight = weight
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data["pii_config"] = {
            k: asdict(v) for k, v in self.pii_config.items()
        }
        data["context_config"] = {
            k: asdict(v) for k, v in self.context_config.items()
        }
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "DoxxingSettings":
        pii_config = {}
        if "pii_config" in data:
            for k, v in data["pii_config"].items():
                pii_config[k] = DoxxingPIIConfig(**v)

        context_config = {}
        if "context_config" in data:
            for k, v in data["context_config"].items():
                context_config[k] = DoxxingContextConfig(**v)

        data["pii_config"] = pii_config
        data["context_config"] = context_config
        
        return cls(**data)
