from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import datetime


class Instructor(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='instructors/', blank=True, null=True)
    photo_url = models.URLField(blank=True, help_text='External photo URL')
    specialties = models.CharField(max_length=300, blank=True, help_text="Comma-separated list")
    years_experience = models.IntegerField(default=1)
    certifications = models.TextField(blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, help_text='Instructor contact email')
    phone = models.CharField(max_length=30, blank=True, help_text='Instructor contact phone')
    website = models.URLField(blank=True, help_text='Instructor personal website')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class YogaClass(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('all', 'All Levels'),
    ]
    CATEGORY_CHOICES = [
        ('yoga', 'Yoga'),
        ('pilates', 'Pilates'),
        ('reformer', 'Reformer Pilates'),
        ('meditation', 'Meditation'),
        ('breathwork', 'Breathwork'),
        ('hiit', 'HIIT Yoga'),
        ('yin', 'Yin'),
        ('prenatal', 'Prenatal'),
    ]
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    instructor = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, related_name='classes')
    duration_minutes = models.IntegerField(default=60)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='all')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='yoga')
    image = models.ImageField(upload_to='classes/', blank=True, null=True)
    photo_url = models.URLField(blank=True, help_text='External photo URL (e.g. Unsplash)')
    max_participants = models.IntegerField(default=15)
    is_active = models.BooleanField(default=True)
    what_to_bring = models.TextField(blank=True, default="Comfortable yoga attire, water bottle. Mats available to borrow.")
    cancellation_hours = models.IntegerField(default=12, help_text="Hours before class to allow cancellation")
    prerequisite_note = models.CharField(max_length=300, blank=True, help_text="e.g. Must have completed Intro to Reformer")
    is_online = models.BooleanField(default=False)
    online_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while YogaClass.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def avg_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum(r.rating for r in reviews) / len(reviews), 1)
        return 0

    def total_reviews(self):
        return self.reviews.count()

    class Meta:
        verbose_name_plural = 'Yoga Classes'


class ClassSession(models.Model):
    """A specific scheduled instance of a YogaClass on a specific date/time."""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('unavailable', 'Unavailable'),   # admin marks as not available
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    yoga_class = models.ForeignKey(YogaClass, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    override_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                         help_text="Leave blank to use class default price")
    override_max = models.IntegerField(null=True, blank=True,
                                       help_text="Leave blank to use class default max participants")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.CharField(max_length=300, blank=True, help_text="e.g. 'Bring a towel', 'Outdoor session'")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.yoga_class.name} — {self.date} {self.start_time}"

    @property
    def effective_price(self):
        return self.override_price if self.override_price is not None else self.yoga_class.price

    @property
    def effective_max(self):
        return self.override_max if self.override_max is not None else self.yoga_class.max_participants

    @property
    def confirmed_count(self):
        return self.bookings.filter(status__in=['accepted', 'pending']).count()

    @property
    def spots_remaining(self):
        return max(0, self.effective_max - self.confirmed_count)

    @property
    def is_full(self):
        return self.spots_remaining == 0

    @property
    def is_low_spots(self):
        """True when 1–3 spots remain (but not full)."""
        r = self.spots_remaining
        return 0 < r <= 3

    @property
    def is_unavailable(self):
        return self.status == 'unavailable'

    @property
    def waitlist_count(self):
        return self.waitlist_entries.filter(status='waiting').count()

    @property
    def is_past(self):
        session_dt = datetime.datetime.combine(self.date, self.start_time)
        return timezone.now() > timezone.make_aware(session_dt)

    @property
    def cancellation_deadline(self):
        session_dt = datetime.datetime.combine(self.date, self.start_time)
        return timezone.make_aware(session_dt) - datetime.timedelta(hours=self.yoga_class.cancellation_hours)

    @property
    def can_cancel(self):
        return timezone.now() < self.cancellation_deadline


