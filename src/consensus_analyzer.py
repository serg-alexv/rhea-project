"""
consensus_analyzer.py — Semantic consensus analysis for Rhea Tribunal

Inspired by:
  - ICE (Iterative Consensus Ensemble): models critique each other in rounds
    until convergence. +7-15% accuracy over single model. (2025)
  - LLM Council (Karpathy): Chairman model sees all responses + critiques,
    synthesizes final answer. (Dec 2025)
  - MoA (Mixture of Agents): committee of models outperforms single strong model.

Three analysis levels:
  Level 1 (local): TF-IDF cosine + Jaccard + stance heuristics. No API calls. Free.
  Level 2 (chairman): Single LLM synthesizes all responses. 1 extra API call.
  Level 3 (ICE): Iterative critique rounds until convergence. N×rounds API calls.

Usage:
    from consensus_analyzer import ConsensusAnalyzer
    analyzer = ConsensusAnalyzer(bridge=bridge)

    # Level 1: local only (free)
    report = analyzer.analyze(responses)

    # Level 2: chairman synthesis (1 extra call)
    report = analyzer.analyze(responses, mode="chairman")

    # Level 3: ICE iterative consensus (N×R extra calls)
    report = analyzer.analyze_ice(prompt, models=5, rounds=3)
"""
from __future__ import annotations

import math
import re
import string
from collections import Counter
from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ConsensusReport:
    agreement_score: float = 0.0
    confidence: float = 0.0
    consensus_text: str = ""
    agreement_points: list = field(default_factory=list)
    divergence_points: list = field(default_factory=list)
    stance_summary: dict = field(default_factory=dict)
    pairwise_similarity: dict = field(default_factory=dict)
    model_count: int = 0
    successful_count: int = 0
    analysis_method: str = "tfidf_local"
    rounds_completed: int = 0        # ICE: how many critique rounds ran
    convergence_achieved: bool = False # ICE: did responses stabilize?
    chairman_model: str = ""          # Council: which model synthesized
    round_history: list = field(default_factory=list)  # ICE: per-round snapshots
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Stop words
# ---------------------------------------------------------------------------

STOP_WORDS = frozenset(
    "a an the and or but in on at to for of is it this that with as by from "
    "are was were be been being have has had do does did will would could should "
    "may might can shall not no nor so if then than too very just about above "
    "after again all also am any because before between both each few he her "
    "here his how i its me more most my no nor now only other our out own "
    "re same she some such their them there these they through under until up "
    "we what when where which while who whom why you your".split()
)


# ---------------------------------------------------------------------------
# Text processing
# ---------------------------------------------------------------------------

def _tokenize(text: str, include_bigrams: bool = True) -> list[str]:
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    words = text.split()
    unigrams = [t for t in words if t not in STOP_WORDS and len(t) > 1]
    if not include_bigrams:
        return unigrams
    bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)
               if words[i] not in STOP_WORDS and words[i+1] not in STOP_WORDS
               and len(words[i]) > 1 and len(words[i+1]) > 1]
    return unigrams + bigrams


def _sentences(text: str) -> list[str]:
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in parts if len(s.strip()) > 10]


# ---------------------------------------------------------------------------
# TF-IDF engine
# ---------------------------------------------------------------------------

class TfIdf:
    def __init__(self):
        self.idf: dict[str, float] = {}
        self.vectors: list[dict[str, float]] = []

    def fit_transform(self, documents: list[list[str]]) -> list[dict[str, float]]:
        n_docs = len(documents)
        if n_docs == 0:
            return []
        df: Counter = Counter()
        for doc in documents:
            for term in set(doc):
                df[term] += 1
        self.idf = {t: math.log(n_docs / c) + 1.0 for t, c in df.items()}
        vectors = []
        for doc in documents:
            tf = Counter(doc)
            doc_len = len(doc) if doc else 1
            vec = {t: (c / doc_len) * self.idf.get(t, 1.0) for t, c in tf.items()}
            vectors.append(vec)
        self.vectors = vectors
        return vectors


