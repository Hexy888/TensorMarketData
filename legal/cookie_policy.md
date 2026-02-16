# Cookie Policy

**Last Updated: February 12, 2026**

## 1. Overview

This Cookie Policy explains what cookies are, how TensorMarketData uses them, and your choices regarding cookies.

## 2. What Are Cookies?

Cookies are small text files stored on your device when you visit websites. They help remember your preferences, enable functionality, and provide analytics.

## 3. Types of Cookies We Use

### Essential Cookies
**Purpose:** Required for the platform to function

| Cookie Name | Purpose | Duration |
|-------------|---------|----------|
| session_id | Maintain login state | 24 hours |
| csrf_token | Security (CSRF protection) | Session |
| consent_banner | Remember cookie preferences | 1 year |

**Legal Basis:** Legitimate interest / Necessary for service

### Analytics Cookies
**Purpose:** Understand how visitors use our platform

| Cookie Name | Purpose | Duration |
|-------------|---------|----------|
| _ga | Google Analytics - user identification | 2 years |
| _gid | Google Analytics - session tracking | 24 hours |
| _gat | Google Analytics - request throttling | 1 minute |

**Legal Basis:** Consent

### Functional Cookies
**Purpose:** Enhanced functionality and personalization

| Cookie Name | Purpose | Duration |
|-------------|---------|----------|
| preferences | Remember UI settings | 1 year |
| language | Language selection | 1 year |

**Legal Basis:** Consent

### Marketing Cookies
**Purpose:** We do NOT use marketing or advertising cookies

We do not track users across third-party sites for advertising purposes.

## 4. Cookie Categories Summary

| Category | Required | Can Disable |
|----------|----------|-------------|
| Essential | Yes | No |
| Analytics | No | Yes |
| Functional | No | Yes |
| Marketing | N/A | N/A |

## 5. How We Use Cookies

- **Authentication:** Keep you logged in
- **Security:** Prevent fraud and protect against attacks
- **Preferences:** Remember settings and choices
- **Analytics:** Understand traffic and improve the platform
- **Performance:** Monitor and optimize service delivery

## 6. Managing Cookies

### Browser Settings
Most browsers allow you to control cookies via settings:
- Chrome: Settings → Privacy → Cookies
- Firefox: Options → Privacy → Cookies
- Safari: Preferences → Privacy → Cookies
- Edge: Settings → Cookies and site permissions

### Opt-Out Links
- Google Analytics: https://tools.google.com/dlpage/gaoptout

### Consequences of Disabling
Disabling essential cookies will prevent you from:
- Logging into your account
- Making purchases
- Accessing secure areas of the platform

## 7. Third-Party Cookies

We use these third-party services that set cookies:

| Third Party | Purpose | Privacy Policy |
|-------------|---------|----------------|
| Google Analytics | Website analytics | google.com/policies/privacy |
| Stripe | Payment processing | stripe.com/privacy |

We don't control third-party cookies. Review their policies for more information.

## 8. Updates to This Policy

We may update this policy as our services evolve. Any material changes will be communicated via the platform.

---

# Consent Banner

## Text for Implementation

```html
<!-- Cookie Consent Banner -->
<div id="cookie-consent-banner" style="display:none; position:fixed; bottom:0; left:0; right:0; background:#fff; border-top:1px solid #ddd; padding:20px; box-shadow:0 -2px 10px rgba(0,0,0,0.1); z-index:9999;">
  <div style="max-width:1200px; margin:0 auto; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:15px;">
    <div style="flex:1; min-width:280px;">
      <h3 style="margin:0 0 8px 0; font-size:16px;">🍪 We use cookies</h3>
      <p style="margin:0; font-size:14px; color:#666;">
        We use essential cookies for security and functionality. With your consent, we also use analytics cookies to improve our platform. 
        <a href="/privacy" style="color:#0066cc;">Privacy Policy</a>
      </p>
    </div>
    <div style="display:flex; gap:10px;">
      <button id="cookie-reject" style="padding:10px 20px; border:1px solid #ddd; background:#fff; cursor:pointer; border-radius:4px;">Reject Non-Essential</button>
      <button id="cookie-accept" style="padding:10px 20px; border:none; background:#0066cc; color:#fff; cursor:pointer; border-radius:4px;">Accept All</button>
    </div>
  </div>
</div>
```

```javascript
// JavaScript for Consent Banner
document.addEventListener('DOMContentLoaded', function() {
  const banner = document.getElementById('cookie-consent-banner');
  const consent = localStorage.getItem('cookie_consent');
  
  if (!consent) {
    banner.style.display = 'block';
  }
  
  document.getElementById('cookie-accept').addEventListener('click', function() {
    localStorage.setItem('cookie_consent', 'accepted');
    banner.style.display = 'none';
    // Enable analytics cookies here
    gtag('consent', 'update', {'analytics_storage': 'granted'});
  });
  
  document.getElementById('cookie-reject').addEventListener('click', function() {
    localStorage.setItem('cookie_consent', 'rejected');
    banner.style.display = 'none';
    // Disable analytics cookies here
    gtag('consent', 'update', {'analytics_storage': 'denied'});
  });
});
```

---

*This is a simplified example document. Consult qualified legal counsel before use.*
