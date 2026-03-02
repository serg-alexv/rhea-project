# Security Policy

**Rhea Research Platform**
timelabs npo
Last updated: 2026-02-26

---

## 1. Our Commitment

timelabs npo takes security seriously. Rhea handles scientific research queries and, when accounts are enabled, user credentials. We are committed to fixing confirmed vulnerabilities promptly and working transparently with the security community.

---

## 2. Scope

This policy covers:
- The Rhea web platform and its APIs
- The `rhea_bridge.py` multi-model routing layer
- Authentication and session management (when accounts are enabled)
- Firebase/Firestore backend (firestore.rules and related config)
- The open-source repository at github.com/serg-alexv/rhea-project

**Out of scope:**
- Third-party AI provider APIs (OpenAI, Anthropic, Google, etc.) — report those to the respective provider
- Issues in GitHub's own infrastructure
- Attacks requiring physical access to our systems
- Social engineering attacks on timelabs npo team members

---

## 3. Supported Versions

| Branch | Supported |
|--------|-----------|
| `main` | Yes — active development, patches applied |
| Older tags | No — upgrade to `main` |

We do not maintain separate LTS branches. Security fixes land on `main`.

---

## 4. Reporting a Vulnerability

**Please do not report security vulnerabilities via GitHub Issues.** Issues are public and may expose users before a fix is ready.

### How to Report

**Email**: celestica201@gmail.com
**Subject line**: `[SECURITY] <brief description>`

Include in your report:
- Description of the vulnerability and its impact
- Steps to reproduce (proof of concept if possible)
- Affected component (bridge, auth, Firestore rules, API endpoint, etc.)
- Your suggested severity (Critical / High / Medium / Low)
- Whether you have already disclosed this publicly

We will acknowledge your report within **48 hours** and provide a status update within **7 days**.

---

## 5. Responsible Disclosure Process

1. **Report**: Submit via email as described above
2. **Acknowledgment**: We confirm receipt within 48 hours
3. **Triage**: We assess severity and reproduce the issue within 7 days
4. **Remediation**: We develop and test a fix (timeline varies by severity — see below)
5. **Disclosure**: We coordinate a public disclosure date with you, typically after the fix is released
6. **Credit**: We credit reporters in the release notes unless you prefer to remain anonymous

We ask that you:
- Give us reasonable time to fix before public disclosure
- Not access or modify user data beyond what is needed to demonstrate the issue
- Not perform denial-of-service attacks

---

## 6. Severity and Response Timelines

| Severity | Description | Target Fix Time |
|----------|-------------|-----------------|
| Critical | Remote code execution, authentication bypass, mass data exposure | 24-48 hours |
| High | Privilege escalation, significant data leak, SSRF | 7 days |
| Medium | XSS, CSRF, moderate information disclosure | 30 days |
| Low | Minor information leakage, hardening improvements | 90 days |

For Critical and High severity, we will deploy hotfixes to `main` and notify affected users as appropriate.

---

## 7. Bug Bounty

timelabs npo is a **non-profit organization**. We do not currently offer monetary bug bounties.

We do offer:
- **Public credit** in release notes and the repository's SECURITY acknowledgments (unless you prefer anonymity)
- Our sincere gratitude — security researchers help protect real scientists using this platform
- A direct line of communication with the core team

If the project grows to a point where a paid bounty program is sustainable, we will announce it here and via the repository.

---

## 8. Known Security Practices

For transparency, here is what we currently do:

- **Firestore Security Rules**: access control enforced at the database layer (`firebase/firestore.rules`)
- **Secrets management**: API keys stored in `.env` (gitignored, never committed)
- **Dependency updates**: monitored via GitHub Dependabot
- **TLS**: all external communications use HTTPS
- **Authentication**: credentials hashed with industry-standard algorithms (when accounts are enabled)
- **Principle of least privilege**: service accounts and API keys scoped to minimum required permissions
- **Open source**: code is publicly auditable at github.com/serg-alexv/rhea-project

---

## 9. Security Acknowledgments

We thank the following individuals for responsible disclosure (updated as reports are received):

*None yet — be the first.*

---

## 10. Contact

Security reports: **celestica201@gmail.com**
General security questions welcome at the same address.
GitHub: github.com/serg-alexv/rhea-project
