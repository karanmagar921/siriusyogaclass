from django.core.mail import send_mail
from django.conf import settings


def _fmt_session(booking):
    if booking.session:
        return (
            f"{booking.session.date.strftime('%A, %B %d, %Y')} "
            f"at {booking.session.start_time.strftime('%I:%M %p')} — "
            f"{booking.session.end_time.strftime('%I:%M %p')}"
        )
    return str(booking.booking_date)


# ── 1. Instant email to STUDENT when they submit a booking ──────────────────
def send_booking_received_email(booking):
    name = booking.user.get_full_name() or booking.user.username
    subject = f"📩 Booking Received — {booking.yoga_class.name}"
    message = f"""Hi {name},

Thanks for booking with Sirius Yoga! We have received your request and the owner will review it shortly.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOOKING DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Class      : {booking.yoga_class.name}
Instructor : {booking.yoga_class.instructor.name if booking.yoga_class.instructor else 'TBA'}
Session    : {_fmt_session(booking)}
Duration   : {booking.yoga_class.duration_minutes} minutes
Price      : A${booking.yoga_class.price}
Status     : Pending confirmation ⏳

You will receive another email once your booking is confirmed.
You can view your bookings at any time: http://127.0.0.1:8000/bookings/

Namaste 🙏
Sirius Yoga
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [booking.user.email], fail_silently=False)
    except Exception as e:
        print(f"Email error (booking received): {e}")


# ── 2. Email to OWNER when a student books ──────────────────────────────────
def send_booking_notification_to_owner(booking):
    name = booking.user.get_full_name() or booking.user.username
    subject = f"🔔 New Booking Request — {booking.yoga_class.name}"
    message = f"""A new booking request has been submitted on Sirius Yoga.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STUDENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name    : {name}
Email   : {booking.user.email}
Phone   : {booking.user.profile.phone if hasattr(booking.user, 'profile') and booking.user.profile.phone else 'Not provided'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLASS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Class   : {booking.yoga_class.name}
Session : {_fmt_session(booking)}
Notes   : {booking.notes or 'None'}

➡ Accept or Reject: http://127.0.0.1:8000/manage/bookings/
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.OWNER_EMAIL], fail_silently=False)
    except Exception as e:
        print(f"Email error (owner notification): {e}")


# ── 3. Email to STUDENT when owner ACCEPTS ──────────────────────────────────
def send_booking_accepted_email(booking):
    name = booking.user.get_full_name() or booking.user.username
    subject = f"✅ Booking Confirmed! — {booking.yoga_class.name}"
    message = f"""Hi {name},

Great news — your booking has been CONFIRMED by Sirius Yoga! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFIRMED BOOKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Class      : {booking.yoga_class.name}
Instructor : {booking.yoga_class.instructor.name if booking.yoga_class.instructor else 'TBA'}
Session    : {_fmt_session(booking)}
Duration   : {booking.yoga_class.duration_minutes} minutes
Price      : A${booking.yoga_class.price}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO BRING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{booking.yoga_class.what_to_bring}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAYMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{'✅ Already paid via membership pass — no further action needed.' if booking.payment_status == 'free' else f'💳 Please complete your payment at: http://127.0.0.1:8000/bookings/'}

We look forward to seeing you on the mat!

Namaste 🙏
Sirius Yoga
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [booking.user.email], fail_silently=False)
    except Exception as e:
        print(f"Email error (booking accepted): {e}")


# ── 4. Email to STUDENT when owner REJECTS ──────────────────────────────────
def send_booking_rejected_email(booking):
    name = booking.user.get_full_name() or booking.user.username
    subject = f"❌ Booking Unavailable — {booking.yoga_class.name}"
    message = f"""Hi {name},

Thank you for your interest in Sirius Yoga.

Unfortunately we were unable to confirm your booking for:

Class   : {booking.yoga_class.name}
Session : {_fmt_session(booking)}

This may be due to capacity limits or scheduling conflicts.
Please browse other available sessions: http://127.0.0.1:8000/schedule/

We hope to see you on the mat soon!

Namaste 🙏
Sirius Yoga
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [booking.user.email], fail_silently=False)
    except Exception as e:
        print(f"Email error (booking rejected): {e}")


# ── 5. Email to STUDENT when a waitlist spot opens ──────────────────────────
def send_waitlist_notification(waitlist_entry):
    name = waitlist_entry.user.get_full_name() or waitlist_entry.user.username
    subject = f"🎉 Spot Available — {waitlist_entry.session.yoga_class.name}"
    message = f"""Hi {name},

A spot has just opened up in a class you're waiting for!

Class   : {waitlist_entry.session.yoga_class.name}
Date    : {waitlist_entry.session.date.strftime('%A, %B %d, %Y')}
Time    : {waitlist_entry.session.start_time.strftime('%I:%M %p')}

Book now before it fills up: http://127.0.0.1:8000/session/{waitlist_entry.session.pk}/book/

Namaste 🙏
Sirius Yoga
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [waitlist_entry.user.email], fail_silently=False)
    except Exception as e:
        print(f"Email error (waitlist): {e}")


# ── 6. Payment receipt ───────────────────────────────────────────────────────
def send_payment_receipt_email(booking, payment):
    name = booking.user.get_full_name() or booking.user.username
    subject = f"🧾 Payment Receipt — {booking.yoga_class.name}"
    message = f"""Hi {name},

