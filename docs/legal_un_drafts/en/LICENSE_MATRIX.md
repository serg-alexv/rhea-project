# LICENSE MATRIX (Draft)

## 1) Artifact-to-License Mapping
- Core source code: `Apache-2.0` (default).
- Selected utility modules: `MIT` (only when explicitly marked).
- Documentation: `CC BY 4.0` (or `CC BY-NC 4.0` for restricted materials).
- Research datasets/content: declared per dataset card.
- Brand/logos/names: trademark policy, not open-source licensed.

## 2) Allowed Third-Party Licenses (Default Allowlist)
- `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `MPL-2.0`.

## 3) Restricted/Review-Required
- `GPL-*`, `AGPL-*`, `LGPL-*`, `SSPL-*`, non-commercial or custom licenses.
- Any dependency without clear SPDX identifier.

## 4) Compliance Controls
- Automated SPDX scanning in CI.
- `NOTICE` and attribution updates required for release.
- Failing policy checks block merge/release.

## 5) Exceptions
License exceptions require written maintainer + steward approval and a tracked decision record.
