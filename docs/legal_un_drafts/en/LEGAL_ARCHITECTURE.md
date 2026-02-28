# LEGAL ARCHITECTURE (Draft)

## 1) Purpose
This architecture separates legal regimes by artifact type so the project can stay open, reusable, and governable as a non-profit experiment.

## 2) Layer Model
- Layer A — Open Core Code: `Apache-2.0` (or `MIT` for selected modules).
- Layer B — Data, content, educational materials: default `CC BY-NC 4.0` unless explicitly marked otherwise.
- Layer C — Brand assets (names, logos, visual identity): protected by trademark policy.
- Layer D — Hosted services and operations: governed by Terms/Privacy/Security documents.

## 3) Defaults
- Repository code default SPDX: `Apache-2.0`.
- Example snippets/docs default: `CC BY 4.0` unless marked `CC BY-NC 4.0`.
- Third-party licenses are preserved and attributed in `NOTICE` and dependency manifests.

## 4) Guardrails
- No secret data in public repos.
- No relicensing of third-party code without rights.
- Every distributable artifact must have a declared SPDX identifier.
- CI must fail when license policy checks fail.

## 5) Governance Link
Legal changes require:
- RFC issue,
- maintainer review,
- steward approval,
- changelog entry in legal docs.

## 6) Not Legal Advice
This document is a project draft and must be validated by qualified counsel before formal adoption.
