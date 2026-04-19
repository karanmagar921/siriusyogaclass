import uuid
import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import (YogaClass, ClassSession, Booking, Review, UserProfile,
                     Payment, ContactMessage, Schedule, Waitlist, MembershipPlan,
                     UserMembership, Instructor)
from .forms import (RegisterForm, LoginForm, ReviewForm, SessionBookingForm,
                    PaymentForm, UserProfileForm, ContactForm)
from .utils import (send_booking_notification_to_owner, send_booking_accepted_email,
                    send_booking_rejected_email, send_waitlist_notification,
                    send_payment_receipt_email, send_booking_received_email)


# ─── PUBLIC PAGES ────────────────────────────────────────────────────────────

def home(request):
    classes = YogaClass.objects.filter(is_active=True).prefetch_related('reviews')[:6]
    reviews = Review.objects.select_related('user', 'yoga_class').order_by('-created_at')[:6]
    upcoming = ClassSession.objects.filter(
        date__gte=timezone.now().date(),
        status='scheduled'
    ).select_related('yoga_class', 'yoga_class__instructor').order_by('date', 'start_time')[:5]
    return render(request, 'home.html', {'classes': classes, 'reviews': reviews, 'upcoming': upcoming})


def classes_list(request):
    level = request.GET.get('level', '')
    category = request.GET.get('category', '')
    classes = YogaClass.objects.filter(is_active=True).prefetch_related('reviews')
    if level:
        classes = classes.filter(level=level)
    if category:
        classes = classes.filter(category=category)
    categories = YogaClass.CATEGORY_CHOICES
    return render(request, 'classes.html', {
        'classes': classes,
        'selected_level': level,
        'selected_category': category,
        'categories': categories,
    })


def class_detail(request, pk):
    yoga_class = get_object_or_404(YogaClass, pk=pk, is_active=True)
    reviews = yoga_class.reviews.select_related('user').order_by('-created_at')
    # Upcoming sessions for this class (next 30 days)
    today = timezone.now().date()
    sessions = ClassSession.objects.filter(
        yoga_class=yoga_class,
        date__gte=today,
        date__lte=today + datetime.timedelta(days=30),
        status__in=['scheduled', 'unavailable']
    ).order_by('date', 'start_time')
    related_classes = YogaClass.objects.filter(
        is_active=True, category=yoga_class.category
    ).exclude(pk=pk)[:3]
    user_review = None
    review_form = None
    user_booked_sessions = set()

    if request.user.is_authenticated:
        user_review = Review.objects.filter(user=request.user, yoga_class=yoga_class).first()
        if not user_review:
            review_form = ReviewForm()
        user_booked_sessions = set(
            Booking.objects.filter(
                user=request.user, session__in=sessions,
                status__in=['pending', 'accepted']
            ).values_list('session_id', flat=True)
        )
    user_waitlist_sessions = set()
    if request.user.is_authenticated:
        user_waitlist_sessions = set(
            Waitlist.objects.filter(
                user=request.user, session__in=sessions, status='waiting'
            ).values_list('session_id', flat=True)
        )

    return render(request, 'class_detail.html', {
        'yoga_class': yoga_class,
        'reviews': reviews,
        'sessions': sessions,
        'related_classes': related_classes,
        'user_review': user_review,
        'review_form': review_form,
        'user_booked_sessions': user_booked_sessions,
        'user_waitlist_sessions': user_waitlist_sessions,
    })


def session_detail(request, session_pk):
    session = get_object_or_404(ClassSession, pk=session_pk, status__in=['scheduled', 'unavailable', 'cancelled', 'completed'])
    yoga_class = session.yoga_class
    user_booking = None
    user_waitlist = None
    in_cart = False
    form = SessionBookingForm()

    if request.user.is_authenticated:
        user_booking = Booking.objects.filter(
            user=request.user, session=session, status__in=['pending', 'accepted', 'attended']
        ).first()
        user_waitlist = Waitlist.objects.filter(
            user=request.user, session=session, status='waiting'
        ).first()
        from .models import CartItem
        in_cart = CartItem.objects.filter(user=request.user, session=session).exists()

    return render(request, 'session_detail.html', {
        'session': session,
        'yoga_class': yoga_class,
        'form': form,
        'user_booking': user_booking,
        'user_waitlist': user_waitlist,
        'in_cart': in_cart,
    })