class Schedule(models.Model):
    """Recurring weekly schedule — generates ClassSessions."""
    DAY_CHOICES = [
        ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday'),
    ]
    yoga_class = models.ForeignKey(YogaClass, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.yoga_class.name} — {self.day_of_week} {self.start_time}"


class MembershipPlan(models.Model):
    PLAN_TYPE_CHOICES = [
        ('unlimited', 'Unlimited Monthly'),
        ('pack', 'Class Pack'),
        ('drop_in', 'Drop-In'),
    ]
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    classes_included = models.IntegerField(null=True, blank=True, help_text="For packs. Null = unlimited")
    validity_days = models.IntegerField(default=30, help_text="How many days this plan is valid")
    is_active = models.BooleanField(default=True)
    highlight = models.BooleanField(default=False, help_text="Mark as featured/popular")

    def __str__(self):
        return self.name


class UserMembership(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('expired', 'Expired'), ('cancelled', 'Cancelled')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    classes_remaining = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.plan.name}"

    @property
    def is_valid(self):
        return self.status == 'active' and self.end_date >= timezone.now().date()


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    yoga_class = models.ForeignKey(YogaClass, on_delete=models.CASCADE, related_name='bookings')
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    booking_date = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    used_membership = models.ForeignKey(UserMembership, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[('unpaid', 'Unpaid'), ('paid', 'Paid'), ('free', 'Free via Membership')],
        default='unpaid'
    )
    reminder_sent = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'session')

    def __str__(self):
        return f"{self.user.username} — {self.yoga_class.name} ({self.booking_date})"

    @property
    def can_cancel(self):
        if self.session:
            return self.session.can_cancel
        return True


class Waitlist(models.Model):
    STATUS_CHOICES = [('waiting', 'Waiting'), ('notified', 'Notified'), ('booked', 'Booked'), ('expired', 'Expired')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='waitlist_entries')
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name='waitlist_entries')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'session')
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} — waitlist for {self.session}"


class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment', null=True, blank=True)
    membership = models.OneToOneField(UserMembership, on_delete=models.CASCADE, related_name='payment', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=50, default='card')
    status = models.CharField(max_length=20, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.transaction_id} — {self.user.username}"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    yoga_class = models.ForeignKey(YogaClass, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    owner_reply = models.TextField(blank=True, null=True)
    owner_reply_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'yoga_class')

    def __str__(self):
        return f"{self.user.username} — {self.yoga_class.name} ({self.rating}★)"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    health_notes = models.TextField(blank=True, help_text="Any health conditions the instructor should know about")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} — {self.subject}"


class CartItem(models.Model):
    """Session-based cart — one item per user per session."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    yoga_class = models.ForeignKey(YogaClass, on_delete=models.CASCADE)
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'session')

    def __str__(self):
        return f"{self.user.username} cart — {self.yoga_class.name}"

    @property
    def subtotal(self):
        price = self.session.effective_price if self.session else self.yoga_class.price
        return price * self.quantity


class BookingForm(models.Model):
    """Pre-booking intake form filled before adding to cart."""
    booking = models.OneToOneField('Booking', on_delete=models.CASCADE,
                                   related_name='intake_form', null=True, blank=True)
    session = models.ForeignKey('ClassSession', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    # Personal
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    # Address
    country = models.CharField(max_length=60, default='Australia')
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    suburb = models.CharField(max_length=100)
    state = models.CharField(max_length=60)
    postcode = models.CharField(max_length=10)
    # How found
    HOW_CHOICES = [
        ('google', 'Google / Search Engine'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('friend', 'Friend / Word of Mouth'),
        ('returning', 'Returning Student'),
        ('other', 'Other'),
    ]
    how_found = models.CharField(max_length=20, choices=HOW_CHOICES, blank=True)
    # Experience
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('experienced', 'Experienced'),
        ('advanced', 'Advanced'),
    ]
    experience_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    # Medical waiver
    medical_waiver_agreed = models.BooleanField(default=False)
    # Notes
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} — intake form"
