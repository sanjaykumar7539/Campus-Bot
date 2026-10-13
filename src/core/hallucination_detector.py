"""Optional LettuceDetect post-generation grounding verification."""
import logging
from config import config

logger = logging.getLogger(__name__)
_detector = None
_load_failed = False


def _get_detector():
    global _detector, _load_failed
    if not config.LETTUCEDETECT_ENABLED or _load_failed:
        return None
    if _detector is None:
        try:
            from lettucedetect.models.inference import HallucinationDetector
            _detector = HallucinationDetector(method="transformer", model_path=config.LETTUCEDETECT_MODEL)
        except Exception as exc:
            _load_failed = True
            logger.warning("LettuceDetect unavailable; existing grounding guardrails remain active: %s", exc)
            return None
    return _detector


def verify(context: str, question: str, answer: str) -> dict:
    detector = _get_detector()
    if detector is None or not context.strip() or not answer.strip():
        return {"checked": False, "supported": True, "spans": []}
    try:
        spans = detector.predict(
            context=[context], question=question, answer=answer,
            output_format="spans", min_confidence=config.LETTUCEDETECT_MIN_CONFIDENCE,
        ) or []
        return {"checked": True, "supported": len(spans) == 0, "spans": spans}
    except Exception as exc:
        logger.warning("LettuceDetect verification failed; fail-open to existing guardrails: %s", exc)
        return {"checked": False, "supported": True, "spans": [], "error": str(exc)}