def schedule_view(request):
    """Full weekly/monthly schedule view."""
    today = timezone.now().date()
    week_offset = int(request.GET.get('week', 0))
    # Start from today for week 0, from Monday for other weeks
    if week_offset == 0:
        week_start = today
    else:
        monday = today - datetime.timedelta(days=today.weekday())
        week_start = monday + datetime.timedelta(weeks=week_offset)
    week_end = week_start + datetime.timedelta(days=6)
    sessions = ClassSession.objects.filter(
        date__range=[week_start, week_end],
    ).select_related('yoga_class', 'yoga_class__instructor').order_by('date', 'start_time')

    # For admin: attach bookings to each session
    session_bookings = {}
    if request.user.is_staff:
        all_bookings = Booking.objects.filter(
            session__in=sessions,
            status__in=['pending', 'accepted', 'attended']
        ).select_related('user').order_by('created_at')
        for b in all_bookings:
            session_bookings.setdefault(b.session_id, []).append(b)

    # Group by day
    days = []
    for i in range(7):
        day_date = week_start + datetime.timedelta(days=i)
        day_sessions = [s for s in sessions if s.date == day_date]
        days.append({'date': day_date, 'sessions': day_sessions})

    user_booked = set()
    cart_session_ids = set()
    if request.user.is_authenticated:
        user_booked = set(
            Booking.objects.filter(
                user=request.user, session__in=sessions,
                status__in=['pending', 'accepted', 'attended']
            ).values_list('session_id', flat=True)
        )
        from .models import CartItem
        cart_session_ids = set(
            CartItem.objects.filter(
                user=request.user, session__in=sessions
            ).values_list('session_id', flat=True)
        )

    return render(request, 'schedule.html', {
        'days': days,
        'week_start': week_start,
        'week_end': week_end,
        'week_offset': week_offset,
        'prev_week': week_offset - 1,
        'next_week': week_offset + 1,
        'user_booked': user_booked,
        'cart_session_ids': cart_session_ids,
        'today': today,
        'session_bookings': session_bookings,
    })


def instructors_view(request):
    instructors = Instructor.objects.filter(is_active=True)
    return render(request, 'instructors.html', {'instructors': instructors})


def instructor_detail(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk, is_active=True)
    classes = instructor.classes.filter(is_active=True)
    return render(request, 'instructor_detail.html', {'instructor': instructor, 'classes': classes})


def pricing_view(request):
    plans = MembershipPlan.objects.filter(is_active=True).order_by('price')
    faq = [
        ("Can I use a class pack across different class types?", "Yes! All class packs and memberships can be used for any class at Sirius Yoga, including yoga, pilates, reformer, meditation, and breathwork sessions."),
        ("What happens if I cancel a booking?", "You can cancel up to the class's cancellation deadline (usually 12–24 hours before). If you paid individually, you'll receive a credit. If you used a class pack, your class is returned automatically."),
        ("Do class packs expire?", "Yes. The 5-class pack is valid for 60 days, and the 10-class pack for 90 days. Unlimited monthly memberships run for 30 days from purchase."),
        ("Can I freeze my membership?", "Please contact us directly to discuss freezing your membership due to injury, travel, or illness. We're flexible and happy to help."),
        ("Is there a waitlist if a class is full?", "Yes! You can join the waitlist for any full class. If a spot opens up, you'll be automatically notified by email."),
    ]
    return render(request, 'pricing.html', {'plans': plans, 'faq': faq})


# ─── BOOKING ─────────────────────────────────────────────────────────────────

@login_required
def book_session(request, session_pk):
    """Add session to cart and redirect to cart — enforces cart-first flow."""
    session = get_object_or_404(ClassSession, pk=session_pk)
    if session.status != 'scheduled':
        messages.error(request, '⛔ This session is not available for booking.')
        return redirect('class_booking_page', slug=session.yoga_class.slug)
    yoga_class = session.yoga_class

    if session.is_past:
        messages.error(request, 'This session has already passed.')
        return redirect('class_booking_page', slug=yoga_class.slug)

    # Already booked?
    existing = Booking.objects.filter(
        user=request.user, session=session, status__in=['pending', 'accepted']
    ).first()
    if existing:
        messages.info(request, 'You already have a booking for this session.')
        return redirect('my_bookings')

    # Class is full → offer waitlist
    if session.is_full:
        messages.warning(request, 'This session is full. Join the waitlist below.')
        return redirect('session_detail', session_pk=session_pk)

    # ── Cart-first: add to cart then redirect to cart ──
    if request.method == 'POST':
        from .models import CartItem
        item, created = CartItem.objects.get_or_create(
            user=request.user, session=session,
            defaults={'yoga_class': yoga_class, 'quantity': 1}
        )
        if created:
            messages.success(request, f'🛒 "{yoga_class.name}" added to cart!')
        else:
            messages.info(request, f'"{yoga_class.name}" is already in your cart.')
        return redirect('cart')
    else:
        # GET — redirect to the class booking page to select session
        return redirect('class_booking_page', slug=yoga_class.slug)




@login_required
def join_waitlist(request, session_pk):
    session = get_object_or_404(ClassSession, pk=session_pk, status='scheduled')
    if not session.is_full:
        messages.info(request, 'There are still spots available. Book directly!')
        return redirect('session_detail', session_pk=session_pk)
    entry, created = Waitlist.objects.get_or_create(user=request.user, session=session, defaults={'status': 'waiting'})
    if created:
        messages.success(request, f'You joined the waitlist (position #{session.waitlist_count}). We will email you if a spot opens.')
    else:
        messages.info(request, 'You are already on the waitlist for this session.')
    return redirect('my_bookings')


@login_required
def leave_waitlist(request, session_pk):
    session = get_object_or_404(ClassSession, pk=session_pk)
    Waitlist.objects.filter(user=request.user, session=session, status='waiting').delete()
    messages.success(request, 'Removed from waitlist.')
    return redirect('my_bookings')


