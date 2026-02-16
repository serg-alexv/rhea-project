# Retrieval Evaluation & Recall Quality (Advanced)

SYSTEM:
You are a scientist. Measure retrieval, don't assume it works.

USER:
Define an evaluation plan for external memory retrieval:
- metrics: recall@k, precision@k, MRR, faithfulness, citation coverage
- test set construction: "needle" facts + adversarial distractors
- prompt-injection robustness tests for retrieved documents
- monitoring in production: drift detection, missing-receipt rate
Output: a concise protocol with acceptance thresholds.
