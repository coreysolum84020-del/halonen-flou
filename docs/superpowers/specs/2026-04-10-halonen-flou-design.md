# HALONEN FLOU — Website Design Spec

**Date:** 2026-04-10  
**Owner:** Brent Halonen  
**Stack:** Python · Flask · Jinja2 · SQLAlchemy · SQLite (dev) / PostgreSQL (prod)

---

## 1. Business Context

**Company:** HALONEN FLOU  
**Owner:** Brent Halonen  
**Email:** bluealikeu@gmail.com  
**Phone:** +19295039212  

**Services:**
- Artist Promotion — social media campaigns, PR, playlist pitching
- Music Lessons — guitar, piano, voice, production (all skill levels)
- Artist Production — studio production, mixing, mastering

**Business model:** Daily subscriptions for all three services. No long-term commitment.  
**Language:** English only.  
**Audience:** Musicians, emerging artists, music enthusiasts.

---

## 2. Design Direction

**Style:** Neon Urban  
- Dark background (`#0a0a0a`, `#0d0d0d`)
- Primary accent: purple (`#8a2be2`) with neon glow
- Secondary accent: electric blue (`#00bfff`)
- Typography: sans-serif, uppercase headings, wide letter-spacing
- Visual motifs: sound bars, gradient glows, thin neon dividers
- No existing logo or brand assets — created from scratch in CSS

**Color palette:**
| Role | Value |
|------|-------|
| Background | `#0a0a0a` |
| Surface | `#0d0d0d`, `#120926` |
| Primary | `#8a2be2` (BlueViolet) |
| Secondary | `#00bfff` (DeepSkyBlue) |
| Text primary | `#ffffff` |
| Text secondary | `#999999` |
| Border | `rgba(138,43,226,0.3)` |

---

## 3. Site Structure

```
/ (Home)
/about
/services
  /services/promotion
  /services/lessons
  /services/production
/artists
/contact
```

### Pages

**/ Home**
- Navbar (sticky, glassmorphism blur)
- Hero: "We Make Artists Shine." + stats (50+ Artists, 3 Services, 5★, 10y)
- Services preview (3 cards with daily prices)
- Featured Artists (Nova Raines, DJ Kaleo, Zara Vex)
- Subscription CTA banner
- Footer

**/ About**
- Brent Halonen bio + portrait placeholder
- Mission statement
- Company values (3 pillars)
- Timeline / our story

**/ Services**
- Overview grid of all 3 services
- Individual service detail sections with:
  - Full description
  - What's included
  - Price (fixed or custom input for Promotion)
  - FAQ (3–5 questions)
  - Subscribe / Book CTA button

**/ Artists**
- Portfolio grid of fictional case studies:
  - **Nova Raines** — R&B/Soul, +340% streams via promotion package
  - **DJ Kaleo** — Electronic/House, signed to label after production work
  - **Zara Vex** — Alt-Rock/Indie, grew to 50K followers in 6 months
  - **Marcus Cole** — Hip-Hop, released debut album after music lessons
  - **Lia Frost** — Pop, viral TikTok campaign through promotion service
- Each artist: avatar (CSS gradient), genre, service used, key metric, short story

**/ Contact**
- Contact info (email + phone)
- Contact form (Name, Email, Subject, Message, Submit)
- Form submission via Flask-Mail or stored in DB + email notification

---

## 4. Flask Project Architecture

```
halonen-flou/
├── app/
│   ├── __init__.py          # App factory, register blueprints
│   ├── config.py            # Config classes (Dev, Prod)
│   ├── models.py            # ContactMessage, Subscriber models
│   ├── extensions.py        # db, mail, csrf instances
│   ├── blueprints/
│   │   ├── main/            # Home, About, Artists
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── services/        # Services pages
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── contact/         # Contact form handling
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   └── subscriptions/   # Payment-ready subscription stub
│   │       ├── __init__.py
│   │       └── routes.py
│   ├── templates/
│   │   ├── base.html        # Layout, nav, footer, CSS/JS includes
│   │   ├── index.html
│   │   ├── about.html
│   │   ├── services.html
│   │   ├── artists.html
│   │   └── contact.html
│   └── static/
│       ├── css/
│       │   └── main.css     # Neon Urban theme
│       ├── js/
│       │   └── main.js      # Scroll animations, nav effects
│       └── img/
├── migrations/
├── tests/
├── .env.example
├── requirements.txt
├── run.py
└── README.md
```

---

## 5. Data Models

```python
# ContactMessage
id, name, email, subject, message, created_at, is_read

# Subscriber (payment-ready stub)
id, email, name, service_type, plan_type='daily',
status='pending', stripe_customer_id, created_at
```

---

## 6. Payment Integration Architecture (Future)

The `subscriptions` blueprint is pre-wired as a stub with clear integration points:

- `POST /subscribe` — create subscriber record, redirect to payment
- `POST /webhooks/<provider>` — handle payment events (activate/cancel)
- `GET /subscribe/success` — confirmation page
- `GET /subscribe/cancel` — cancellation page

**Supported providers (plug-in ready):**
- Helcim, Authorize.net, CashApp Pay, QuickBooks Payments, Melio, Wave

Each provider gets its own module in `app/blueprints/subscriptions/providers/`. The `Subscriber` model uses `status` field (`pending` → `active` → `cancelled`) compatible with all provider webhook patterns.

---

## 7. Fictional Artist Case Studies

| Artist | Genre | Service | Key Result |
|--------|-------|---------|------------|
| Nova Raines | R&B · Soul | Promotion | +340% streams in 3 months |
| DJ Kaleo | Electronic · House | Production | Signed to Arista Records |
| Zara Vex | Alt-Rock · Indie | Promotion | 50K Instagram followers |
| Marcus Cole | Hip-Hop | Lessons + Production | Released debut album |
| Lia Frost | Pop | Promotion | 2M TikTok views, viral |

---

## 8. Pricing

| Service | Price | Model |
|---------|-------|-------|
| Daily Subscription | $500/day | Fixed, daily billing |
| Music Lessons | $100/hour | Hourly, billed per session |
| Artist Promotion | Client sets price | Custom quote — client enters amount |
| Artist Production | $2,500 | Fixed project fee |

**Notes:**
- Artist Promotion uses a "pay what you want" / custom quote input — client enters their own budget on the subscribe/checkout form
- Music Lessons billed per hour, not per day
- Artist Production is a flat project fee (not daily)

---

## 9. Non-Goals (Out of Scope for v1)

- User authentication / member portal
- Blog / CMS
- Multilingual support
- Actual payment processing (stubs only)
- Admin dashboard