@login_required
def submit_review(request, pk):
    yoga_class = get_object_or_404(YogaClass, pk=pk)
    if request.method == 'POST':
        if Review.objects.filter(user=request.user, yoga_class=yoga_class).exists():
            messages.warning(request, 'You have already reviewed this class.')
            return redirect('class_detail', pk=pk)
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.yoga_class = yoga_class
            review.save()
            messages.success(request, 'Review submitted! Thank you. 🙏')
        else:
            messages.error(request, 'Please fill in all fields correctly.')
    return redirect('class_detail', pk=pk)


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related(
        'yoga_class', 'session', 'used_membership'
    ).order_by('-created_at')
    waitlist = Waitlist.objects.filter(user=request.user, status='waiting').select_related(
        'session', 'session__yoga_class'
    ).order_by('session__date')
    memberships = UserMembership.objects.filter(
        user=request.user, status='active',
        end_date__gte=timezone.now().date()
    ).select_related('plan')
    return render(request, 'my_bookings.html', {
        'bookings': bookings,
        'waitlist': waitlist,
        'memberships': memberships,
    })


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status in ('pending', 'accepted'):
        if not booking.can_cancel:
            messages.error(request, f'Cancellation deadline has passed ({booking.yoga_class.cancellation_hours}h before class).')
            return redirect('my_bookings')
        # Refund membership credit if used
        if booking.used_membership and booking.used_membership.plan.plan_type == 'pack':
            booking.used_membership.classes_remaining += 1
            booking.used_membership.save()
        booking.status = 'cancelled'
        booking.save()
        # Notify waitlist
        if booking.session:
            next_waiting = booking.session.waitlist_entries.filter(status='waiting').first()
            if next_waiting:
                next_waiting.status = 'notified'
                next_waiting.save()
                send_waitlist_notification(next_waiting)
        messages.success(request, 'Booking cancelled successfully.')
    return redirect('my_bookings')


# ─── PAYMENT ─────────────────────────────────────────────────────────────────

@login_required
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.payment_status == 'paid':
        messages.info(request, 'This booking is already paid.')
        return redirect('my_bookings')
    form = PaymentForm()
    return render(request, 'payment.html', {'booking': booking, 'form': form})


@login_required
def process_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if request.method == 'POST':
        # ── TEST MODE: skip card validation, auto-approve ──
        txn_id = f"SY-{uuid.uuid4().hex[:12].upper()}"
        price = booking.session.effective_price if booking.session else booking.yoga_class.price
        payment = Payment.objects.create(
            booking=booking, user=request.user,
            amount=price, transaction_id=txn_id,
            payment_method='card', status='completed',
        )
        booking.payment_status = 'paid'
        booking.save()
        from .utils import send_payment_receipt_to_admin
        send_payment_receipt_email(booking, payment)
        send_payment_receipt_to_admin(
            payment, request.user,
            f"Class: {booking.yoga_class.name}\nSession: {booking.session.date if booking.session else booking.booking_date}"
        )
        messages.success(request, f'✅ Payment successful! Receipt sent to {request.user.email}. Transaction: {txn_id}')
        return redirect('my_bookings')
    return redirect('payment_page', booking_id=booking_id)


@login_required
def buy_membership(request, plan_id):
    plan = get_object_or_404(MembershipPlan, pk=plan_id, is_active=True)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        import re as _re
        card_name   = request.POST.get('card_name', '').strip()
        card_number = request.POST.get('card_number', '').strip().replace(' ', '')
        expiry      = request.POST.get('expiry', '').strip()
        cvv         = request.POST.get('cvv', '').strip()
        card_errors = []
        if not card_name:
            card_errors.append('card_name')
        if not card_number or not card_number.isdigit() or len(card_number) < 13:
            card_errors.append('card_number')
        if not expiry or '/' not in expiry:
            card_errors.append('expiry')
        if not cvv or not cvv.isdigit() or len(cvv) < 3:
            card_errors.append('cvv')

        if card_errors:
            messages.error(request, 'Please enter valid card details.')
            return render(request, 'buy_membership.html', {
                'plan': plan, 'card_errors': card_errors,
                'post_data': request.POST, 'profile': profile,
            })

        txn_id = f"SY-MEM-{uuid.uuid4().hex[:10].upper()}"
        start = timezone.now().date()
        end = start + datetime.timedelta(days=plan.validity_days)
        membership = UserMembership.objects.create(
            user=request.user, plan=plan,
            start_date=start, end_date=end,
            classes_remaining=plan.classes_included,
            status='active'
        )
        payment = Payment.objects.create(
            membership=membership, user=request.user,
            amount=plan.price, transaction_id=txn_id,
            payment_method='card', status='completed',
        )
        # Send receipts to customer AND admin
        from .utils import send_membership_receipt_email, send_payment_receipt_to_admin
        send_membership_receipt_email(membership, payment)
        send_payment_receipt_to_admin(
            payment, request.user,
            f"Pass: {plan.name}\nValid: {start} to {end}"
        )
        # Store for receipt page
        request.session['membership_receipt_id'] = membership.pk
        messages.success(request, f'🎉 {plan.name} activated! Receipt sent to {request.user.email}.')
        return redirect('membership_receipt')

    return render(request, 'buy_membership.html', {
        'plan': plan, 'card_errors': [],
        'post_data': None, 'profile': profile,
    })


# ─── OWNER MANAGEMENT ────────────────────────────────────────────────────────

@login_required
def manage_bookings(request):
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('home')
    # Order oldest first (1 = first booking, 11 = latest)
    bookings = Booking.objects.select_related(
        'user', 'yoga_class', 'session'
    ).order_by('created_at')
    return render(request, 'manage_bookings.html', {'bookings': bookings})


