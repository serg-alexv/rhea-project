# SPDX Policy Activation Checklist

## 0) Scope and Activation Target

- Source drafts (authoritative inputs for activation):
  - `docs/legal_un_drafts/en/LEGAL_ARCHITECTURE.md`
  - `docs/legal_un_drafts/en/LICENSE_MATRIX.md`
  - `docs/legal_un_drafts/en/GOVERNANCE.md`
  - `docs/legal_un_drafts/en/CONTRIBUTING.md`
  - `docs/legal_un_drafts/en/DCO.md`
- Activation objective: move SPDX/license policy from draft text to enforced repository policy (PR + release blocking).
- "Active" means all of the following are true:
  - Steward-approved legal text is published in canonical non-draft paths.
  - CI gates are required checks on protected branches.
  - Release process blocks on SPDX/license/NOTICE failures.
  - Ownership, versioning, cadence, and rollback controls are operating.

## 1) Ownership (RACI)

- Steward (A): legal policy approval, exception approval, rollback ratification.
- Maintainer (R): implements policy in repo, enables required checks, enforces merges/releases.
- Compliance Operator (R): maintains CI gate definitions and incident triage.
- Release Owner (R): release-time verification (`NOTICE`, attribution, artifact SPDX declarations).
- Contributors (C): comply with SPDX/DCO/license requirements in PRs.
- Community (I): visibility through changelog and policy updates.

## 2) Draft -> Active Execution Checklist

### Phase A: Freeze and Open Activation Work Item

- [ ] Create activation issue `legal/spdx-activation` with links to all 5 source drafts.
- [ ] Record baseline commit SHA of draft set.
- [ ] Assign named owners for Steward, Maintainer, Compliance Operator, Release Owner.
- [ ] Define target activation date and rollback contact channel.

Exit criteria:
- Activation issue exists, owners assigned, target date set, draft baseline captured.

### Phase B: Legal Ratification

- [ ] Run counsel review on the 5 English draft docs.
- [ ] Resolve all redlines in branch linked to activation issue.
- [ ] Obtain steward sign-off in writing (issue comment or decision record).
- [ ] Mark any unresolved items as explicit post-activation TODOs with deadlines.

Exit criteria:
- Counsel feedback resolved, steward approval recorded, no unresolved blockers.

### Phase C: Publish Active Canonical Policy Files

- [ ] Promote approved docs from draft area to canonical policy location (recommended: `docs/legal/`).
- [ ] Ensure root `LICENSE` and `NOTICE` align with approved policy.
- [ ] Add policy changelog entry describing activation decision and effective date.
- [ ] Mark draft docs as superseded (do not delete history; keep traceability).

Exit criteria:
- Canonical policy docs published, changelog entry present, LICENSE/NOTICE aligned.

### Phase D: Enforce CI and Branch Protection

- [ ] Implement and enable all required CI gates in Section 3.
- [ ] Mark gates as required checks for protected branches.
- [ ] Verify merge is blocked when any gate fails.
- [ ] Verify release pipeline is blocked when release gates fail.

Exit criteria:
- Required checks are active and demonstrably blocking merges/releases on failure.

### Phase E: Activation Verification

- [ ] Run one "known-good" PR through all gates (must pass).
- [ ] Run one "known-bad" PR (missing SPDX or disallowed license) to confirm blocking behavior.
- [ ] Run a release dry-run and validate `NOTICE` + dependency attribution checks.
- [ ] Publish activation announcement with policy version and effective date.

Exit criteria:
- Positive and negative control tests verified; policy announced as active.

## 3) Required CI Gates (Blocking)

The following checks must be required for protected branches.

