from django import template

register = template.Library()

@register.filter
def lte(value, arg):
    """Returns True if value <= arg."""
    try:
        return int(value) <= int(arg)
    except (ValueError, TypeError):
        return False

@register.filter
def range_up_to(value):
    """Return range(1, value+1) for star rendering."""
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return range(0)


@register.inclusion_tag('partials/avail_badge.html')
def avail_badge(session, user=None):
    """Render an availability badge for a session."""
    from siriusyogaclass.core.models import Booking, Waitlist
    is_booked = False
    is_waitlisted = False

    if user and user.is_authenticated:
        is_booked = Booking.objects.filter(
            user=user, session=session, status__in=['pending', 'accepted']
        ).exists()
        if not is_booked:
            is_waitlisted = Waitlist.objects.filter(
                user=user, session=session, status='waiting'
            ).exists()

    if session.is_past:
        status = 'past'
    elif is_booked:
        status = 'booked'
    elif is_waitlisted:
        status = 'waitlist'
    elif session.is_full:
        status = 'full'
    elif session.is_low_spots:
        status = 'low'
    else:
        status = 'open'

    return {
        'status': status,
        'spots': session.spots_remaining,
        'max': session.effective_max,
        'waitlist_count': session.waitlist_count,
    }


@register.simple_tag
def class_photo(yoga_class, css_class="", style=""):
    """Return img tag using uploaded image or photo_url fallback."""
    from django.utils.html import format_html, escape
    if yoga_class.image:
        src = yoga_class.image.url
    elif yoga_class.photo_url:
        src = yoga_class.photo_url
    else:
        return format_html('<span style="font-size:4rem;display:flex;align-items:center;justify-content:center;height:100%;">🧘</span>')
    return format_html(
        '<img src="{}" alt="{}" class="{}" style="width:100%;height:100%;object-fit:cover;{}" loading="lazy">',
        src, escape(yoga_class.name), css_class, style
    )


@register.simple_tag
def instructor_photo(instructor, size="56px"):
    """Return instructor photo img or emoji fallback."""
    from django.utils.html import format_html
    style = f"width:{size};height:{size};border-radius:50%;object-fit:cover;"
    if instructor.photo:
        return format_html('<img src="{}" alt="{}" style="{}">', instructor.photo.url, instructor.name, style)
    elif instructor.photo_url:
        return format_html('<img src="{}" alt="{}" style="{}" loading="lazy">', instructor.photo_url, instructor.name, style)
    return format_html('<span style="font-size:1.5rem;display:flex;align-items:center;justify-content:center;width:{};height:{};border-radius:50%;background:var(--sage);color:white;">🧘</span>', size, size)


@register.filter
def split(value, delimiter=','):
    return value.split(delimiter)


@register.filter
def dict_get(d, key):
    """Get a value from a dict by key — handles int/string mismatch."""
    try:
        result = d.get(key)
        if result is None:
            # Try int conversion
            try:
                result = d.get(int(key))
            except (ValueError, TypeError):
                pass
        return result
    except (AttributeError, TypeError):
        return None