@login_required
def update_booking_status(request, booking_id):
    if not request.user.is_staff:
        return redirect('home')
    booking = get_object_or_404(Booking, id=booking_id)
    action = request.POST.get('action')
    if action == 'accept':
        booking.status = 'accepted'
        booking.save()
        send_booking_accepted_email(booking)
        messages.success(request, f'Booking accepted. {booking.user.email} notified.')
    elif action == 'reject':
        booking.status = 'rejected'
        booking.save()
        send_booking_rejected_email(booking)
        messages.info(request, f'Booking rejected. {booking.user.email} notified.')
    elif action == 'attended':
        booking.status = 'attended'
        booking.save()
    return redirect('manage_bookings')


# ─── AUTH ─────────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect(request.GET.get('next', 'home'))
    next_url = request.GET.get('next', '') or request.POST.get('next', '')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.phone = form.cleaned_data.get('phone', '')
            profile.save()
            messages.success(request, f'Account created! Welcome, {user.first_name or user.username}! Please log in to continue. 🙏')
            from urllib.parse import quote
            login_url = f"/login/?next={quote(next_url, safe='/')}" if next_url else "/login/"
            return redirect(login_url)
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form, 'next': next_url})


def login_view(request):
    if request.user.is_authenticated:
        return redirect(request.GET.get('next', 'home'))
    if request.method == 'POST':
        from django.contrib.auth.forms import AuthenticationForm
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next', '')
            return redirect(next_url if next_url else 'home')
        messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out. Namaste! 🙏')
    return redirect('home')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })
    return render(request, 'profile.html', {'form': form, 'profile': profile})


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Message sent! We will get back to you soon.')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


def about_view(request):
    instructors = Instructor.objects.filter(is_active=True)
    return render(request, 'about.html', {'instructors': instructors})


@login_required
def reply_review(request, review_id):
    """Owner/staff replies to a student review."""
    if not request.user.is_staff:
        messages.error(request, 'Only the studio owner can reply to reviews.')
        return redirect('home')
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        reply_text = request.POST.get('reply', '').strip()
        if reply_text:
            review.owner_reply = reply_text
            review.owner_reply_at = timezone.now()
            review.save()
            messages.success(request, 'Reply posted successfully!')
        else:
            messages.error(request, 'Reply cannot be empty.')
    return redirect('class_detail', pk=review.yoga_class.pk)


@login_required
def delete_reply(request, review_id):
    """Owner deletes their reply to a review."""
    if not request.user.is_staff:
        return redirect('home')
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        review.owner_reply = None
        review.owner_reply_at = None
        review.save()
        messages.success(request, 'Reply deleted.')
    return redirect('class_detail', pk=review.yoga_class.pk)


# ─── CART ─────────────────────────────────────────────────────────────────────

def get_cart_count(user):
    if user.is_authenticated:
        from .models import CartItem
        return CartItem.objects.filter(user=user).count()
    return 0


@login_required
def add_to_cart(request, session_pk):
    from .models import CartItem
    session = get_object_or_404(ClassSession, pk=session_pk, status='scheduled')
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        quantity = max(1, min(quantity, session.spots_remaining or 1))

        # Check already booked
        if Booking.objects.filter(user=request.user, session=session,
                                  status__in=['pending', 'accepted']).exists():
            messages.warning(request, 'You already have a booking for this session.')
            return redirect('class_booking_page', slug=session.yoga_class.slug)

        item, created = CartItem.objects.get_or_create(
            user=request.user, session=session,
            defaults={'yoga_class': session.yoga_class, 'quantity': quantity}
        )
        if not created:
            item.quantity = quantity
            item.save()

        messages.success(request, f'✅ "{session.yoga_class.name}" added to cart!')
        # redirect back to class page or cart
        next_url = request.POST.get('next', 'cart')
        return redirect(next_url)
    return redirect('class_booking_page', slug=session.yoga_class.slug)


@login_required
def cart_view(request):
    from .models import CartItem
    items = CartItem.objects.filter(user=request.user).select_related(
        'yoga_class', 'session', 'yoga_class__instructor'
    ).order_by('added_at')
    total = sum(item.subtotal for item in items)
    return render(request, 'cart.html', {'items': items, 'total': total})


@login_required
def remove_from_cart(request, item_id):
    from .models import CartItem
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    if request.method == 'POST':
        class_name = item.yoga_class.name
        item.delete()
        messages.success(request, f'"{class_name}" removed from cart.')
    return redirect('cart')


