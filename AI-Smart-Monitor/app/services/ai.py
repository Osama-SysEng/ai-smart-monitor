from typing import Protocol
import json, httpx
from app.core.config import settings

class LLMProvider(Protocol):
    def analyze(self, evidence: dict) -> dict: ...

class DeterministicFallback:
    def analyze(self, evidence):
        diff=float(evidence.get("difference",0))
        causes=[]
        if evidence.get("source_a") and evidence.get("source_b"):
            causes += [{"cause":"Delayed or incomplete source posting","classification":"POSSIBLE","confidence":0.72}]
        if evidence.get("historical_repeat"):
            causes += [{"cause":"Recurring process failure","classification":"LIKELY","confidence":0.84}]
        return {"summary":f"Evidence shows discrepancy of {diff}. Deterministic facts remain authoritative.",
                "confirmed_facts":evidence.get("facts",[]),"possible_causes":causes,
                "recommended_actions":["Verify source documents","Check posting timestamps","Review prior occurrences"],
                "confidence":0.80}

class OpenAIProvider:
    def analyze(self,evidence):
        if not settings.openai_api_key: return DeterministicFallback().analyze(evidence)
        prompt=("Analyze operational evidence. Never invent facts. Return JSON with summary, "
                "confirmed_facts, possible_causes[{cause,classification,confidence}], "
                "recommended_actions, confidence. Evidence:\n"+json.dumps(evidence,default=str))
        try:
            r=httpx.post("https://api.openai.com/v1/chat/completions",
              headers={"Authorization":f"Bearer {settings.openai_api_key}"},
              json={"model":settings.ai_model,"temperature":0,"response_format":{"type":"json_object"},
                    "messages":[{"role":"system","content":"You are an evidence-bound operations analyst."},
                                {"role":"user","content":prompt}]},timeout=settings.ai_timeout)
            r.raise_for_status()
            return json.loads(r.json()["choices"][0]["message"]["content"])
        except Exception:
            return DeterministicFallback().analyze(evidence)

class ProviderRouter:
    def get(self):
        return OpenAIProvider() if settings.ai_provider=="openai" else DeterministicFallback()

def get_provider(): return ProviderRouter().get()
