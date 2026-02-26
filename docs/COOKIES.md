# Cookie Policy

**Rhea Research Platform**
TimeLabs NPO
Last updated: 2026-02-26

---

## 1. Overview

This policy explains what cookies and similar technologies Rhea uses, why, and what we do not use them for.

**Short version**: Rhea uses only essential cookies necessary to operate the platform. No tracking. No advertising. No third-party analytics.

---

## 2. What Are Cookies

Cookies are small text files stored in your browser when you visit a website. They can remember preferences, session state, and other information between page loads. Similar technologies include localStorage, sessionStorage, and IndexedDB — all governed by the same principles here.

---

## 3. Cookies We Use

### Essential Cookies Only

Rhea uses a minimal set of cookies strictly required for the platform to function. We do not set any cookie that is not essential.

| Cookie Name | Purpose | Duration | Type |
|-------------|---------|----------|------|
| `rhea_session` | Maintains your login session (when accounts are enabled) | Session (expires on browser close) | Essential |
| `rhea_csrf` | Cross-site request forgery protection token | Session | Essential |
| `rhea_theme` | Stores your UI preference (light/dark mode) | 1 year | Essential/Functional |

**localStorage usage:**
| Key | Purpose | Controlled by |
|-----|---------|---------------|
| `rhea_query_history` | Stores your query history locally in your browser | You — cleared by clearing browser data |
| `rhea_model_prefs` | Stores your model/tier preferences | You — cleared by clearing browser data |

All localStorage data stays on your device. It is never transmitted to our servers unless you explicitly sync it (future feature, opt-in only).

---

## 4. What We Do Not Use

We explicitly do not use:

- **Analytics cookies** (Google Analytics, Mixpanel, Amplitude, or any equivalent)
- **Advertising cookies** or ad network pixels
- **Social media tracking cookies** (Facebook Pixel, Twitter/X tracking, LinkedIn Insight)
- **Third-party behavioral tracking** of any kind
- **Fingerprinting** or any non-cookie tracking technique that identifies you across sites
- **Persistent cross-session identifiers** beyond the session cookie above

If you see a cookie in your browser not listed in Section 3, please report it to us — it should not be there.

---

## 5. Third-Party Cookies

Rhea does not embed third-party scripts that set cookies. We do not use:
- CDN-served analytics (e.g., Google Tag Manager)
- Embedded social widgets
- Chat widgets from third parties
- A/B testing platforms

If this changes, we will update this policy and notify users.

---

## 6. Consent

Under GDPR and ePrivacy Directive rules:
- **Essential cookies** do not require consent — they are necessary for the site to work
- **Functional cookies** (theme preference) are minimal and privacy-safe; no consent popup is required
- Because we use no analytics or advertising cookies, no cookie consent banner is needed for those categories

If you are in a jurisdiction that requires explicit consent for functional cookies, you can disable them by not using the preference feature — defaults will apply.

---

## 7. Managing Cookies

You can control cookies through your browser settings:

- **Chrome**: Settings > Privacy and security > Cookies
- **Firefox**: Settings > Privacy & Security > Cookies and Site Data
- **Safari**: Preferences > Privacy > Manage Website Data
- **Edge**: Settings > Cookies and site permissions

Disabling the session cookie will prevent login (when accounts are enabled). Disabling localStorage will prevent local query history from being stored. All other platform functionality remains available.

---

## 8. Do Not Track

Rhea respects the `DNT` (Do Not Track) browser header. Since we do not track users regardless, this header has no additional effect — but we honor the intent.

---

## 9. Changes to This Policy

If we introduce new cookies or change how existing ones work, we will update this document with a new date and note the change in the repository changelog. We will not add tracking or advertising cookies without explicit, separate user consent.

---

## 10. Contact

Cookie questions:
**celestica201@gmail.com**
GitHub: github.com/serg-alexv/rhea-project
