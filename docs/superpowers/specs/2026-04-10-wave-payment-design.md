# Wave Payment Integration Design

**Date:** 2026-04-10  
**Owner:** Brent Halonen  
**Stack:** Flask · Wave GraphQL API · SQLAlchemy

---

## 1. Business Context

HALONEN FLOU uses Wave (waveapps.com) as its payment processor. When a client subscribes, they are redirected to a Wave-hosted payment page to pay the first day/session fee. After payment, the subscriber record is marked `active` via a Wave webhook.

**Business ID:** `QnVzaW5lc3M6ZmZjMGJiZjEtMjhhZi00ODgyLWIwOTAtYWQyNjg1OGE5ZDFi` (base64, used in API calls)  
**Wave API endpoint:** `https://gql.waveapps.com/graphql/public`

---

## 2. Payment Flow

```
Client fills /subscribe form
        ↓
POST /subscribe — validate → create Subscriber(status='pending') → call Wave API
        ↓
Wave API: customerCreate (or find by email) → invoiceCreate → return viewUrl
        ↓
Redirect client to Wave hosted payment page (next.waveapps.com/...)
        ↓
Client pays with card on Wave
        ↓
Wave sends webhook POST /subscribe/webhooks/wave
        ↓
Webhook handler verifies → Subscriber.status = 'active'
        ↓
Client redirected to /subscribe/success (via Wave's "redirect after payment" URL)
```

---

## 3. Pricing Per Service

| Service | Amount | Notes |
|---------|--------|-------|
| Artist Promotion | `custom_amount` entered by client | Minimum $1 |
| Music Lessons | $100.00 | Fixed per session |
| Artist Production | $2,500.00 | Fixed project fee |

---

## 4. Architecture

### New file: `app/blueprints/subscriptions/providers/wave.py`

Two public functions:

**`create_invoice(subscriber) → str`**
- Calls Wave GraphQL API
- Creates or finds customer by email (`customerCreate` or query)
- Creates invoice with one line item (service name + amount)
- Returns `invoice.viewUrl` (the Wave hosted checkout URL)
- Stores `invoice.id` on the Subscriber record

**`handle_webhook(payload) → bool`**
- Receives Wave webhook JSON payload
- Checks `data.invoice.status == 'PAID'`
- Finds Subscriber by `wave_invoice_id`
- Sets `status = 'active'`
- Returns True on success

### Modified: `app/blueprints/subscriptions/routes.py`

`subscribe()` POST handler — after saving Subscriber to DB:
```python
from .providers.wave import create_invoice
checkout_url = create_invoice(sub)
return redirect(checkout_url)
```

`webhook()` handler for `provider == 'wave'`:
```python
from .providers.wave import handle_webhook
handle_webhook(payload)
```

### Modified: `app/models.py`

Add field to `Subscriber`:
```python
wave_invoice_id = db.Column(db.String(200), nullable=True)
```

### New migration

Add `wave_invoice_id` column to `subscriber` table.

---

## 5. Wave API Calls

### Create/find customer
```graphql
mutation customerCreate($businessId: ID!, $input: CustomerCreateInput!) {
  customerCreate(businessId: $businessId, input: $input) {
    customer { id name }
    didCreate
    inputErrors { message }
  }
}
```

Input: `{ name, email }`

### Create invoice
```graphql
mutation invoiceCreate($businessId: ID!, $input: InvoiceCreateInput!) {
  invoiceCreate(businessId: $businessId, input: $input) {
    invoice { id viewUrl status }
    didCreate
    inputErrors { message }
  }
}
```

Input:
```json
{
  "customerId": "...",
  "items": [{
    "description": "Artist Promotion — Daily Subscription",
    "quantity": "1",
    "unitPrice": "200.00"
  }]
}
```

---

## 6. Webhook Handling

Wave sends a POST to `/subscribe/webhooks/wave` when invoice status changes.

Payload structure:
```json
{
  "data": {
    "invoice": {
      "id": "...",
      "status": "PAID"
    }
  }
}
```

Handler:
1. Parse `payload['data']['invoice']['id']`
2. Find `Subscriber` where `wave_invoice_id == invoice_id`
3. If found and status is `PAID` → set `subscriber.status = 'active'`
4. Return 200

Wave webhook URL to configure in Wave dashboard: `https://web-production-f4c2c.up.railway.app/subscribe/webhooks/wave`

---

## 7. Environment Variables

Add to Railway web service:
```
WAVE_API_TOKEN = 4uQqMcTFsojZ6U2AmxPAH4OHizdsOe
WAVE_BUSINESS_ID = QnVzaW5lc3M6ZmZjMGJiZjEtMjhhZi00ODgyLWIwOTAtYWQyNjg1OGE5ZDFi
```

Add to `.env.example` (without values):
```
WAVE_API_TOKEN=
WAVE_BUSINESS_ID=
```

---

## 8. Error Handling

- Wave API unreachable → flash error, re-render form, do NOT save Subscriber
- Wave returns `inputErrors` → log error, flash generic message, do NOT save Subscriber
- Webhook arrives for unknown invoice ID → return 200 (idempotent, ignore)
- Webhook arrives for already-active subscriber → return 200 (idempotent, no-op)

---

## 9. Out of Scope

- Recurring automatic daily billing (manual invoicing after first payment)
- Refunds via API
- Webhook signature verification (Wave does not provide HMAC signing)
- Email notifications beyond what Wave sends automatically