| Gate Name | Purpose | Fail Condition | Owner | Scope |
|---|---|---|---|---|
| `spdx_artifact_gate` | Ensure distributable artifacts and source paths declare SPDX identifiers per policy | Missing SPDX declaration in required file/artifact set | Compliance Operator | PR + Release |
| `dependency_license_allowlist_gate` | Enforce allowlist from `LICENSE_MATRIX` | Dependency license is disallowed (`GPL-*`, `AGPL-*`, `LGPL-*`, `SSPL-*`, custom/non-commercial) or unknown | Compliance Operator | PR + Release |
| `notice_attribution_gate` | Enforce attribution updates | Dependency changes without corresponding `NOTICE`/attribution update | Release Owner | PR + Release |
| `dco_signoff_gate` | Enforce signed provenance | Any commit in PR lacks valid DCO sign-off | Maintainer | PR |
| `policy_version_sync_gate` | Prevent unversioned policy changes | Policy behavior changes without version bump + changelog entry | Maintainer | PR |

Minimum branch protection settings:
- Require status checks to pass before merging.
- Require at least one maintainer approval.
- Disallow bypass for non-steward/non-admin actors.

## 4) Versioning Policy

- Version format: `spdx-policy-vMAJOR.MINOR.PATCH`.
- MAJOR:
  - Allowlist/restriction model changes (for example allowing or banning license families).
  - Governance authority or exception model changes.
- MINOR:
  - New artifact classes, new CI gates, or expanded required evidence.
- PATCH:
  - Clarifications that do not change enforcement outcomes.

Required versioning actions on each policy change:
- [ ] Increment version in canonical policy index/header.
- [ ] Add dated changelog entry with rationale and approvers.
- [ ] Tag release commit (recommended tag: `legal/spdx/vX.Y.Z`).
- [ ] Link activation/decision issue in changelog.

## 5) Review Cadence (Operational)

- Weekly (Compliance Operator + Maintainer):
  - Triage CI failures/exceptions and close or escalate within 5 business days.
- Monthly (Maintainer + Release Owner):
  - Review dependency license delta and `NOTICE` completeness.
- Quarterly (Steward + Maintainer):
  - Full policy review against active repo artifacts and release behavior.
  - Re-confirm allowlist/restricted list applicability.
- Annual (Steward + Counsel):
  - Formal legal review and ratification of continued policy fit.

Cadence evidence required:
- Meeting/decision note with date, attendees, decisions, and action items.
- Changelog update when review results in policy behavior changes.

## 6) Exception Handling

- Exceptions are temporary and must include:
  - Scope (dependency/artifact/path),
  - Risk justification,
  - Expiration date,
  - Maintainer + Steward written approval,
  - Tracking issue/decision record.
- Expired exceptions automatically return to blocked state until renewed.

## 7) Rollback Protocol (If Activation Causes Legal or Delivery Risk)

### Triggers

- False-positive CI behavior blocks critical delivery for >4 hours.
- Post-activation legal conflict discovered (license incompatibility, attribution gap).
- Enforcement regression causes release integrity risk.

### Authority

- Immediate mitigation: Maintainer can apply temporary rollback action.
- Final ratification within 24 hours: Steward approval required.

### Execution Steps

- [ ] Open incident record `legal/spdx-rollback-<date>` with trigger and impact.
- [ ] Revert to last known-good policy version tag (`legal/spdx/vX.Y.Z`).
- [ ] Restore prior CI gate configuration from that version.
- [ ] Re-run blocking gates on default branch to confirm restored baseline.
- [ ] Publish incident note with rollback time, impact window, and temporary rules.
- [ ] Create corrective action plan with owner + due date before re-activation.

Rollback completion criteria:
- Previous stable policy version active, CI stable, incident documented, corrective plan approved.

## 8) Definition of Done (Activation Complete)

- [ ] Steward-approved policy is published outside draft paths.
- [ ] All required CI gates are active and required.
- [ ] Version/changelog/tagging controls are in use.
- [ ] Review cadence calendar and owners are assigned.
- [ ] Rollback runbook tested at least once via tabletop or dry run.
- [ ] Activation issue is closed with links to evidence artifacts.
