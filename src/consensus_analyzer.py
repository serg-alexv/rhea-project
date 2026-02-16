"""
consensus_analyzer.py — Semantic consensus analysis for Rhea Tribunal

Analyzes N model responses to the same prompt and produces:
- Agreement score (0.0–1.0): how much do models agree?
- Confidence rating (0.0–1.0): how reliable is the consensus?
- Divergence points: where models disagree
- Agreement points: where models converge
- Pairwise similarity matrix
- Stance classification per model
- Synthesized consensus text

Two analysis modes:
  Level 1 (local): TF-IDF cosine similarity + stance heuristics. No API calls.
  Level 2 (LLM-assisted): Uses a cheap model to synthesize. Requires bridge.

Usage:
    from consensus_analyzer import ConsensusAnalyzer
    analyzer = ConsensusAnalyzer()
    report = analyzer.analyze(responses)  # list of (model_id, response_text)
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
    agreement_score: float = 0.0           # 0.0–1.0, avg pairwise similarity
    confidence: float = 0.0                # 0.0–1.0, how reliable this analysis is
    consensus_text: str = ""               # synthesized consensus statement
    agreement_points: list = field(default_factory=list)   # shared claims/positions
    divergence_points: list = field(default_factory=list)  # disagreements
    stance_summary: dict = field(default_factory=dict)     # model → stance label
    pairwise_similarity: dict = field(default_factory=dict) # "modelA vs modelB" → score
    model_count: int = 0
    successful_count: int = 0
    analysis_method: str = "tfidf_local"
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Stop words (minimal set — no NLTK dependency)
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
# Text processing utilities
# ---------------------------------------------------------------------------

def _tokenize(text: str, include_bigrams: bool = True) -> list[str]:
    """Lowercase, strip punctuation, split into tokens, remove stop words.

    With bigrams enabled, captures multi-word concepts like
    'cold exposure', 'norepinephrine increase', etc.
    """
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
    """Split text into sentences. Handles common abbreviations."""
    # Split on sentence-ending punctuation followed by space or end
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in parts if len(s.strip()) > 10]


def _ngrams(tokens: list[str], n: int = 2) -> list[str]:
    """Generate n-grams from token list."""
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


# ---------------------------------------------------------------------------
# TF-IDF engine (pure Python, no numpy/sklearn)
# ---------------------------------------------------------------------------

class TfIdf:
    """Minimal TF-IDF implementation. No external dependencies."""

    def __init__(self):
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.vectors: list[dict[str, float]] = []

    def fit_transform(self, documents: list[list[str]]) -> list[dict[str, float]]:
        """Build vocabulary, compute IDF, return TF-IDF vectors (sparse dicts)."""
        n_docs = len(documents)
        if n_docs == 0:
            return []

        # Build vocab + document frequency
        df: Counter = Counter()
        for doc in documents:
            unique_terms = set(doc)
            for term in unique_terms:
                df[term] += 1

        # IDF: log(N / df) + 1 (smoothed)
        self.idf = {
            term: math.log(n_docs / count) + 1.0
            for term, count in df.items()
        }

        # TF-IDF vectors
        vectors = []
        for doc in documents:
            tf = Counter(doc)
            doc_len = len(doc) if doc else 1
            vec = {}
            for term, count in tf.items():
                tf_val = count / doc_len  # normalized TF
                idf_val = self.idf.get(term, 1.0)
                vec[term] = tf_val * idf_val
            vectors.append(vec)

        self.vectors = vectors
        return vectors


def _cosine_similarity(v1: dict[str, float], v2: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors (dicts)."""
    if not v1 or not v2:
        return 0.0

    common_keys = set(v1.keys()) & set(v2.keys())
    dot = sum(v1[k] * v2[k] for k in common_keys)
    mag1 = math.sqrt(sum(v * v for v in v1.values()))
    mag2 = math.sqrt(sum(v * v for v in v2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot / (mag1 * mag2)


def _jaccard_similarity(tokens1: list[str], tokens2: list[str]) -> float:
    """Jaccard index between two token sets. Captures vocabulary overlap."""
    s1, s2 = set(tokens1), set(tokens2)
    if not s1 or not s2:
        return 0.0
    intersection = len(s1 & s2)
    union = len(s1 | s2)
    return intersection / union if union > 0 else 0.0


def _blended_similarity(
    cosine: float,
    jaccard: float,
    cosine_weight: float = 0.6,
) -> float:
    """Blend cosine and Jaccard for more robust similarity scoring.

    Cosine captures TF-IDF-weighted overlap (content similarity).
    Jaccard captures raw vocabulary overlap (topic similarity).
    """
    return cosine_weight * cosine + (1 - cosine_weight) * jaccard


# ---------------------------------------------------------------------------
# Stance detection (heuristic)
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
    "evidence against", "studies show.*negative", "not supported",
]

QUALIFIED_SIGNALS = [
    "however", "depends", "it depends", "context", "nuanced",
    "on one hand", "on the other", "with caveats", "conditionally",
    "in some cases", "not always", "varies", "mixed evidence",
    "both", "trade-off", "tradeoff", "pros and cons",
]


def _detect_stance(text: str) -> dict:
    """Classify response stance as affirmative/negative/qualified with scores."""
    text_lower = text.lower()
    word_count = len(text_lower.split())
    if word_count == 0:
        return {"stance": "empty", "affirmative": 0, "negative": 0, "qualified": 0}

    aff_score = sum(1 for s in AFFIRMATIVE_SIGNALS if s in text_lower)
    neg_score = sum(1 for s in NEGATIVE_SIGNALS if s in text_lower)
    qual_score = sum(1 for s in QUALIFIED_SIGNALS if s in text_lower)

    # Normalize by response length (longer responses naturally hit more keywords)
    length_factor = min(word_count / 200, 3.0)  # cap at 3x for very long responses
    if length_factor > 0:
        aff_score = aff_score / length_factor
        neg_score = neg_score / length_factor
        qual_score = qual_score / length_factor

    total = aff_score + neg_score + qual_score
    if total == 0:
        stance = "neutral"
    elif qual_score > aff_score and qual_score > neg_score:
        stance = "qualified"
    elif aff_score > neg_score:
        stance = "affirmative"
    elif neg_score > aff_score:
        stance = "negative"
    else:
        stance = "mixed"

    return {
        "stance": stance,
        "affirmative": round(aff_score, 3),
        "negative": round(neg_score, 3),
        "qualified": round(qual_score, 3),
    }


# ---------------------------------------------------------------------------
# Key claim extraction
# ---------------------------------------------------------------------------

def _extract_key_claims(text: str, top_n: int = 5) -> list[str]:
    """Extract the most information-dense sentences from a response."""
    sents = _sentences(text)
    if not sents:
        return []

    # Score sentences by information density:
    # - longer sentences (up to a point) carry more info
    # - sentences with numbers/data are more substantive
    # - sentences with hedging language are less decisive
    scored = []
    for sent in sents:
        words = sent.split()
        length_score = min(len(words) / 20, 1.0)  # favor 20+ word sentences
        data_score = 0.3 if re.search(r'\d+', sent) else 0.0  # has numbers
        list_penalty = -0.2 if sent.startswith(('-', '*', '•')) else 0.0
        score = length_score + data_score + list_penalty
        scored.append((score, sent))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:top_n]]