@login_required
def checkout_cart(request):
    from .models import CartItem
    items = CartItem.objects.filter(user=request.user).select_related(
        'yoga_class', 'session'
    )
    if not items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    total = sum(item.subtotal for item in items)

    # Check if user has an active membership pass (with classes remaining)
    active_membership = UserMembership.objects.filter(
        user=request.user, status='active',
        end_date__gte=timezone.now().date()
    ).filter(
        Q(plan__plan_type='unlimited') |
        Q(plan__plan_type='pack', classes_remaining__gt=0)
    ).first()

    # Check if user has a pass that is exhausted (0 classes left but still valid)
    exhausted_pass = None
    if not active_membership:
        exhausted_pass = UserMembership.objects.filter(
            user=request.user, status='active',
            end_date__gte=timezone.now().date(),
            plan__plan_type='pack',
            classes_remaining=0
        ).first()

    if request.method == 'POST':
        # If user has active pass — skip card validation entirely
        using_pass = active_membership and request.POST.get('use_pass') == '1'

        if not using_pass:
            # Validate card form
            card_name   = request.POST.get('card_name', '').strip()
            card_number = request.POST.get('card_number', '').strip().replace(' ', '')
            expiry      = request.POST.get('expiry', '').strip()
            cvv         = request.POST.get('cvv', '').strip()

            card_errors = []
            if not card_name:
                card_errors.append('card_name')
            if not card_number or not card_number.isdigit() or len(card_number) < 13:
                card_errors.append('card_number')
            if not expiry or '/' not in expiry:
                card_errors.append('expiry')
            if not cvv or not cvv.isdigit() or len(cvv) < 3:
                card_errors.append('cvv')

            if card_errors:
                messages.error(request, 'Please enter valid card details.')
                return render(request, 'checkout.html', {
                    'items': items, 'total': total,
                    'card_errors': card_errors, 'post_data': request.POST,
                    'active_membership': active_membership,
                    'exhausted_pass': exhausted_pass,
                })

        # ── Pass limit check: if using a pack, ensure enough classes remain ──
        cart_count = items.count()
        if using_pass and active_membership and active_membership.plan.plan_type == 'pack':
            classes_left = active_membership.classes_remaining or 0
            if cart_count > classes_left:
                return render(request, 'checkout.html', {
                    'items': items, 'total': total,
                    'active_membership': active_membership,
                    'exhausted_pass': exhausted_pass,
                    'card_errors': [], 'post_data': None,
                    'pass_exceeded': True,
                    'pass_exceeded_count': cart_count,
                    'pass_remaining': classes_left,
                    'pass_excess': cart_count - classes_left,
                })

        # Process all cart items into bookings
        booked = []
        classes_used_from_pass = 0
        for item in items:
            session = item.session
            if not session or session.is_full:
                messages.error(request, f'"{item.yoga_class.name}" is no longer available.')
                continue

            # For pack passes, only use pass for first N items where N = classes_remaining
            if using_pass and active_membership and active_membership.plan.plan_type == 'pack':
                membership_to_use = active_membership if classes_used_from_pass < (active_membership.classes_remaining or 0) else None
            else:
                membership_to_use = active_membership if (using_pass or active_membership) else None

            try:
                booking = Booking(
                    user=request.user,
                    yoga_class=item.yoga_class,
                    session=session,
                    booking_date=session.date,
                    notes='',
                    status='accepted',
                    payment_status='free' if membership_to_use else 'unpaid',
                    used_membership=membership_to_use if membership_to_use else None,
                )
                booking.save()
                booked.append(booking)

                if membership_to_use and membership_to_use.plan.plan_type == 'pack' \
                        and membership_to_use.classes_remaining:
                    membership_to_use.classes_remaining -= 1
                    membership_to_use.save()
                    classes_used_from_pass += 1

                send_booking_notification_to_owner(booking)
                send_booking_accepted_email(booking)
            except Exception:
                messages.warning(request, f'"{item.yoga_class.name}" could not be booked (already exists).')

        # Pay for unpaid bookings immediately on checkout
        unpaid = [b for b in booked if b.payment_status == 'unpaid']
        if unpaid:
            txn_id = f"SY-CART-{uuid.uuid4().hex[:10].upper()}"
            for b in unpaid:
                price = b.session.effective_price if b.session else b.yoga_class.price
                p = Payment.objects.create(
                    booking=b, user=request.user,
                    amount=price, transaction_id=f"{txn_id}-{b.pk}",
                    payment_method='card', status='completed',
                )
                b.payment_status = 'paid'
                b.save()
                send_payment_receipt_email(b, p)
                from .utils import send_payment_receipt_to_admin
                send_payment_receipt_to_admin(
                    p, request.user,
                    f"Class: {b.yoga_class.name}\nSession: {b.session.date if b.session else b.booking_date}"
                )

        # Clear cart
        items.delete()

        # Store booking IDs in session for receipt page
        request.session['receipt_booking_ids'] = [b.pk for b in booked]
        return redirect('booking_receipt')

    return render(request, 'checkout.html', {
        'items': items, 'total': total,
        'active_membership': active_membership,
        'exhausted_pass': exhausted_pass,
        'card_errors': [], 'post_data': None,
    })


def class_booking_page(request, slug):
    """Product-style booking page at /bookings/<slug>/"""
    yoga_class = get_object_or_404(YogaClass, slug=slug, is_active=True)
    today = timezone.now().date()
    sessions = ClassSession.objects.filter(
        yoga_class=yoga_class, date__gte=today,
        date__lte=today + datetime.timedelta(days=60),
        status__in=['scheduled', 'unavailable']
    ).order_by('date', 'start_time')

    reviews = yoga_class.reviews.select_related('user').order_by('-created_at')
    related = YogaClass.objects.filter(
        is_active=True, category=yoga_class.category
    ).exclude(pk=yoga_class.pk)[:3]

    cart_session_ids = set()
    user_review = None
    review_form = None
    active_membership = None
    if request.user.is_authenticated:
        from .models import CartItem
        cart_session_ids = set(
            CartItem.objects.filter(user=request.user).values_list('session_id', flat=True)
        )
        user_review = Review.objects.filter(user=request.user, yoga_class=yoga_class).first()
        if not user_review:
            review_form = ReviewForm()
        active_membership = UserMembership.objects.filter(
            user=request.user, status='active',
            end_date__gte=today
        ).filter(
            Q(plan__plan_type='unlimited') |
            Q(plan__plan_type='pack', classes_remaining__gt=0)
        ).first()

    return render(request, 'class_booking_page.html', {
        'yoga_class': yoga_class,
        'sessions': sessions,
        'reviews': reviews,
        'related': related,
        'cart_session_ids': cart_session_ids,
        'user_review': user_review,
        'review_form': review_form,
        'active_membership': active_membership,
    })


