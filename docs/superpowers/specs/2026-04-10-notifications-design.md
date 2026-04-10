# Email Notifications & Success Page Design

**Date:** 2026-04-10  
**Owner:** Brent Halonen  
**Stack:** Flask · Flask-Mail · Gmail SMTP

---

## 1. Business Context

HALONEN FLOU needs to be notified when:
1. A visitor submits the contact form
2. A subscriber's Wave payment is confirmed (webhook marks them active)

Currently neither event sends any email. The success page also has outdated copy referencing "we'll reach out in 24 hours" — irrelevant now that clients pay and activate via Wave.

---

## 2. Email Notifications

### What gets sent

**Contact form submitted:**
- Subject: `[HALONEN FLOU] New contact message from {name}`
- Body: name, email, subject, message text

**Subscriber activated (Wave payment confirmed):**
- Subject: `[HALONEN FLOU] New subscriber: {name} ({service_type})`
- Body: name, email, service type, custom amount if applicable

### Where emails are sent

To: `bluealikeu@gmail.com` (configured via `NOTIFY_EMAIL` env var)

### Architecture

New file: `app/email.py`

```python
def send_notification(subject: str, body: str) -> None
```

- Uses Flask-Mail with Gmail SMTP
- Logs error and returns silently if sending fails — does NOT raise
- Called after DB commit in both trigger points

### Trigger points

- `app/blueprints/contact/routes.py` — after `db.session.commit()`
- `app/blueprints/subscriptions/providers/wave.py` — after `db.session.commit()` in `handle_webhook()`

### Config (all via env vars)

| Variable | Value |
|----------|-------|
| `MAIL_SERVER` | `smtp.gmail.com` |
| `MAIL_PORT` | `587` |
| `MAIL_USE_TLS` | `True` |
| `MAIL_USERNAME` | `bluealikeu@gmail.com` |
| `MAIL_PASSWORD` | Gmail App Password (16-char) |
| `NOTIFY_EMAIL` | `bluealikeu@gmail.com` |

### Railway env vars to add

```
MAIL_USERNAME=bluealikeu@gmail.com
MAIL_PASSWORD=<app-password>
NOTIFY_EMAIL=bluealikeu@gmail.com
```

### Gmail App Password setup

1. Google Account → Security → 2-Step Verification (must be ON)
2. Security → App Passwords → create "Mail / Other" → copy 16-char password
3. Use that as `MAIL_PASSWORD`

---

## 3. Success Page

Current copy says "We'll reach out within 24 hours to get everything set up" — this is wrong post-Wave. Client has already paid; subscription is active or pending webhook.

**Updated copy:**

> **Payment Received!**  
> Thank you for subscribing with HALONEN FLOU. Your payment was processed successfully. We'll be in touch within 24 hours to kick things off.

Keep the two CTAs: "See Artist Stories" and "Contact Us".

---

## 4. Error Handling

- Email fails → log `app.logger.error(...)`, continue silently
- `MAIL_PASSWORD` not set → Flask-Mail raises on first send → caught by the silent handler above
- No change to contact/subscribe flows — email is best-effort

---

## 5. Testing

- `app/email.py` tested with `unittest.mock.patch('flask_mail.Mail.send')`
- One test per trigger point: contact route, webhook handler
- Existing 41 tests must still pass

---

## 6. Out of Scope

- Confirmation email to the client
- HTML email templates
- Email queuing / retry logic
- Unsubscribe links