# ---------------------------------------------------------------------------
# Agreement / divergence detection
# ---------------------------------------------------------------------------

def _find_agreement_divergence(
    model_ids: list[str],
    texts: list[str],
    threshold_agree: float = 0.3,
    threshold_diverge: float = 0.15,
) -> tuple[list[str], list[str]]:
    """Find agreement points (sentences similar across models) and divergence points.

    Uses sentence-level TF-IDF matching across all response pairs.
    """
    if len(texts) < 2:
        return [], []

    # Collect all sentences with their source model
    all_sents = []  # (model_id, sentence, tokens)
    for mid, text in zip(model_ids, texts):
        for sent in _sentences(text):
            tokens = _tokenize(sent)
            if len(tokens) >= 3:  # skip trivially short sentences
                all_sents.append((mid, sent, tokens))

    if len(all_sents) < 2:
        return [], []

    # Build TF-IDF on all sentences
    tfidf = TfIdf()
    vectors = tfidf.fit_transform([s[2] for s in all_sents])

    # Find cross-model sentence pairs with high similarity
    agreement_candidates = []
    divergence_candidates = []

    for i in range(len(all_sents)):
        for j in range(i + 1, len(all_sents)):
            if all_sents[i][0] == all_sents[j][0]:
                continue  # skip same-model pairs

            sim = _cosine_similarity(vectors[i], vectors[j])
            pair = (all_sents[i][1], all_sents[j][1], sim, all_sents[i][0], all_sents[j][0])

            if sim >= threshold_agree:
                agreement_candidates.append(pair)

    # Agreement: pick top cross-model matches
    agreement_candidates.sort(key=lambda x: x[2], reverse=True)
    seen_agreement = set()
    agreement_points = []
    for sent_a, sent_b, sim, mid_a, mid_b in agreement_candidates[:10]:
        # Deduplicate by checking if we already captured this idea
        key_a = " ".join(_tokenize(sent_a)[:5])
        if key_a not in seen_agreement:
            seen_agreement.add(key_a)
            # Use the shorter sentence as the representative
            rep = sent_a if len(sent_a) <= len(sent_b) else sent_b
            agreement_points.append(f"[{mid_a}, {mid_b}] {rep}")
            if len(agreement_points) >= 5:
                break

    # Divergence: find claims in one model not matched in any other
    for i, (mid_i, sent_i, tok_i) in enumerate(all_sents):
        max_cross_sim = 0.0
        for j, (mid_j, sent_j, tok_j) in enumerate(all_sents):
            if mid_i == mid_j:
                continue
            sim = _cosine_similarity(vectors[i], vectors[j])
            max_cross_sim = max(max_cross_sim, sim)

        if max_cross_sim < threshold_diverge and len(tok_i) >= 5:
            divergence_candidates.append((max_cross_sim, mid_i, sent_i))

    divergence_candidates.sort(key=lambda x: x[0])
    divergence_points = []
    seen_div = set()
    for _, mid, sent in divergence_candidates[:10]:
        key = " ".join(_tokenize(sent)[:5])
        if key not in seen_div:
            seen_div.add(key)
            divergence_points.append(f"[{mid} only] {sent}")
            if len(divergence_points) >= 5:
                break

    return agreement_points, divergence_points