def _cosine_similarity(v1: dict[str, float], v2: dict[str, float]) -> float:
    if not v1 or not v2:
        return 0.0
    common = set(v1.keys()) & set(v2.keys())
    dot = sum(v1[k] * v2[k] for k in common)
    mag1 = math.sqrt(sum(v * v for v in v1.values()))
    mag2 = math.sqrt(sum(v * v for v in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def _jaccard_similarity(tokens1: list[str], tokens2: list[str]) -> float:
    s1, s2 = set(tokens1), set(tokens2)
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


def _blended_similarity(cosine: float, jaccard: float, w: float = 0.6) -> float:
    return w * cosine + (1 - w) * jaccard


# ---------------------------------------------------------------------------
# Stance detection
# ---------------------------------------------------------------------------

AFFIRMATIVE_SIGNALS = [
    "yes", "agree", "recommend", "should", "correct", "true",
    "support", "beneficial", "effective", "absolutely", "definitely",
    "indeed", "certainly", "strongly recommend", "best practice",
    "evidence supports", "research shows", "studies confirm",
]

NEGATIVE_SIGNALS = [
    "no", "disagree", "should not", "shouldn't", "avoid", "incorrect",
    "false", "not recommend", "against", "harmful", "ineffective",
    "don't", "do not", "risky", "dangerous", "caution against",
    "evidence against", "not supported",
]

QUALIFIED_SIGNALS = [
    "however", "depends", "it depends", "context", "nuanced",
    "on one hand", "on the other", "with caveats", "conditionally",
    "in some cases", "not always", "varies", "mixed evidence",
    "both", "trade-off", "tradeoff", "pros and cons",
]


def _detect_stance(text: str) -> dict:
    text_lower = text.lower()
    word_count = len(text_lower.split())
    if word_count == 0:
        return {"stance": "empty", "affirmative": 0, "negative": 0, "qualified": 0}
    aff = sum(1 for s in AFFIRMATIVE_SIGNALS if s in text_lower)
    neg = sum(1 for s in NEGATIVE_SIGNALS if s in text_lower)
    qual = sum(1 for s in QUALIFIED_SIGNALS if s in text_lower)
    lf = min(word_count / 200, 3.0)
    if lf > 0:
        aff, neg, qual = aff / lf, neg / lf, qual / lf
    total = aff + neg + qual
    if total == 0:
        stance = "neutral"
    elif qual > aff and qual > neg:
        stance = "qualified"
    elif aff > neg:
        stance = "affirmative"
    elif neg > aff:
        stance = "negative"
    else:
        stance = "mixed"
    return {"stance": stance, "affirmative": round(aff, 3),
            "negative": round(neg, 3), "qualified": round(qual, 3)}


# ---------------------------------------------------------------------------
# Agreement / divergence detection
# ---------------------------------------------------------------------------

def _find_agreement_divergence(
    model_ids: list[str], texts: list[str],
    threshold_agree: float = 0.3, threshold_diverge: float = 0.15,
) -> tuple[list[str], list[str]]:
    if len(texts) < 2:
        return [], []
    all_sents = []
    for mid, text in zip(model_ids, texts):
        for sent in _sentences(text):
            tokens = _tokenize(sent)
            if len(tokens) >= 3:
                all_sents.append((mid, sent, tokens))
    if len(all_sents) < 2:
        return [], []
    tfidf = TfIdf()
    vectors = tfidf.fit_transform([s[2] for s in all_sents])

    agreement_candidates = []
    for i in range(len(all_sents)):
        for j in range(i + 1, len(all_sents)):
            if all_sents[i][0] == all_sents[j][0]:
                continue
            sim = _cosine_similarity(vectors[i], vectors[j])
            if sim >= threshold_agree:
                agreement_candidates.append(
                    (all_sents[i][1], all_sents[j][1], sim,
                     all_sents[i][0], all_sents[j][0]))

    agreement_candidates.sort(key=lambda x: x[2], reverse=True)
    seen, agreement_points = set(), []
    for sa, sb, sim, ma, mb in agreement_candidates[:10]:
        key = " ".join(_tokenize(sa)[:5])
        if key not in seen:
            seen.add(key)
            rep = sa if len(sa) <= len(sb) else sb
            agreement_points.append(f"[{ma}, {mb}] {rep}")
            if len(agreement_points) >= 5:
                break

    divergence_candidates = []
    for i, (mi, si, ti) in enumerate(all_sents):
        max_sim = 0.0
        for j, (mj, sj, tj) in enumerate(all_sents):
            if mi == mj:
                continue
            max_sim = max(max_sim, _cosine_similarity(vectors[i], vectors[j]))
        if max_sim < threshold_diverge and len(ti) >= 5:
            divergence_candidates.append((max_sim, mi, si))

    divergence_candidates.sort(key=lambda x: x[0])
    seen_d, divergence_points = set(), []
    for _, mid, sent in divergence_candidates[:10]:
        key = " ".join(_tokenize(sent)[:5])
        if key not in seen_d:
            seen_d.add(key)
            divergence_points.append(f"[{mid} only] {sent}")
            if len(divergence_points) >= 5:
                break
    return agreement_points, divergence_points


# ---------------------------------------------------------------------------
# Local synthesis (Level 1 — free, no API calls)
# ---------------------------------------------------------------------------

def _synthesize_local(
    model_ids, texts, stances, agreement_score, agreement_pts, divergence_pts,
) -> str:
    n = len(model_ids)
    if n == 0:
        return "No responses to analyze."
    if agreement_score >= 0.7:
        strength = "Strong consensus"
    elif agreement_score >= 0.4:
        strength = "Moderate consensus"
    elif agreement_score >= 0.2:
        strength = "Weak consensus"
    else:
        strength = "No clear consensus"
    parts = [f"{strength} across {n} models (agreement: {agreement_score:.0%})."]
    stance_dist = Counter(stances[m]["stance"] for m in model_ids)
    if len(stance_dist) == 1:
        parts.append(f"All models take a {list(stance_dist.keys())[0]} position.")
    else:
        dist_str = ", ".join(f"{k}: {v}/{n}" for k, v in stance_dist.most_common())
        parts.append(f"Stance distribution: {dist_str}.")
    if agreement_pts:
        parts.append("\nKey areas of agreement:")
        for pt in agreement_pts[:3]:
            parts.append(f"  - {pt}")
    if divergence_pts:
        parts.append("\nKey areas of divergence:")
        for pt in divergence_pts[:3]:
            parts.append(f"  - {pt}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Chairman synthesis (Level 2 — Karpathy Council pattern)
# ---------------------------------------------------------------------------

CHAIRMAN_PROMPT = """You are the Chairman of an AI model council. {n} models independently answered the same question. You see ALL their responses below.

Your job: resolve conflicts, merge the best insights, produce ONE definitive answer.

ORIGINAL QUESTION:
{question}

MODEL RESPONSES:
{responses}

{critique_section}

Instructions:
1. Identify what the majority agrees on (CONSENSUS POINTS)
2. Identify meaningful disagreements (DISSENT POINTS — name which model dissents and why)
3. Resolve each disagreement by evaluating the strength of evidence on each side
4. Produce a FINAL SYNTHESIS that incorporates the strongest arguments from all models
5. Rate your confidence 0-100

Format your response exactly as:
CONSENSUS POINTS:
- [point]

DISSENT POINTS:
- [model]: [dissenting view] — RESOLUTION: [your judgment]

CONFIDENCE: [0-100]

FINAL SYNTHESIS:
[one paragraph, max 150 words, combining the strongest insights]"""


def _chairman_synthesize(
    model_ids: list[str],
    texts: list[str],
    prompt: str,
    bridge,
    tier: str = "cheap",
    critiques: list[dict] = None,
) -> tuple[str, str]:
    """Chairman model sees all responses (+ optional critiques) and synthesizes.

    Returns (synthesis_text, chairman_model_id).
    """
    response_block = ""
    for mid, text in zip(model_ids, texts):
        truncated = text[:600] + ("..." if len(text) > 600 else "")
        response_block += f"\n### {mid}\n{truncated}\n"

    critique_section = ""
    if critiques:
        critique_section = "\nCRITIQUES FROM PREVIOUS ROUND:\n"
        for c in critiques:
            critique_section += f"\n### {c['critic']} critiquing {c['target']}:\n{c['text'][:400]}\n"

    chairman_prompt = CHAIRMAN_PROMPT.format(
        n=len(model_ids),
        question=prompt[:500],
        responses=response_block,
        critique_section=critique_section,
    )

    try:
        resp = bridge.ask_tier(
            tier, chairman_prompt,
            system="You are a precise, authoritative consensus synthesizer. No hedging. Resolve disagreements decisively.",
        )
        if resp.error:
            return "", ""
        chairman_id = f"{resp.provider}/{resp.model}"
        return resp.text, chairman_id
    except Exception:
        return "", ""


# ---------------------------------------------------------------------------
# ICE: Iterative Consensus Ensemble (Level 3)
# ---------------------------------------------------------------------------

ICE_CRITIQUE_PROMPT = """You previously answered a question. Now you see how OTHER models answered the same question.

ORIGINAL QUESTION:
{question}

YOUR PREVIOUS ANSWER:
{own_answer}

OTHER MODELS' ANSWERS:
{other_answers}

Instructions:
1. Compare your answer with the others
2. Identify where you AGREE with the majority
3. Identify where you DISAGREE and explain WHY (with evidence)
4. If another model made a stronger argument than yours, ADOPT it
5. Produce your REVISED ANSWER incorporating the best insights from all models

Keep your revised answer under 200 words. Be specific. Cite evidence."""


def _ice_critique_round(
    prompt: str,
    model_ids: list[str],
    current_texts: list[str],
    bridge,
    tier: str = "cheap",
) -> tuple[list[str], list[dict]]:
    """Run one ICE critique round: each model sees others' answers and revises.

    Returns (revised_texts, critiques_metadata).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    revised = [None] * len(model_ids)
    critiques = []

    def critique_one(idx):
        mid = model_ids[idx]
        own = current_texts[idx]
        others_block = ""
        for j, (other_mid, other_text) in enumerate(zip(model_ids, current_texts)):
            if j == idx:
                continue
            truncated = other_text[:400] + ("..." if len(other_text) > 400 else "")
            others_block += f"\n### {other_mid}\n{truncated}\n"

        ice_prompt = ICE_CRITIQUE_PROMPT.format(
            question=prompt[:300],
            own_answer=own[:500],
            other_answers=others_block,
        )

        try:
            resp = bridge.ask(ice_prompt, mid,
                              system="You are refining your answer based on peer review. Be honest about what others got right.",
                              max_tokens=1024)
            if resp.error:
                return idx, own, {"critic": mid, "target": "all", "text": f"[error: {resp.error}]"}
            return idx, resp.text, {"critic": mid, "target": "all", "text": resp.text[:200]}
        except Exception as e:
            return idx, own, {"critic": mid, "target": "all", "text": f"[error: {e}]"}

    with ThreadPoolExecutor(max_workers=min(len(model_ids), 10)) as pool:
        futures = {pool.submit(critique_one, i): i for i in range(len(model_ids))}
        for future in as_completed(futures):
            idx, new_text, critique = future.result()
            revised[idx] = new_text
            critiques.append(critique)

    return revised, critiques


def _measure_convergence(prev_texts: list[str], curr_texts: list[str]) -> float:
    """Measure how much responses changed between rounds. 0 = identical, 1 = completely different."""
    if len(prev_texts) != len(curr_texts):
        return 1.0
    similarities = []
    for prev, curr in zip(prev_texts, curr_texts):
        prev_tok = _tokenize(prev)
        curr_tok = _tokenize(curr)
        if not prev_tok or not curr_tok:
            similarities.append(0.0)
            continue
        tfidf = TfIdf()
        vecs = tfidf.fit_transform([prev_tok, curr_tok])
        similarities.append(_cosine_similarity(vecs[0], vecs[1]))
    avg_sim = sum(similarities) / len(similarities) if similarities else 0.0
    return 1.0 - avg_sim  # delta: 0 = converged, 1 = diverged


# ---------------------------------------------------------------------------
# Core analysis (shared by all levels)
# ---------------------------------------------------------------------------

def _core_analysis(
    model_ids: list[str], texts: list[str],
) -> dict:
    """Run TF-IDF, stance, agreement/divergence on a set of responses. Returns dict of metrics."""
    tokenized = [_tokenize(text) for text in texts]
    tfidf = TfIdf()
    vectors = tfidf.fit_transform(tokenized)

    similarities, sim_values = {}, []
    for i in range(len(model_ids)):
        for j in range(i + 1, len(model_ids)):
            cosine = _cosine_similarity(vectors[i], vectors[j])
            jaccard = _jaccard_similarity(tokenized[i], tokenized[j])
            blended = _blended_similarity(cosine, jaccard)
            key = f"{model_ids[i]} vs {model_ids[j]}"
            similarities[key] = round(blended, 4)
            sim_values.append(blended)

    raw_text_sim = sum(sim_values) / len(sim_values) if sim_values else 0.0

    stances = {mid: _detect_stance(text) for mid, text in zip(model_ids, texts)}
    stance_values = [s["stance"] for s in stances.values()]
    stance_counts = Counter(stance_values)
    dominant_count = max(stance_counts.values()) if stance_counts else 0
    stance_alignment = dominant_count / len(stance_values) if stance_values else 0.0

    agreement_pts, divergence_pts = _find_agreement_divergence(model_ids, texts)
    total_pts = len(agreement_pts) + len(divergence_pts)
    claim_overlap = len(agreement_pts) / total_pts if total_pts > 0 else 0.5

    calibrated_text = min(max((raw_text_sim - 0.03) / 0.25, 0.0), 1.0)
    agreement_score = round(0.35 * calibrated_text + 0.40 * stance_alignment + 0.25 * claim_overlap, 4)

    n = len(model_ids)
    model_factor = min(n / 5, 1.0)
    confidence = round(0.3 * model_factor + 0.4 * agreement_score + 0.3 * stance_alignment, 4)

    return {
        "similarities": similarities,
        "stances": stances,
        "stance_alignment": stance_alignment,
        "agreement_pts": agreement_pts,
        "divergence_pts": divergence_pts,
        "agreement_score": agreement_score,
        "confidence": confidence,
        "vocab_size": len(tfidf.idf),
        "tokenized": tokenized,
    }


# ---------------------------------------------------------------------------
# Main analyzer
# ---------------------------------------------------------------------------

class ConsensusAnalyzer:
    """Multi-level consensus analyzer for Rhea Tribunal.

    Level 1 (local): TF-IDF + stance heuristics. Free.
    Level 2 (chairman): + Karpathy Council chairman synthesis. 1 API call.
    Level 3 (ICE): + Iterative critique rounds. N×rounds API calls.
    """

    def __init__(self, bridge=None):
        self.bridge = bridge

    def analyze(
        self,
        responses: list[tuple[str, str]],
        prompt: str = "",
        mode: str = "local",
        llm_tier: str = "cheap",
    ) -> ConsensusReport:
        """Analyze pre-collected responses.

        Args:
            responses: List of (model_id, response_text) tuples.
            prompt: Original question.
            mode: "local" (L1), "chairman" (L2), or "ice" (L3 — use analyze_ice for full ICE).
            llm_tier: Cost tier for chairman/ICE synthesis.
        """
        report = ConsensusReport()
        valid = [(mid, text) for mid, text in responses if text and len(text.strip()) > 10]
        report.model_count = len(responses)
        report.successful_count = len(valid)

        if len(valid) < 2:
            report.consensus_text = f"Insufficient responses ({len(valid)}/{len(responses)} valid)."
            report.confidence = 0.0
            return report

        model_ids = [mid for mid, _ in valid]
        texts = [text for _, text in valid]

        # Core analysis (all levels)
        core = _core_analysis(model_ids, texts)
        report.pairwise_similarity = core["similarities"]
        report.stance_summary = core["stances"]
        report.agreement_points = core["agreement_pts"]
        report.divergence_points = core["divergence_pts"]
        report.agreement_score = core["agreement_score"]
        report.confidence = core["confidence"]
        report.meta = {
            "vocab_size": core["vocab_size"],
            "avg_response_length": round(sum(len(t) for t in texts) / len(texts)),
            "avg_token_count": round(sum(len(t) for t in core["tokenized"]) / len(core["tokenized"])),
        }

        # Level 1: local synthesis
        if mode == "local" or not self.bridge:
            report.analysis_method = "tfidf_local"
            report.consensus_text = _synthesize_local(
                model_ids, texts, core["stances"],
                core["agreement_score"], core["agreement_pts"], core["divergence_pts"],
            )
            return report

        # Level 2: chairman synthesis (Karpathy Council)
        if mode == "chairman":
            synthesis, chairman_id = _chairman_synthesize(
                model_ids, texts, prompt, self.bridge, llm_tier,
            )
            if synthesis:
                report.consensus_text = synthesis
                report.chairman_model = chairman_id
                report.analysis_method = "tfidf + chairman_council"
            else:
                report.analysis_method = "tfidf_local (chairman failed)"
                report.consensus_text = _synthesize_local(
                    model_ids, texts, core["stances"],
                    core["agreement_score"], core["agreement_pts"], core["divergence_pts"],
                )
            return report

        # For ICE mode on pre-collected responses, use chairman as fallback
        report.analysis_method = "tfidf_local"
        report.consensus_text = _synthesize_local(
            model_ids, texts, core["stances"],
            core["agreement_score"], core["agreement_pts"], core["divergence_pts"],
        )
        return report

    def analyze_ice(
        self,
        prompt: str,
        k: int = 5,
        rounds: int = 3,
        tier: str = "cheap",
        convergence_threshold: float = 0.15,
        chairman_tier: str = "balanced",
    ) -> ConsensusReport:
        """Full ICE pipeline: query → critique rounds → chairman synthesis.

        This is the premium Tribunal API endpoint.
        Cost: k initial calls + k×rounds critique calls + 1 chairman call.

        Args:
            prompt: The question to tribunal.
            k: Number of models to query.
            rounds: Max critique rounds (ICE paper: 2-3 is optimal).
            tier: Cost tier for initial query + critiques.
            convergence_threshold: Stop if inter-round delta < this.
            chairman_tier: Cost tier for final chairman synthesis.
        """
        if not self.bridge:
            raise ValueError("ICE mode requires a RheaBridge instance")

        report = ConsensusReport()
        report.analysis_method = f"ice_{rounds}rounds + chairman"

        # --- Round 0: Initial parallel query (standard tribunal) ---
        tribunal_result = self.bridge.tribunal(prompt, k=k, tier=tier)
        model_ids = []
        current_texts = []
        for r in tribunal_result.responses:
            mid = f"{r.provider}/{r.model}" if r.provider else r.model
            if not r.error and r.text:
                model_ids.append(mid)
                current_texts.append(r.text)

        report.model_count = len(tribunal_result.responses)
        report.successful_count = len(model_ids)

        if len(model_ids) < 2:
            report.consensus_text = f"Insufficient responses ({len(model_ids)} valid)."
            return report

        # Snapshot round 0
        round0_core = _core_analysis(model_ids, current_texts)
        report.round_history.append({
            "round": 0,
            "type": "initial",
            "agreement_score": round0_core["agreement_score"],
            "confidence": round0_core["confidence"],
        })

        # --- Rounds 1..N: ICE critique loops ---
        all_critiques = []
        for r in range(1, rounds + 1):
            prev_texts = list(current_texts)

            revised_texts, critiques = _ice_critique_round(
                prompt, model_ids, current_texts, self.bridge, tier,
            )
            current_texts = revised_texts
            all_critiques.extend(critiques)

            # Measure convergence
            delta = _measure_convergence(prev_texts, current_texts)
            round_core = _core_analysis(model_ids, current_texts)

            report.round_history.append({
                "round": r,
                "type": "critique",
                "agreement_score": round_core["agreement_score"],
                "confidence": round_core["confidence"],
                "delta": round(delta, 4),
            })
            report.rounds_completed = r

            # Convergence check: if responses barely changed, stop early
            if delta < convergence_threshold:
                report.convergence_achieved = True
                break

        # --- Final analysis on converged responses ---
        final_core = _core_analysis(model_ids, current_texts)
        report.pairwise_similarity = final_core["similarities"]
        report.stance_summary = final_core["stances"]
        report.agreement_points = final_core["agreement_pts"]
        report.divergence_points = final_core["divergence_pts"]
        report.agreement_score = final_core["agreement_score"]
        report.confidence = final_core["confidence"]
        report.meta = {
            "vocab_size": final_core["vocab_size"],
            "avg_response_length": round(sum(len(t) for t in current_texts) / len(current_texts)),
            "initial_agreement": round0_core["agreement_score"],
            "final_agreement": final_core["agreement_score"],
            "agreement_delta": round(final_core["agreement_score"] - round0_core["agreement_score"], 4),
            "total_api_calls": len(model_ids) + len(model_ids) * report.rounds_completed + 1,
        }

        # --- Chairman synthesis on final converged responses ---
        synthesis, chairman_id = _chairman_synthesize(
            model_ids, current_texts, prompt, self.bridge,
            tier=chairman_tier, critiques=all_critiques[-len(model_ids):],
        )
        if synthesis:
            report.consensus_text = synthesis
            report.chairman_model = chairman_id
        else:
            report.consensus_text = _synthesize_local(
                model_ids, current_texts, final_core["stances"],
                final_core["agreement_score"], final_core["agreement_pts"],
                final_core["divergence_pts"],
            )

        return report


# ---------------------------------------------------------------------------
# Bridge integration convenience
# ---------------------------------------------------------------------------

def analyze_tribunal_responses(
    tribunal_result,
    prompt: str = "",
    bridge=None,
    mode: str = "local",
) -> ConsensusReport:
    """Analyze a TribunalResult from rhea_bridge.py."""
    if not prompt:
        prompt = tribunal_result.prompt
    responses = []
    for r in tribunal_result.responses:
        model_id = f"{r.provider}/{r.model}" if r.provider else r.model
        responses.append((model_id, r.text if not r.error else ""))
    analyzer = ConsensusAnalyzer(bridge=bridge)
    return analyzer.analyze(responses, prompt=prompt, mode=mode)


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

def _demo():
    print("=== Consensus Analyzer v2 Demo (ICE + Council) ===\n")

    responses = [
        ("openai/gpt-4o", (
            "Cold showers can be beneficial for morning alertness and mood. "
            "Research shows cold exposure activates the sympathetic nervous system, "
            "increasing norepinephrine by up to 530%. For ADHD individuals, this "
            "dopamine boost can improve focus. However, start gradually with 30-second "
            "cold bursts. The polyvagal theory suggests sudden cold can trigger a "
            "freeze response in some individuals, so individual tolerance matters."
        )),
        ("gemini/gemini-2.0-flash", (
            "Morning cold exposure has strong evidence for increasing alertness and "
            "dopamine levels. A 2023 meta-analysis found cold water immersion "
            "increases circulating norepinephrine by 200-530%. For individuals "
            "with ADHD, this is particularly relevant as dopamine regulation is "
            "a core deficit. Recommendation: start with 15-30 seconds of cold "
            "at the end of a warm shower. Contraindicated for those with "
            "cardiovascular conditions."
        )),
        ("deepseek/deepseek-chat", (
            "Cold showers in the morning are generally beneficial. The cold "
            "exposure triggers a hormetic stress response that increases "
            "norepinephrine and dopamine. This can help with focus and energy, "
            "especially relevant for ADHD. The key is gradual adaptation — "
            "start with lukewarm and progressively decrease temperature. "
            "Cold showers also improve cold tolerance and may support immune "
            "function, though evidence for the latter is mixed."
        )),
        ("openrouter/mistral-large", (
            "I would not universally recommend cold showers. While there is "
            "evidence for norepinephrine increase, the stress response can be "
            "counterproductive for individuals with anxiety or dysautonomia. "
            "The polyvagal perspective suggests that forced cold exposure may "
            "push some people into a sympathetic overdrive state rather than "
            "the ventral vagal calm needed for focus. A better alternative "
            "might be face-only cold water exposure, which activates the "
            "dive reflex without full-body stress."
        )),
        ("azure/gpt-4o-mini", (
            "Cold showers can increase alertness through norepinephrine release. "
            "The scientific evidence supports short cold exposure (30-90 seconds) "
            "for mood and energy benefits. For ADHD, the dopamine connection is "
            "promising. However, this should be one tool among many, not a "
            "silver bullet. Individual variation is significant — some people "
            "find cold showers invigorating while others find them deeply "
            "unpleasant and counterproductive to routine adherence."
        )),
    ]

    prompt = "Should you take cold showers in the morning for ADHD management?"

    # Level 1: local
    analyzer = ConsensusAnalyzer()
    report = analyzer.analyze(responses, prompt=prompt, mode="local")

    print(f"[Level 1: Local]")
    print(f"Agreement: {report.agreement_score:.1%} | Confidence: {report.confidence:.1%}")
    print(f"Method: {report.analysis_method}")
    print(f"\n{report.consensus_text}")

    print(f"\n--- Pairwise Similarity ---")
    for pair, sim in sorted(report.pairwise_similarity.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(sim * 30)
        print(f"  {pair:50s} {sim:.3f} {bar}")

    print(f"\n--- Stances ---")
    for model, stance in report.stance_summary.items():
        print(f"  {model:35s} → {stance['stance']}")

    print(f"\n--- Round History ---")
    for rh in report.round_history:
        print(f"  Round {rh['round']}: agreement={rh.get('agreement_score','N/A')}")

    print(f"\n[Level 2/3 require bridge — pass bridge=RheaBridge() to enable]")
    print(f"  analyzer.analyze(responses, mode='chairman')  # +1 API call")
    print(f"  analyzer.analyze_ice(prompt, k=5, rounds=3)   # +k*rounds+1 API calls")


if __name__ == "__main__":
    _demo()