# ─── SEARCH ───────────────────────────────────────────────────────────────────

import json
from django.http import JsonResponse
from django.db.models import Q


def search_autocomplete(request):
    """Live autocomplete — returns JSON suggestions as user types."""
    q = request.GET.get('q', '').strip()
    results = []
    if len(q) >= 2:
        classes = YogaClass.objects.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(category__icontains=q) |
            Q(level__icontains=q)
        ).filter(is_active=True)[:6]

        # Also match instructors
        instructors = Instructor.objects.filter(
            Q(name__icontains=q) | Q(specialties__icontains=q),
            is_active=True
        )[:3]

        for cls in classes:
            next_sess = cls.sessions.filter(
                date__gte=timezone.now().date(),
                status__in=['scheduled', 'unavailable']
            ).order_by('date').first()
            results.append({
                'type': 'class',
                'name': cls.name,
                'subtitle': f"{cls.get_level_display()} · {cls.get_category_display()} · A${cls.price}",
                'url': f'/bookings/{cls.slug}/',
                'photo': cls.photo_url or '',
                'available': True,
                'next_session': next_sess.date.strftime('%a, %b %d') if next_sess else None,
                'next_status': next_sess.status if next_sess else None,
            })

        for inst in instructors:
            results.append({
                'type': 'instructor',
                'name': inst.name,
                'subtitle': inst.specialties or 'Instructor',
                'url': f'/instructors/{inst.pk}/',
                'photo': inst.photo_url or '',
                'available': True,
                'next_session': None,
                'next_status': None,
            })

    return JsonResponse({'results': results, 'query': q})


def search_results(request):
    """Full search results page."""
    q = request.GET.get('q', '').strip()
    classes = []
    instructors = []

    if q:
        classes = YogaClass.objects.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(category__icontains=q) |
            Q(level__icontains=q) |
            Q(instructor__name__icontains=q),
            is_active=True
        ).distinct().prefetch_related('sessions')

        instructors = Instructor.objects.filter(
            Q(name__icontains=q) | Q(specialties__icontains=q) | Q(bio__icontains=q),
            is_active=True
        )

    return render(request, 'search_results.html', {
        'query': q,
        'classes': classes,
        'instructors': instructors,
        'total': classes.count() + instructors.count() if q else 0,
    })


# ─── INTAKE FORM BEFORE ADD-TO-CART ──────────────────────────────────────────

