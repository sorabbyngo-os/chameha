"""
conversation.py — Tier router + Public/Personal Chameha mode resolver
Public Chameha  -> existing T1/T2/T3 routing, shared personality
Personal Chameha-> twin context injected, domain detection, T2 escalation
"""
from __future__ import annotations
import logging, re
from identity import get_active_user_id, get_twin_session, TwinSessionInfo
from twin_client import fetch_twin_context, push_interaction, TwinContext, TwinUnavailable
from tier1 import Tier1
from tier2 import Tier2
from tier3 import Tier3
from personality.tone_engine import PublicTone, PersonalTone

log = logging.getLogger("chameha.conversation")

HIGH_STAKES_DOMAINS = {"medical", "financial", "legal"}
_CLOUD_PREFIX       = re.compile(r"^/cloud\s+", re.IGNORECASE)
_COMPLEX_THRESHOLD  = 80

_MEDICAL_KW   = re.compile(r"\b(symptom|diagnos|medic|drug|dose|hospital|pain|ill|sick|treat|pressure|sugar|diabetes|prescri)\b", re.I)
_FINANCIAL_KW = re.compile(r"\b(invest|portfolio|stock|fund|savings|loan|debt|mortgage|insurance|tax|pension|budget|afford)\b", re.I)
_LEGAL_KW     = re.compile(r"\b(contract|lawsuit|legal|court|rights|clause|liability|attorney|lawyer|sue|compliance)\b", re.I)

def _detect_domain(prompt: str) -> str:
    if _MEDICAL_KW.search(prompt):   return "medical"
    if _FINANCIAL_KW.search(prompt): return "financial"
    if _LEGAL_KW.search(prompt):     return "legal"
    return "general"

def _is_complex(prompt: str) -> bool:
    words = len(prompt.split())
    cues  = re.search(r"\b(explain|compare|analyse|why|how does|step[- ]by[- ]step|summarise)\b", prompt, re.I)
    return words > _COMPLEX_THRESHOLD or bool(cues)


class ConversationRouter:
    def __init__(self):
        self.t1 = Tier1()
        self.t2 = Tier2()
        self.t3 = Tier3()

    def handle(self, prompt: str, context: dict) -> str:
        user_id = get_active_user_id()
        session = get_twin_session(user_id) if user_id else None
        if session:
            log.debug("Personal Chameha mode — user %s", session.user_id)
            return PersonalChameha(self.t1, self.t2, self.t3).handle(prompt, context, session)
        log.debug("Public Chameha mode")
        return PublicChameha(self.t1, self.t2, self.t3).handle(prompt, context)


class PublicChameha:
    def __init__(self, t1, t2, t3):
        self.t1, self.t2, self.t3 = t1, t2, t3
        self.tone = PublicTone()

    def handle(self, prompt: str, context: dict) -> str:
        system = self.tone.system_prompt()
        if _CLOUD_PREFIX.match(prompt):
            return self.t3.infer(_CLOUD_PREFIX.sub("", prompt), system)
        if _is_complex(prompt):
            return self.t2.infer(prompt, system)
        return self.t1.infer(prompt, system)


class PersonalChameha:
    def __init__(self, t1, t2, t3):
        self.t1, self.t2, self.t3 = t1, t2, t3

    def handle(self, prompt: str, context: dict, session: TwinSessionInfo) -> str:
        twin = fetch_twin_context(session.user_id)
        if isinstance(twin, TwinUnavailable):
            log.warning("Twin unavailable (%s) — falling back to public mode", twin.reason)
            response = PublicChameha(self.t1, self.t2, self.t3).handle(prompt, context)
            return response + f"\n\n[Chameha reduced mode — twin unavailable ({twin.reason})]"

        domain = _detect_domain(prompt)
        system = self._build_system(twin, domain)
        response = self._route(prompt, system, domain)
        push_interaction(session.user_id, "user",      prompt,   domain)
        push_interaction(session.user_id, "assistant", response, domain)
        return response

    def _build_system(self, twin: TwinContext, domain: str) -> str:
        base = PersonalTone(twin).system_prompt()
        if domain in HIGH_STAKES_DOMAINS and domain in twin.safety_flags:
            base += (
                f"\n\nSAFETY OVERRIDE — domain={domain}: "
                "Append a non-dismissable disclaimer: "
                "'This is not professional medical/financial/legal advice. "
                "Consult a qualified professional before acting on this.' "
                "Flag this response for human review in the audit log."
            )
        return base

    def _route(self, prompt: str, system: str, domain: str) -> str:
        if domain in HIGH_STAKES_DOMAINS:
            log.info("Personal -> Tier 2 (high-stakes: %s)", domain)
            return self.t2.infer(prompt, system)
        if _CLOUD_PREFIX.match(prompt):
            return self.t3.infer(_CLOUD_PREFIX.sub("", prompt), system)
        if _is_complex(prompt):
            return self.t2.infer(prompt, system)
        return self.t1.infer(prompt, system)
