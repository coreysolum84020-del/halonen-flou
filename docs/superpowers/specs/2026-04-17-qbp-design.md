# QuickBooks Payments Integration Design

**Date:** 2026-04-17
**Owner:** Brent Halonen
**Stack:** Flask · SQLAlchemy · QuickBooks Payments API · OAuth 2.0

---

## 1. Business Context

Authorize.net was rejected for live processing. QuickBooks Payments replaces it as the second payment option alongside Wave on the subscribe form.

---

## 2. Payment Flow

```
Client fills /subscribe form → selects "QuickBooks Payments"
        ↓
Intuit.js tokenizes card client-side → card_token
        ↓
POST /subscribe (with card_token)
        ↓
qbp.charge_card(name, email, service_type, amount, card_token)
→ POST https://api.intuit.com/quickbooks/v4/payments/charges
→ Synchronous response: CAPTURED or error
        ↓
On success:
Save Subscriber(status='active', payment_provider='quickbooks', provider_customer_id=charge_id)
Redirect to /subscribe/success
```

No webhook needed — charge is synchronous.

---

## 3. Pricing

Same as before:

| Service | Amount |
|---------|--------|
| Artist Promotion | `custom_amount` (minimum $1) |
| Music Lessons | $100.00 |
| Artist Production | $2,500.00 |

---

## 4. Architecture

### New model: `AppConfig` in `app/models.py`

Stores OAuth tokens between requests:

```python
class AppConfig(db.Model):
    __tablename__ = 'app_config'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=True)
```

Keys used:
- `qbp_access_token` — expires every 3600 seconds
- `qbp_refresh_token` — expires every 100 days
- `qbp_token_expiry` — Unix timestamp (float) when access token expires

### New blueprint: `app/blueprints/setup/`

Two routes for one-time OAuth setup:

**`GET /setup/qbp`**
Redirects to Intuit OAuth URL:
```
https://appcenter.intuit.com/connect/oauth2
  ?client_id=QBP_CLIENT_ID
  &redirect_uri=https://web-production-f4c2c.up.railway.app/setup/qbp/callback
  &response_type=code
  &scope=com.intuit.quickbooks.payment
  &state=<random>
```

**`GET /setup/qbp/callback`**
Exchanges auth code for tokens, saves to `AppConfig`, returns confirmation page.

### New file: `app/blueprints/subscriptions/providers/qbp.py`

Three public functions:

**`get_access_token() → str`**
- Reads `qbp_access_token` and `qbp_token_expiry` from `AppConfig`
- If expired: calls refresh endpoint, saves new tokens, returns new access token
- Raises `RuntimeError` if no tokens exist (OAuth not set up yet)

**`charge_card(name, email, service_type, amount, card_token) → str`**
- Gets access token via `get_access_token()`
- POSTs to `https://api.intuit.com/quickbooks/v4/payments/charges`
- Request body: `{"amount": "100.00", "currency": "USD", "card": {"token": card_token}, "capture": true}`
- Returns `charge_id` on success (`status == "CAPTURED"`)
- Raises `RuntimeError` on failure

**Token refresh (internal)**
- `POST https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer`
- Body: `grant_type=refresh_token&refresh_token=...`
- Auth: Basic with client_id:client_secret

### Modified: `app/blueprints/subscriptions/routes.py`

Remove Authorize.net branch entirely. Add QuickBooks Payments branch:

```python
elif payment_method == 'quickbooks':
    card_token = request.form.get('card_token', '').strip()
    if not card_token:
        errors['card_token'] = 'Card details required.'
    else:
        charge_id = charge_card(name, email, service_type, amount, card_token)
        sub = Subscriber(..., payment_provider='quickbooks',
                         provider_customer_id=charge_id, status='active')
        db.session.add(sub)
        db.session.commit()
        return redirect(url_for('subscriptions.success'))
```

### Modified: `app/templates/subscriptions/subscribe.html`

Replace Authorize.net radio button with QuickBooks Payments. Add card fields section that shows/hides based on selected payment method:

```html
<!-- shown only when quickbooks selected -->
<div id="qbp-card-form" style="display:none;">
  <div id="intuit-card-container"></div>
  <input type="hidden" name="card_token" id="card_token">
</div>
```

Intuit.js script initialises the card container, tokenises on submit, and populates `card_token`.

### Removed files

- `app/blueprints/subscriptions/providers/authnet.py`
- `app/templates/subscriptions/authnet_redirect.html`

### Modified: `app/config.py`

```python
QBP_CLIENT_ID = os.environ.get('QBP_CLIENT_ID', '')
QBP_CLIENT_SECRET = os.environ.get('QBP_CLIENT_SECRET', '')
```

---

## 5. QuickBooks Payments API

### Charge endpoint
`POST https://api.intuit.com/quickbooks/v4/payments/charges`

Headers:
```
Authorization: Bearer {access_token}
Content-Type: application/json
Request-Id: {uuid4}
```

Body:
```json
{
  "amount": "100.00",
  "currency": "USD",
  "card": {
    "token": "{card_token_from_intuit_js}"
  },
  "capture": true
}
```

Success response: `status == "CAPTURED"`, `id` = charge ID.

### Token refresh endpoint
`POST https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer`

Headers:
```
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded
```

Body: `grant_type=refresh_token&refresh_token={token}`

Response: `access_token`, `refresh_token`, `expires_in`

---

## 6. OAuth Setup (one-time)

After deploy:

1. In Intuit developer portal → app settings → add redirect URI:
   `https://web-production-f4c2c.up.railway.app/setup/qbp/callback`

2. Visit `https://web-production-f4c2c.up.railway.app/setup/qbp` in browser

3. Log in with QuickBooks Payments account → authorize

4. Callback saves tokens to DB → done

---

## 7. Environment Variables

Add to Railway:
```
QBP_CLIENT_ID=ABlMujiurwLQLgcLAT3FZU44kYw4nHmpUqFdox1EDvJleu0m1E
QBP_CLIENT_SECRET=NlUffw93rDT1QMFf0cvBaNSC7M0c8pTWhG5CeA35
```

Remove (no longer needed):
```
AUTHNET_LOGIN_ID
AUTHNET_TRANSACTION_KEY
```

---

## 8. Error Handling

- No tokens in DB → flash error "Payment setup incomplete", do NOT save Subscriber
- Charge declined → flash "Your card was declined. Please try again."
- QBP API unreachable → flash generic unavailable message
- Token refresh fails → same generic message, log error

---

## 9. Testing

- `tests/test_qbp_provider.py` — unit tests mocking `requests.post`:
  - `test_charge_card_returns_charge_id`
  - `test_charge_card_raises_on_declined`
  - `test_charge_card_raises_on_api_error`
  - `test_get_access_token_refreshes_when_expired`

- `tests/test_subscriptions.py` — add 1 test:
  - `test_subscribe_qbp_post_saves_active_subscriber`

- Remove authnet tests from `tests/test_authnet_provider.py` and `tests/test_subscriptions.py`

---

## 10. Out of Scope

- ACH / bank transfer via QBP
- Refunds via API
- Storing card data
- Multi-currency
