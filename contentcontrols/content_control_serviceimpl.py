import time
from typing import Callable, Dict, List, Optional

from contentcontrols.content_control_service import ContentControlService
from contentcontrols.content_control import ContentDecision, ContentControlEngine
from contentcontrols.content_metrics import ContentMetrics
from customrules.customrule import CustomRule
from user.workspace import Workspace


class ContentControlServiceImpl(ContentControlService):

    ENGINE_TTL_SECONDS = 600

    def __init__(
        self,
        metrics: Optional[ContentMetrics] = None,
        rules_provider: Optional[Callable[[str], List[CustomRule]]] = None,
    ):
        self._engines: Dict[str, dict] = {}
        self._metrics = metrics or ContentMetrics()
        self._rules_provider = rules_provider

    def _cleanup_cache(self):
        now = time.time()
        self._engines = {wid: data for wid, data in self._engines.items()
                        if now - data.get("created_at", 0) <= self.ENGINE_TTL_SECONDS}

    def _create_engine_entry(self, workspace: Workspace) -> dict:
        return {
            "engine": ContentControlEngine(
                workspace,
                metrics=self._metrics,
                rules_provider=self._rules_provider,
            ),
            "created_at": time.time(),
        }

    def evaluate_content(self, workspace: Workspace, message: str, user_identifier: str,
                        user_role: Optional[str] = None, metadata: Optional[dict] = None,
                        force_refresh: bool = False) -> ContentDecision:
        if not workspace:
            raise ValueError("Workspace cannot be None")

        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        self._cleanup_cache()

        workspace_id = str(workspace.id)

        cache_entry = self._engines.get(workspace_id)
        needs_refresh = cache_entry is None or force_refresh

        if not needs_refresh and cache_entry["engine"].workspace.updated_at < workspace.updated_at:
            needs_refresh = True

        if needs_refresh:
            cache_entry = self._create_engine_entry(workspace)
            self._engines[workspace_id] = cache_entry
            self._metrics.record_cache_miss()
        else:
            self._metrics.record_cache_hit()

        user_identifier = user_identifier or "anonymous"
        metadata = metadata or {}

        try:
            decision = cache_entry["engine"].evaluate(
                user_id=user_identifier, message=message, user_role=user_role, metadata=metadata)
            
            response_time_ms = getattr(decision.metadata, 'response_time_ms', 0)
            detector = decision.metadata.get('detector', 'unknown') if decision.metadata else 'unknown'
            
            self._metrics.record_evaluation(
                user_id=user_identifier,
                allowed=decision.allowed,
                detector=detector,
                response_time_ms=response_time_ms
            )
            
            return decision
        except Exception as e:
            print(f"[ContentControl ERROR] workspace={workspace_id} error={str(e)}")
            return ContentDecision.allow()

    def get_metrics(self) -> ContentMetrics:
        return self._metrics