@login_required
def intake_form_view(request, session_pk):
    """Show the booking intake form before adding to cart."""
    from .models import BookingForm as IntakeForm, CartItem
    session = get_object_or_404(ClassSession, pk=session_pk, status='scheduled')
    yoga_class = session.yoga_class

    if session.is_past:
        messages.error(request, 'This session has already passed.')
        return redirect('class_booking_page', slug=yoga_class.slug)
    if session.is_full:
        messages.warning(request, 'Session is full. Join the waitlist.')
        return redirect('session_detail', session_pk=session_pk)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    levels = [('beginner','Beginner'),('experienced','Experienced'),('advanced','Advanced')]
    states = ['ACT','NSW','NT','QLD','SA','TAS','VIC','WA']

    # Try to load previously saved intake form for this user (any session)
    prev_intake = IntakeForm.objects.filter(user=request.user).order_by('-created_at').first()

    # Build pre-filled data from profile + previous intake
    prefill = {
        'first_name': request.user.first_name or (prev_intake.first_name if prev_intake else ''),
        'last_name':  request.user.last_name  or (prev_intake.last_name  if prev_intake else ''),
        'email':      request.user.email      or (prev_intake.email      if prev_intake else ''),
        'phone':      profile.phone           or (prev_intake.phone      if prev_intake else ''),
        'address_line1': (prev_intake.address_line1 if prev_intake else ''),
        'address_line2': (prev_intake.address_line2 if prev_intake else ''),
        'suburb':     (prev_intake.suburb     if prev_intake else ''),
        'state':      (prev_intake.state      if prev_intake else ''),
        'postcode':   (prev_intake.postcode   if prev_intake else ''),
        'country':    (prev_intake.country    if prev_intake else 'Australia'),
        'how_found':  (prev_intake.how_found  if prev_intake else ''),
        'experience_level': (prev_intake.experience_level if prev_intake else 'beginner'),
        'notes':      profile.bio             or (prev_intake.notes if prev_intake else ''),
    }

    # Check if all required fields are already filled — if so, mark as pre-filled
    required_fields = ['first_name','last_name','email','phone','address_line1','suburb','state','postcode']
    all_prefilled = all(prefill.get(f,'').strip() for f in required_fields)
    # Auto-check waiver if user has ANY previous booking (they've agreed before)
    waiver_auto_checked = all_prefilled or (prev_intake is not None and prev_intake.medical_waiver_agreed)

    if request.method == 'POST':
        import re as _re
        required = ['first_name', 'last_name', 'email', 'phone',
                    'address_line1', 'suburb', 'state', 'postcode', 'experience_level']
        errors = []
        validation_messages = {}
        phone_val    = request.POST.get('phone', '').strip()
        email_val    = request.POST.get('email', '').strip()
        postcode_val = request.POST.get('postcode', '').strip()
        name_val     = request.POST.get('first_name', '').strip()
        lastname_val = request.POST.get('last_name', '').strip()

        for field in required:
            if not request.POST.get(field, '').strip():
                errors.append(field)
                validation_messages[field] = 'Required.'

        if name_val and not _re.match(r'^[A-Za-z\s\-]+$', name_val):
            errors.append('first_name')
            validation_messages['first_name'] = 'Letters only.'
        if lastname_val and not _re.match(r'^[A-Za-z\s\-]+$', lastname_val):
            errors.append('last_name')
            validation_messages['last_name'] = 'Letters only.'
        if email_val and not _re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email_val):
            errors.append('email')
            validation_messages['email'] = 'Enter a valid email address.'
        if phone_val and not _re.match(r'^[0-9+\-\s().]+$', phone_val):
            errors.append('phone')
            errors.append('phone_invalid')
            validation_messages['phone'] = 'Digits only — no letters.'
        if postcode_val and not postcode_val.isdigit():
            errors.append('postcode')
            validation_messages['postcode'] = 'Digits only.'
        if not request.POST.get('medical_waiver_agreed'):
            errors.append('medical_waiver_agreed')
            validation_messages['medical_waiver_agreed'] = 'You must agree to the waiver.'

        errors = list(dict.fromkeys(errors))

        if errors:
            # Build friendly grouped error message instead of listing each field
            field_labels = {
                'first_name': 'First Name', 'last_name': 'Last Name',
                'email': 'Email', 'phone': 'Phone',
                'address_line1': 'Address', 'suburb': 'Suburb',
                'state': 'State', 'postcode': 'Postcode',
                'experience_level': 'Experience Level',
            }
            missing = [field_labels.get(f, f.replace('_',' ').title()) for f in errors
                      if f not in ('phone_invalid','medical_waiver_agreed') and validation_messages.get(f) == 'Required.']
            invalid = {k:v for k,v in validation_messages.items()
                      if v != 'Required.' and k != 'medical_waiver_agreed'}

            return render(request, 'intake_form.html', {
                'session': session, 'yoga_class': yoga_class,
                'post_data': request.POST, 'errors': errors,
                'validation_messages': validation_messages,
                'missing_fields': missing,
                'invalid_fields': invalid,
                'levels': levels, 'states': states,
                'user': request.user, 'profile': profile,
                'phone_default': request.POST.get('phone', profile.phone or ''),
                'prefill': prefill,
                'all_prefilled': False,
                'waiver_auto_checked': waiver_auto_checked,
            })

        # Add to cart
        item, created = CartItem.objects.get_or_create(
            user=request.user, session=session,
            defaults={'yoga_class': yoga_class, 'quantity': 1}
        )

        # Save intake form
        IntakeForm.objects.update_or_create(
            user=request.user, session=session,
            defaults={
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'email': request.POST.get('email'),
                'phone': request.POST.get('phone'),
                'country': request.POST.get('country', 'Australia'),
                'address_line1': request.POST.get('address_line1'),
                'address_line2': request.POST.get('address_line2', ''),
                'suburb': request.POST.get('suburb'),
                'state': request.POST.get('state'),
                'postcode': request.POST.get('postcode'),
                'how_found': request.POST.get('how_found', ''),
                'experience_level': request.POST.get('experience_level'),
                'medical_waiver_agreed': bool(request.POST.get('medical_waiver_agreed')),
                'notes': request.POST.get('notes', ''),
            }
        )

        # ── Sync to User + UserProfile so profile page shows the data ──
        u = request.user
        u.first_name = request.POST.get('first_name', u.first_name)
        u.last_name  = request.POST.get('last_name',  u.last_name)
        u.email      = request.POST.get('email',      u.email)
        u.save()

        profile.phone              = request.POST.get('phone', profile.phone or '')
        profile.bio                = request.POST.get('notes', profile.bio or '')
        # Build emergency contact from address info for reference
        addr = ', '.join(filter(None, [
            request.POST.get('address_line1', ''),
            request.POST.get('suburb', ''),
            request.POST.get('state', ''),
            request.POST.get('postcode', ''),
        ]))
        if addr and not profile.emergency_contact:
            profile.emergency_contact = addr
        profile.save()

        if created:
            messages.success(request, f'🛒 "{yoga_class.name}" added to cart!')
        else:
            messages.info(request, f'Cart updated for "{yoga_class.name}".')
        return redirect('cart')

    levels = [('beginner','Beginner'),('experienced','Experienced'),('advanced','Advanced')]
    states = ['ACT','NSW','NT','QLD','SA','TAS','VIC','WA']
    return render(request, 'intake_form.html', {
        'session': session,
        'yoga_class': yoga_class,
        'post_data': None,
        'errors': [],
        'validation_messages': {},
        'missing_fields': [],
        'invalid_fields': {},
        'user': request.user,
        'profile': profile,
        'phone_default': prefill['phone'],
        'prefill': prefill,
        'all_prefilled': all_prefilled,
        'waiver_auto_checked': waiver_auto_checked,
        'levels': levels,
        'states': states,
    })


