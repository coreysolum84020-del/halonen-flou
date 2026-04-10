# Authorize.net Payment Integration Design

**Date:** 2026-04-10  
**Owner:** Brent Halonen  
**Stack:** Flask · Authorize.net Accept Hosted API · SQLAlchemy

---

## 1. Business Context

HALONEN FLOU already accepts payments via Wave. Adding Authorize.net gives clients a second payment option. Both providers appear side-by-side on the subscribe form — client picks one and proceeds to that provider's hosted checkout page.

---

## 2. Payment Flow

```
Client fills /subscribe form → selects "Authorize.net"
        ↓
POST /subscribe
        ↓
Generate ref_id (UUID)
Call Authorize.net API: getHostedPaymentPageRequest → receive token
Save Subscriber(status='pending', payment_provider='authorize', provider_customer_id=ref_id)
Redirect to https://accept.authorize.net/payment/payment?token=TOKEN
        ↓
Client pays with card on Authorize.net hosted page
        ↓
Authorize.net sends Silent Post to POST /subscribe/webhooks/authorize
        ↓
Webhook handler: x_response_code == '1' AND x_invoice_num matches ref_id
→ Subscriber.status = 'active'
        ↓
Authorize.net redirects client to /subscribe/success
```

---

## 3. Pricing

Same as Wave:

| Service | Amount |
|---------|--------|
| Artist Promotion | `custom_amount` (client sets budget, minimum $1) |
| Music Lessons | $100.00 |
| Artist Production | $2,500.00 |

---

## 4. Architecture

### New file: `app/blueprints/subscriptions/providers/authnet.py`

Two public functions:

**`create_hosted_payment(name, email, service_type, amount, ref_id) → str`**
- Calls Authorize.net REST API (`getHostedPaymentPageRequest`)
- Sets `invoiceNum = ref_id` so webhook can match back to subscriber
- Sets `hostedPaymentReturnOptions` with success URL = `/subscribe/success`, cancel URL = `/subscribe/cancel`
- Returns the hosted payment page URL: `https://accept.authorize.net/payment/payment?token=TOKEN`

**`handle_webhook(form_data) → bool`**
- Receives Authorize.net Silent Post (form-encoded, not JSON)
- Checks `x_response_code == '1'` (approved)
- Finds Subscriber by `provider_customer_id == x_invoice_num`
- Sets `status = 'active'`
- Returns True on success

### Modified: `app/blueprints/subscriptions/routes.py`

`subscribe()` POST handler — after validation:
```python
payment_method = request.form.get('payment_method', 'wave')
if payment_method == 'authorize':
    ref_id = str(uuid.uuid4())
    checkout_url = create_hosted_payment(name, email, service_type, amount, ref_id)
    sub = Subscriber(..., payment_provider='authorize', provider_customer_id=ref_id)
else:
    invoice_id, checkout_url = create_invoice(name, email, service_type, custom_amount=amount)
    sub = Subscriber(..., payment_provider='wave', wave_invoice_id=invoice_id)
```

`webhook()` handler for `provider == 'authorize'`:
```python
from .providers.authnet import handle_webhook
handle_webhook(request.form.to_dict())
```

**Note:** For Authorize.net, Subscriber is saved BEFORE redirecting (we need the ref_id in DB before the webhook arrives). For Wave, behaviour is unchanged (save after invoice creation).

### Modified: `app/templates/subscriptions/subscribe.html`

Add payment method selector after the service/amount fields:
- Radio buttons: "Pay with Wave" / "Pay with Authorize.net"
- Default: Wave

---

## 5. Authorize.net API

### Endpoint (Live)
`POST https://api.authorize.net/xml/v1/request.api`

### getHostedPaymentPageRequest
```json
{
  "getHostedPaymentPageRequest": {
    "merchantAuthentication": {
      "name": "AUTHNET_LOGIN_ID",
      "transactionKey": "AUTHNET_TRANSACTION_KEY"
    },
    "transactionRequest": {
      "transactionType": "authCaptureTransaction",
      "amount": "100.00",
      "invoiceNum": "ref_uuid_here",
      "customer": {
        "email": "client@email.com"
      },
      "billTo": {
        "firstName": "Client Name"
      }
    },
    "hostedPaymentSettings": {
      "setting": [
        {
          "settingName": "hostedPaymentReturnOptions",
          "settingValue": "{\"url\": \"https://web-production-f4c2c.up.railway.app/subscribe/success\", \"cancelUrl\": \"https://web-production-f4c2c.up.railway.app/subscribe/cancel\", \"showReceipt\": true}"
        },
        {
          "settingName": "hostedPaymentButtonOptions",
          "settingValue": "{\"text\": \"Pay Now\"}"
        },
        {
          "settingName": "hostedPaymentCustomerOptions",
          "settingValue": "{\"showEmail\": false, \"requiredEmail\": false}"
        }
      ]
    }
  }
}
```

### Hosted Payment URL
`https://accept.authorize.net/payment/payment?token=TOKEN`

---

## 6. Webhook (Silent Post)

Authorize.net POSTs form-encoded data to `/subscribe/webhooks/authorize`.

Key fields:
- `x_response_code`: `1` = approved, `2` = declined, `3` = error
- `x_invoice_num`: our ref_id
- `x_trans_id`: Authorize.net transaction ID
- `x_amount`: amount charged

Handler:
1. Check `x_response_code == '1'`
2. Find `Subscriber` where `provider_customer_id == x_invoice_num`
3. If found and not already active → `status = 'active'`
4. Return 200

Silent Post URL to configure in Authorize.net dashboard:
`https://web-production-f4c2c.up.railway.app/subscribe/webhooks/authorize`

---

## 7. Environment Variables

Add to Railway web service:
```
AUTHNET_LOGIN_ID=<your API Login ID>
AUTHNET_TRANSACTION_KEY=<your Transaction Key>
```

Add to `.env.example`:
```
AUTHNET_LOGIN_ID=
AUTHNET_TRANSACTION_KEY=
```

**Where to find credentials in Authorize.net dashboard:**
Account → Settings → Security Settings → API Credentials & Keys

---

## 8. Error Handling

- Authorize.net API unreachable → flash error, re-render form, do NOT save Subscriber
- API returns error result code → log error, flash generic message, do NOT save Subscriber
- Webhook arrives for unknown ref_id → return 200 (idempotent, ignore)
- Webhook arrives for already-active subscriber → return 200 (no-op)

---

## 9. Testing

- `tests/test_authnet_provider.py` — 5 unit tests mocking `requests.post`
- `tests/test_subscriptions.py` — add 2 tests: Authorize.net POST flow, Authorize.net webhook

---

## 10. Out of Scope

- Recurring billing via Authorize.net ARB
- Refunds via API
- Webhook signature verification (configure IP allowlist in Authorize.net dashboard instead)
- Storing full card data
