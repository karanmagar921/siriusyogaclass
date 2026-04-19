# 🌟 Sirius Yoga — Full-Featured Django Studio App

Inspired by Momence.com — a complete yoga & pilates studio platform with real-time session booking,
waitlists, class passes, instructor profiles, cancellation policies, and email notifications.

---

## 🚀 Quick Start

```bash
pip install django pillow
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Visit: **http://127.0.0.1:8000/**

Admin: **http://127.0.0.1:8000/admin/** → `admin` / `admin123`

---

## 📧 Email Setup (Gmail App Password)

1. Go to your Google Account → Security → 2-Step Verification → **App Passwords**
2. Create an App Password for "Mail"
3. In `sirius_yoga/settings.py`, update:

```python
EMAIL_HOST_PASSWORD = 'your-16-char-app-password'
```

---

## ✨ Features (Momence-Inspired)

### 📅 Schedule & Sessions
- **Weekly calendar view** (`/schedule/`) — browse by week, navigate forward/backward
- **Specific date/time sessions** — each class has real bookable instances (not just "Mondays")
- **83 sessions pre-generated** across 4 weeks for all 8 classes
- **Spots remaining counter** — live count shown on every session
- **Low spots warning** — highlighted when ≤ 3 spots left
- **Full class indicator** — visual cue when sessions are at capacity

### ⏳ Waitlist System
- Join waitlist on full sessions
- Automatic email notification when a spot opens
- Leave waitlist at any time from My Bookings

### 🎫 Passes & Memberships
- **Single class drop-in** — A$25
- **5-class pack** (60 days) — A$110
- **10-class pack** (90 days) — A$200
- **Unlimited monthly** — A$120
- Passes auto-apply on booking — no separate payment step
- Pack credits returned automatically on cancellation

### 🧘 Classes & Instructors
- 8 classes: Vinyasa, Hatha, Power Yoga, Yin, Prenatal, Reformer ×2, Breathwork
- 5 instructor profiles with bios, specialties, certifications
- Instructor detail pages with their class listings
- **Category + Level dual filters** on class listing
- **Prerequisites notes** (e.g., "Must complete Reformer Foundations first")
- **Related classes** sidebar on class detail
- **What to bring** section per class

### 📋 Booking & Cancellations
- Per-class **cancellation deadline** (8–24 hours before session)
- Countdown to deadline shown on session page
- Membership credit auto-returned on valid cancellation
- Waitlist auto-notified when booking is cancelled

### 💳 Payments
- Simulated card payment with **live card preview** UI
- Per-session price (can be overridden per session in admin)
- Membership payment for passes
- Transaction IDs generated for every payment

### ⭐ Reviews & Ratings
- Star rating widget (1–5) with hover interaction
- Average rating displayed on class cards and detail pages
- One review per user per class

### 👤 User Profiles
- Avatar upload
- Emergency contact storage
- Health notes (shared privately with instructors)
- Active passes displayed on profile

### 🔧 Owner Features
- Full Django admin at `/admin/`
- **Manage Bookings** dashboard at `/manage/bookings/`
- Accept / Reject / Mark Attended per booking
- Email sent to student on accept or reject
- Filter bookings by status
- Session-level inline editing in admin (add sessions directly on class)

---

## 🗺️ URL Map

| URL | Page |
|-----|------|
| `/` | Home with upcoming sessions |
| `/schedule/` | Weekly calendar |
| `/classes/` | All classes (filtered) |
| `/classes/<id>/` | Class detail + sessions list |
| `/session/<id>/` | Session detail + booking widget |
| `/session/<id>/book/` | Booking confirmation |
| `/session/<id>/waitlist/` | Join waitlist |
| `/instructors/` | Instructor listing |
| `/instructors/<id>/` | Instructor bio + classes |
| `/pricing/` | Passes & memberships + FAQ |
| `/pricing/<id>/buy/` | Purchase a pass |
| `/bookings/` | My bookings + waitlist + passes |
| `/manage/bookings/` | Owner booking dashboard |
| `/admin/` | Django admin (staff only) |

---

## 🗂️ Project Structure

```
sirius_yoga/
├── core/
│   ├── models.py          ← YogaClass, ClassSession, Booking, Waitlist,
│   │                          MembershipPlan, UserMembership, Instructor, Review, Payment
│   ├── views.py           ← All views including schedule, sessions, waitlist, passes
│   ├── forms.py           ← All forms
│   ├── admin.py           ← Customized admin with inline sessions
│   ├── utils.py           ← Email: booking, accepted, rejected, waitlist, reminder
│   └── management/commands/seed_data.py  ← Seeds 8 classes, 5 instructors, 4 plans, 83 sessions
├── templates/
│   ├── base.html          ← Full navbar with Schedule, Instructors, Pricing
│   ├── home.html          ← Homepage with upcoming sessions strip
│   ├── schedule.html      ← Weekly calendar with navigation
│   ├── classes.html       ← Dual filter (category + level)
│   ├── class_detail.html  ← Sessions list, instructor card, related classes
│   ├── session_detail.html ← Book/Waitlist/Cancel, cancellation policy, share link
│   ├── book_session.html  ← Confirmation with membership auto-apply
│   ├── my_bookings.html   ← Bookings + waitlist + active passes
│   ├── instructors.html
│   ├── instructor_detail.html
│   ├── pricing.html       ← Plans + FAQ accordion
│   ├── buy_membership.html
│   ├── manage_bookings.html ← Accept/Reject/Attended + filters
│   ├── payment.html       ← Card payment with live preview
│   ├── profile.html       ← Health notes + emergency contact
│   ├── register.html / login.html
│   ├── about.html / contact.html
├── static/css/style.css   ← Full design system
└── requirements.txt
```

---

## 🔐 Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Owner/Admin | `admin` | `admin123` |

> Change before going live!

---

Namaste 🙏