# ---------------------------------------------------------------------------
# Consensus text synthesis (local — no LLM call)
# ---------------------------------------------------------------------------

def _synthesize_consensus_local(
    model_ids: list[str],
    texts: list[str],
    stances: dict[str, dict],
    agreement_score: float,
    agreement_points: list[str],
    divergence_points: list[str],
) -> str:
    """Generate a human-readable consensus summary without any API calls."""
    n = len(model_ids)
    if n == 0:
        return "No responses to analyze."

    # Classify overall consensus type
    stance_counts = Counter(s["stance"] for s in stances.values())
    dominant_stance = stance_counts.most_common(1)[0] if stance_counts else ("neutral", 0)

    if agreement_score >= 0.7:
        strength = "Strong consensus"
    elif agreement_score >= 0.4:
        strength = "Moderate consensus"
    elif agreement_score >= 0.2:
        strength = "Weak consensus"
    else:
        strength = "No clear consensus"

    # Build synthesis
    parts = []
    parts.append(f"{strength} across {n} models (agreement: {agreement_score:.0%}).")

    # Stance distribution
    stance_labels = [f"{stances[m]['stance']}" for m in model_ids]
    stance_dist = Counter(stance_labels)
    if len(stance_dist) == 1:
        parts.append(f"All models take a {list(stance_dist.keys())[0]} position.")
    else:
        dist_str = ", ".join(f"{k}: {v}/{n}" for k, v in stance_dist.most_common())
        parts.append(f"Stance distribution: {dist_str}.")

    # Agreement highlights
    if agreement_points:
        parts.append("\nKey areas of agreement:")
        for pt in agreement_points[:3]:
            parts.append(f"  - {pt}")

    # Divergence highlights
    if divergence_points:
        parts.append("\nKey areas of divergence:")
        for pt in divergence_points[:3]:
            parts.append(f"  - {pt}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# LLM-assisted synthesis (Level 2 — requires bridge)
# ---------------------------------------------------------------------------

def _synthesize_consensus_llm(
    model_ids: list[str],
    texts: list[str],
    prompt: str,
    bridge,
    tier: str = "cheap",
) -> str:
    """Use a cheap model to produce a meta-synthesis of tribunal responses.

    This is the premium analysis tier for Tribunal API.
    Returns the model's synthesis or falls back to local if the call fails.
    """
    response_block = ""
    for mid, text in zip(model_ids, texts):
        # Truncate each response to ~500 chars for the meta-prompt
        truncated = text[:500] + ("..." if len(text) > 500 else "")
        response_block += f"\n### {mid}\n{truncated}\n"

    meta_prompt = f"""You are a consensus analyzer. {len(model_ids)} AI models were asked the same question. Analyze their responses and produce a structured consensus.

ORIGINAL QUESTION:
{prompt[:300]}

MODEL RESPONSES:
{response_block}

Produce a concise analysis (200 words max) covering:
1. CONSENSUS: What do most models agree on? (2-3 bullet points)
2. DIVERGENCE: Where do they meaningfully disagree? (1-2 bullet points)
3. CONFIDENCE: Rate 0-100 how confident the consensus is
4. SYNTHESIS: One paragraph combining the strongest points from all models

Be precise. No filler. Cite specific models when noting disagreements."""

    try:
        resp = bridge.ask_tier(tier, meta_prompt, system="You are a precise analytical tool. Output structured analysis only.")
        if resp.error:
            return ""
        return resp.text
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Main analyzer
# ---------------------------------------------------------------------------

class ConsensusAnalyzer:
    """Analyze multiple model responses for consensus, divergence, and confidence."""

    def __init__(self, bridge=None):
        """Initialize. Pass a RheaBridge instance to enable LLM-assisted synthesis."""
        self.bridge = bridge

    def analyze(
        self,
        responses: list[tuple[str, str]],
        prompt: str = "",
        use_llm: bool = False,
        llm_tier: str = "cheap",
    ) -> ConsensusReport:
        """Analyze a list of (model_id, response_text) tuples.

        Args:
            responses: List of (model_id, response_text) tuples.
            prompt: The original prompt (used for LLM synthesis context).
            use_llm: If True and bridge is available, use LLM for synthesis.
            llm_tier: Which cost tier for the synthesis model.

        Returns:
            ConsensusReport with full analysis.
        """
        report = ConsensusReport()

        # Filter out empty/error responses
        valid = [(mid, text) for mid, text in responses if text and len(text.strip()) > 10]
        report.model_count = len(responses)
        report.successful_count = len(valid)

        if len(valid) < 2:
            report.consensus_text = (
                f"Insufficient responses for consensus analysis "
                f"({len(valid)} valid out of {len(responses)} total)."
            )
            report.confidence = 0.0
            return report

        model_ids = [mid for mid, _ in valid]
        texts = [text for _, text in valid]

        # --- Step 1: Tokenize all responses ---
        tokenized = [_tokenize(text) for text in texts]

        # --- Step 2: TF-IDF cosine + Jaccard → blended pairwise similarity ---
        tfidf = TfIdf()
        vectors = tfidf.fit_transform(tokenized)

        similarities = {}
        sim_values = []
        for i in range(len(valid)):
            for j in range(i + 1, len(valid)):
                cosine = _cosine_similarity(vectors[i], vectors[j])
                jaccard = _jaccard_similarity(tokenized[i], tokenized[j])
                blended = _blended_similarity(cosine, jaccard)
                key = f"{model_ids[i]} vs {model_ids[j]}"
                similarities[key] = round(blended, 4)
                sim_values.append(blended)

        report.pairwise_similarity = similarities

        # Raw text similarity (calibrated: 0.10 cosine on short text ≈ moderate agreement)
        raw_text_sim = sum(sim_values) / len(sim_values) if sim_values else 0.0

        # --- Step 3: Stance detection ---
        stances = {}
        for mid, text in valid:
            stances[mid] = _detect_stance(text)
        report.stance_summary = stances

        # Stance alignment score: what fraction of models share the dominant stance?
        stance_values = [s["stance"] for s in stances.values()]
        stance_counts = Counter(stance_values)
        dominant_count = max(stance_counts.values()) if stance_counts else 0
        stance_alignment = dominant_count / len(stance_values) if stance_values else 0.0

        # --- Step 4: Agreement / divergence detection ---
        agreement_pts, divergence_pts = _find_agreement_divergence(
            model_ids, texts
        )
        report.agreement_points = agreement_pts
        report.divergence_points = divergence_pts

        # Claim overlap score: ratio of agreement points to total unique points
        total_points = len(agreement_pts) + len(divergence_pts)
        claim_overlap = len(agreement_pts) / total_points if total_points > 0 else 0.5

        # --- Composite agreement score ---
        # Calibrated text similarity: map raw 0.05-0.30 range to 0.0-1.0
        calibrated_text = min(max((raw_text_sim - 0.03) / 0.25, 0.0), 1.0)

        # Blend: text similarity (35%) + stance alignment (40%) + claim overlap (25%)
        report.agreement_score = round(
            0.35 * calibrated_text + 0.40 * stance_alignment + 0.25 * claim_overlap,
            4,
        )

        # --- Step 5: Confidence scoring ---
        n = len(valid)
        model_factor = min(n / 5, 1.0)  # max out at 5 models
        report.confidence = round(
            0.3 * model_factor + 0.4 * report.agreement_score + 0.3 * stance_alignment,
            4,
        )

        # --- Step 6: Synthesize consensus text ---
        if use_llm and self.bridge:
            llm_synthesis = _synthesize_consensus_llm(
                model_ids, texts, prompt, self.bridge, llm_tier
            )
            if llm_synthesis:
                report.consensus_text = llm_synthesis
                report.analysis_method = "tfidf_local + llm_synthesis"
            else:
                # LLM call failed — fall back to local
                report.consensus_text = _synthesize_consensus_local(
                    model_ids, texts, stances,
                    report.agreement_score, agreement_pts, divergence_pts,
                )
        else:
            report.consensus_text = _synthesize_consensus_local(
                model_ids, texts, stances,
                report.agreement_score, agreement_pts, divergence_pts,
            )

        # --- Meta ---
        report.meta = {
            "vocab_size": len(tfidf.idf),
            "avg_response_length": round(sum(len(t) for t in texts) / len(texts)),
            "avg_token_count": round(sum(len(t) for t in tokenized) / len(tokenized)),
        }

        return report


# ---------------------------------------------------------------------------
# Convenience function for bridge integration
# ---------------------------------------------------------------------------

def analyze_tribunal_responses(
    tribunal_result,
    prompt: str = "",
    bridge=None,
    use_llm: bool = False,
) -> ConsensusReport:
    """Analyze a TribunalResult from rhea_bridge.py.

    This is the main integration point. Call this after bridge.tribunal().

    Args:
        tribunal_result: TribunalResult from RheaBridge.tribunal()
        prompt: The original prompt (defaults to tribunal_result.prompt)
        bridge: RheaBridge instance (needed for LLM synthesis)
        use_llm: Whether to use LLM-assisted synthesis

    Returns:
        ConsensusReport
    """
    if not prompt:
        prompt = tribunal_result.prompt

    responses = []
    for r in tribunal_result.responses:
        model_id = f"{r.provider}/{r.model}" if r.provider else r.model
        responses.append((model_id, r.text if not r.error else ""))

    analyzer = ConsensusAnalyzer(bridge=bridge)
    return analyzer.analyze(responses, prompt=prompt, use_llm=use_llm)


# ---------------------------------------------------------------------------
# CLI (standalone testing)
# ---------------------------------------------------------------------------

def _demo():
    """Run a demo with synthetic responses to verify the analyzer works."""
    print("=== Consensus Analyzer Demo ===\n")

    # Simulate 5 model responses to: "Should you take cold showers in the morning?"
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

    analyzer = ConsensusAnalyzer()
    report = analyzer.analyze(
        responses,
        prompt="Should you take cold showers in the morning for ADHD management?"
    )

    print(f"Agreement Score: {report.agreement_score:.2%}")
    print(f"Confidence: {report.confidence:.2%}")
    print(f"Models: {report.successful_count}/{report.model_count}")
    print(f"\n--- Consensus ---\n{report.consensus_text}")
    print(f"\n--- Pairwise Similarity ---")
    for pair, sim in sorted(report.pairwise_similarity.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(sim * 30)
        print(f"  {pair:50s} {sim:.3f} {bar}")
    print(f"\n--- Stances ---")
    for model, stance in report.stance_summary.items():
        print(f"  {model:35s} → {stance['stance']:12s} (aff={stance['affirmative']:.2f} neg={stance['negative']:.2f} qual={stance['qualified']:.2f})")
    print(f"\n--- Meta ---")
    for k, v in report.meta.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    _demo()