Thank you for your payment! Here is your receipt.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAYMENT RECEIPT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Transaction ID : {payment.transaction_id}
Date           : {payment.created_at.strftime('%A, %B %d, %Y at %I:%M %p')}
Amount Paid    : A${payment.amount}
Payment Method : Card

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLASS DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Class      : {booking.yoga_class.name}
Instructor : {booking.yoga_class.instructor.name if booking.yoga_class.instructor else 'TBA'}
Session    : {_fmt_session(booking)}
Duration   : {booking.yoga_class.duration_minutes} minutes

What to bring:
{booking.yoga_class.what_to_bring}

See you on the mat! 🧘

Namaste 🙏
Sirius Yoga
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [booking.user.email], fail_silently=False)
    except Exception as e:
        print(f"Email error (receipt): {e}")


# ── 7. Reminder (optional future use) ───────────────────────────────────────
def send_booking_reminder(booking):
    name = booking.user.get_full_name() or booking.user.username
    subject = f"⏰ Reminder — {booking.yoga_class.name} Tomorrow"
    message = f"""Hi {name},

Just a reminder that you have a class tomorrow!

Class      : {booking.yoga_class.name}
Session    : {_fmt_session(booking)}
What to bring: {booking.yoga_class.what_to_bring}

See you on the mat! 🧘
Sirius Yoga
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [booking.user.email], fail_silently=False)
    except Exception as e:
        print(f"Email error (reminder): {e}")


def send_payment_receipt_to_admin(payment, user, description):
    """Send payment receipt to the owner/admin."""
    # Strip newlines from subject (email headers cannot have newlines)
    desc_short = description.replace('\n', ' | ').replace('\r', '').split('|')[0].strip()[:60]
    subject = f"Payment Received A${payment.amount} — {desc_short}"
    message = f"""A payment has been received on Sirius Yoga.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAYMENT RECEIPT — ADMIN COPY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Transaction ID : {payment.transaction_id}
Date           : {payment.created_at.strftime('%A, %B %d, %Y at %I:%M %p')}
Amount         : A${payment.amount}
Payment Method : Card

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CUSTOMER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name    : {user.get_full_name() or user.username}
Email   : {user.email}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{description}

View all payments: http://127.0.0.1:8000/manage/payments/
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                  [settings.OWNER_EMAIL], fail_silently=False)
    except Exception as e:
        print(f"Admin receipt email error: {e}")


def send_membership_receipt_email(membership, payment):
    """Send membership purchase receipt to customer."""
    name = membership.user.get_full_name() or membership.user.username
    subject = f"🧾 Pass Receipt — {membership.plan.name}"
    message = f"""Hi {name},

Thank you for purchasing a pass! Here is your receipt.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAYMENT RECEIPT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Transaction ID : {payment.transaction_id}
Date           : {payment.created_at.strftime('%A, %B %d, %Y at %I:%M %p')}
Amount Paid    : A${payment.amount}
Payment Method : Card

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASS DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pass       : {membership.plan.name}
Type       : {membership.plan.get_plan_type_display()}
Valid From : {membership.start_date.strftime('%B %d, %Y')}
Valid Until: {membership.end_date.strftime('%B %d, %Y')}
Classes    : {'Unlimited' if membership.plan.plan_type == 'unlimited' else f'{membership.plan.classes_included} classes'}

Your pass is now active and ready to use.
Book your next class: http://127.0.0.1:8000/classes/

Namaste 🙏
Sirius Yoga
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                  [membership.user.email], fail_silently=False)
    except Exception as e:
        print(f"Membership receipt email error: {e}")


def send_class_reminder(booking, hours_before):
    """Send reminder email to student and admin before class."""
    name = booking.user.get_full_name() or booking.user.username
    session = booking.session
    if not session:
        return

    when = f"{'Tomorrow' if hours_before == 24 else 'In 1 hour'}"
    subject = f"⏰ Reminder: {booking.yoga_class.name} {when}"
    student_msg = f"""Hi {name},

Just a reminder — your class is coming up {when.lower()}!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLASS DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Class      : {booking.yoga_class.name}
Date       : {session.date.strftime('%A, %B %d, %Y')}
Time       : {session.start_time.strftime('%I:%M %p')} – {session.end_time.strftime('%I:%M %p')}
Instructor : {booking.yoga_class.instructor.name if booking.yoga_class.instructor else 'TBA'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO BRING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{booking.yoga_class.what_to_bring}

See you on the mat! 🧘
Namaste,
Sirius Yoga
"""
    admin_msg = f"""CLASS REMINDER — {hours_before}h notice

Student    : {name} ({booking.user.email})
Class      : {booking.yoga_class.name}
Date       : {session.date.strftime('%A, %B %d, %Y')}
Time       : {session.start_time.strftime('%I:%M %p')} – {session.end_time.strftime('%I:%M %p')}
Booking ID : {booking.pk}
"""
    try:
        send_mail(subject, student_msg, settings.DEFAULT_FROM_EMAIL,
                  [booking.user.email], fail_silently=True)
        send_mail(f"[ADMIN] {subject}", admin_msg, settings.DEFAULT_FROM_EMAIL,
                  [settings.OWNER_EMAIL], fail_silently=True)
    except Exception as e:
        print(f"Reminder email error: {e}")