@login_required
def booking_receipt(request):
    """Show receipt after successful checkout."""
    booking_ids = request.session.pop('receipt_booking_ids', [])
    bookings = Booking.objects.filter(
        pk__in=booking_ids, user=request.user
    ).select_related('yoga_class', 'session', 'yoga_class__instructor')
    if not bookings:
        return redirect('my_bookings')
    payments = {p.booking_id: p for p in Payment.objects.filter(booking__in=bookings)}
    booking_payment_pairs = [(b, payments.get(b.pk)) for b in bookings]
    return render(request, 'booking_receipt.html', {
        'bookings': bookings,
        'payments': payments,
        'booking_payment_pairs': booking_payment_pairs,
    })


@login_required
def customer_profile(request):
    """Rich customer profile showing bookings, passes, history."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    bookings = Booking.objects.filter(
        user=request.user
    ).select_related('yoga_class', 'session').order_by('-created_at')
    memberships = UserMembership.objects.filter(
        user=request.user
    ).select_related('plan').order_by('-created_at')
    payments = Payment.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]
    total_spent = sum(p.amount for p in Payment.objects.filter(user=request.user))
    classes_attended = bookings.filter(status='attended').count()
    classes_booked = bookings.filter(status__in=['accepted', 'attended', 'pending']).count()

    if request.method == 'POST':
        from .forms import UserProfileForm
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('customer_profile')
    else:
        from .forms import UserProfileForm
        form = UserProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })

    return render(request, 'customer_profile.html', {
        'profile': profile,
        'form': form,
        'bookings': bookings[:5],
        'memberships': memberships,
        'payments': payments,
        'total_spent': total_spent,
        'classes_attended': classes_attended,
        'classes_booked': classes_booked,
    })


@login_required
def membership_receipt(request):
    membership_id = request.session.pop('membership_receipt_id', None)
    if not membership_id:
        return redirect('my_bookings')
    membership = get_object_or_404(UserMembership, pk=membership_id, user=request.user)
    payment = Payment.objects.filter(membership=membership).first()
    return render(request, 'membership_receipt.html', {
        'membership': membership,
        'payment': payment,
    })


@login_required
def manage_payments(request):
    """Owner view — all payments with receipts."""
    if not request.user.is_staff:
        return redirect('home')
    from django.db.models import Sum, Count
    payments = Payment.objects.select_related(
        'user', 'booking__yoga_class', 'booking__session',
        'membership__plan'
    ).order_by('-created_at')

    total_count = payments.count()
    total = payments.aggregate(t=Sum('amount'))['t'] or 0
    month_start = timezone.now().date().replace(day=1)
    month_total = payments.filter(
        created_at__date__gte=month_start
    ).aggregate(t=Sum('amount'))['t'] or 0

    return render(request, 'manage_payments.html', {
        'payments': payments,
        'total_count': total_count,
        'total': total,
        'month_total': month_total,
    })


@login_required
def owner_dashboard(request):
    """Owner overview dashboard."""
    if not request.user.is_staff:
        return redirect('home')
    from django.db.models import Sum, Count
    from django.contrib.auth.models import User as _User

    today = timezone.now().date()
    month_start = today.replace(day=1)

    # Revenue
    total_revenue = Payment.objects.aggregate(t=Sum('amount'))['t'] or 0
    month_revenue = Payment.objects.filter(
        created_at__date__gte=month_start
    ).aggregate(t=Sum('amount'))['t'] or 0

    # Bookings
    total_bookings   = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    todays_bookings  = Booking.objects.filter(booking_date=today).count()

    # Students
    total_students = _User.objects.filter(is_staff=False).count()

    # Unread contact messages
    unread_msgs = ContactMessage.objects.filter(is_read=False).count()

    # Today's sessions
    todays_sessions = ClassSession.objects.filter(
        date=today, status='scheduled'
    ).select_related('yoga_class').annotate(
        booked=Count('bookings')
    ).order_by('start_time')

    # Upcoming 7 days
    upcoming = ClassSession.objects.filter(
        date__range=[today + datetime.timedelta(days=1),
                     today + datetime.timedelta(days=7)],
        status='scheduled'
    ).select_related('yoga_class').annotate(
        booked=Count('bookings')
    ).order_by('date', 'start_time')[:8]

    # Recent bookings
    recent_bookings = Booking.objects.select_related(
        'user', 'yoga_class', 'session'
    ).order_by('-created_at')[:8]

    # Recent payments
    recent_payments = Payment.objects.select_related(
        'user', 'booking__yoga_class', 'membership__plan'
    ).order_by('-created_at')[:10]

    # Recent messages
    recent_messages = ContactMessage.objects.order_by('-created_at')[:5]

    return render(request, 'owner_dashboard.html', {
        'total_revenue': total_revenue,
        'month_revenue': month_revenue,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'todays_bookings': todays_bookings,
        'total_students': total_students,
        'unread_msgs': unread_msgs,
        'todays_sessions': todays_sessions,
        'upcoming': upcoming,
        'recent_bookings': recent_bookings,
        'recent_payments': recent_payments,
        'recent_messages': recent_messages,
        'today': today,
    })
