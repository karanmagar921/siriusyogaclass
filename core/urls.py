from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('classes/', views.classes_list, name='classes'),
    path('classes/<int:pk>/', views.class_detail, name='class_detail'),
    path('classes/<int:pk>/review/', views.submit_review, name='submit_review'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('instructors/', views.instructors_view, name='instructors'),
    path('instructors/<int:pk>/', views.instructor_detail, name='instructor_detail'),
    path('pricing/', views.pricing_view, name='pricing'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),

    # Sessions
    path('session/<int:session_pk>/', views.session_detail, name='session_detail'),
    path('session/<int:session_pk>/book/', views.book_session, name='book_session'),
    path('session/<int:session_pk>/waitlist/', views.join_waitlist, name='join_waitlist'),
    path('session/<int:session_pk>/leave-waitlist/', views.leave_waitlist, name='leave_waitlist'),

    # Bookings
    path('bookings/', views.my_bookings, name='my_bookings'),
    path('bookings/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('bookings/<int:booking_id>/payment/', views.payment_page, name='payment_page'),
    path('bookings/<int:booking_id>/process-payment/', views.process_payment, name='process_payment'),

    # Memberships
    path('pricing/<int:plan_id>/buy/', views.buy_membership, name='buy_membership'),

    # Owner management
    path('manage/', views.owner_dashboard, name='owner_dashboard'),
    path('manage/payments/', views.manage_payments, name='manage_payments'),
    path('manage/bookings/', views.manage_bookings, name='manage_bookings'),
    path('manage/bookings/<int:booking_id>/update/', views.update_booking_status, name='update_booking_status'),

    # Search
    path('search/', views.search_results, name='search_results'),
    path('search/autocomplete/', views.search_autocomplete, name='search_autocomplete'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/checkout/', views.checkout_cart, name='checkout_cart'),
    path('session/<int:session_pk>/add-to-cart/', views.add_to_cart, name='add_to_cart'),

    # Slug-based booking page (like hillsyoga)
    path('bookings/<slug:slug>/', views.class_booking_page, name='class_booking_page'),

    # Receipt & Profile
    path('membership/receipt/', views.membership_receipt, name='membership_receipt'),
    path('booking/receipt/', views.booking_receipt, name='booking_receipt'),
    path('my-profile/', views.customer_profile, name='customer_profile'),

    # Intake form
    path('session/<int:session_pk>/intake/', views.intake_form_view, name='intake_form'),

    # Reviews
    path('review/<int:review_id>/reply/', views.reply_review, name='reply_review'),
    path('review/<int:review_id>/delete-reply/', views.delete_reply, name='delete_reply'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]
