from django.contrib import admin
from .models import (YogaClass, ClassSession, Schedule, Booking, Payment,
                     Review, UserProfile, ContactMessage, Waitlist,
                     MembershipPlan, UserMembership, Instructor)


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('name', 'years_experience', 'is_active')
    list_editable = ('is_active',)


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1


class SessionInline(admin.TabularInline):
    model = ClassSession
    extra = 3
    fields = ('date', 'start_time', 'end_time', 'status', 'override_price', 'override_max')


@admin.register(YogaClass)
class YogaClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'instructor', 'category', 'level', 'price', 'is_active', 'avg_rating')
    list_filter = ('level', 'category', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_active', 'price')
    inlines = [ScheduleInline, SessionInline]


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ('yoga_class', 'date', 'start_time', 'status_display', 'confirmed_count', 'spots_remaining', 'effective_price')
    list_filter = ('status', 'date', 'yoga_class')
    date_hierarchy = 'date'
    readonly_fields = ('confirmed_count', 'spots_remaining', 'waitlist_count')
    actions = ['mark_unavailable', 'mark_scheduled']

    def status_display(self, obj):
        from django.utils.html import format_html
        colours = {
            'scheduled': '#2e7d32',
            'unavailable': '#c62828',
            'cancelled': '#9e9e9e',
            'completed': '#1565c0',
        }
        colour = colours.get(obj.status, '#000')
        return format_html(
            '<span style="color:{};font-weight:600;">● {}</span>',
            colour, obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def mark_unavailable(self, request, queryset):
        queryset.update(status='unavailable')
        self.message_user(request, f'{queryset.count()} session(s) marked as Unavailable.')
    mark_unavailable.short_description = '🔴 Mark selected as Unavailable'

    def mark_scheduled(self, request, queryset):
        queryset.update(status='scheduled')
        self.message_user(request, f'{queryset.count()} session(s) marked as Scheduled.')
    mark_scheduled.short_description = '🟢 Mark selected as Available'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'yoga_class', 'session', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status')
    list_editable = ('status',)
    search_fields = ('user__username', 'yoga_class__name')
    actions = ['accept_bookings', 'reject_bookings']

    def accept_bookings(self, request, queryset):
        from siriusyogaclass.core.utils import send_booking_accepted_email
        for b in queryset.filter(status='pending'):
            b.status = 'accepted'
            b.save()
            send_booking_accepted_email(b)
        self.message_user(request, "Bookings accepted and students notified by email.")
    accept_bookings.short_description = "✅ Accept & notify student"

    def reject_bookings(self, request, queryset):
        from siriusyogaclass.core.utils import send_booking_rejected_email
        for b in queryset.filter(status='pending'):
            b.status = 'rejected'
            b.save()
            send_booking_rejected_email(b)
        self.message_user(request, "Bookings rejected and students notified by email.")
    reject_bookings.short_description = "❌ Reject & notify student"


@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'session', 'status', 'joined_at')
    list_filter = ('status',)


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'price', 'classes_included', 'validity_days', 'is_active', 'highlight')
    list_editable = ('is_active', 'highlight', 'price')


@admin.register(UserMembership)
class UserMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'classes_remaining', 'status')
    list_filter = ('status', 'plan')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_id', 'status', 'created_at')
    readonly_fields = ('transaction_id',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'yoga_class', 'rating', 'has_reply', 'created_at')

    def has_reply(self, obj):
        return bool(obj.owner_reply)
    has_reply.boolean = True
    has_reply.short_description = 'Replied'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_editable = ('is_read',)


admin.site.site_header = "🌟 Sirius Yoga Admin"
admin.site.site_title = "Sirius Yoga"
admin.site.index_title = "Dashboard"
