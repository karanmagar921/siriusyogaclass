from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from siriusyogaclass.core.models import YogaClass, Schedule, ClassSession, Instructor, MembershipPlan
import datetime


class Command(BaseCommand):
    help = 'Seed database with sample data'

    def handle(self, *args, **kwargs):
        # Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'thapakarann89@gmail.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Superuser created: admin / admin123'))

        # Instructors — with real Unsplash photo URLs
        instructors_data = [
            {
                'name': 'Sarah Chen',
                'bio': 'Sarah has been practicing yoga for over 15 years and teaching for 10. Trained in Bali and India, she brings a deep understanding of vinyasa flow and mindfulness to every class. Her sessions are dynamic, soulful, and accessible to all levels.',
                'specialties': 'Vinyasa Flow, Power Yoga, Pranayama',
                'years_experience': 10,
                'certifications': 'RYT-500, Yin Yoga Certified, Pranayama Teacher Training',
                'photo_url': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400&q=80',
                'email': 'sarah@siriusyoga.com.au',
                'phone': '+61 400 111 222',
                'instagram': '@sarahchenyoga',
            },
            {
                'name': 'Maya Patel',
                'bio': 'Maya discovered yoga as a teenager and never looked back. Her gentle, alignment-focused approach has helped hundreds of beginners build confidence on the mat. She is also a certified meditation teacher.',
                'specialties': 'Hatha Yoga, Yin, Meditation',
                'years_experience': 8,
                'certifications': 'RYT-200, Meditation Teacher Training, Yin Yoga Certification',
                'photo_url': 'https://images.unsplash.com/photo-1593811167562-9cef47bfc4d7?w=400&q=80',
                'email': 'maya@siriusyoga.com.au',
                'phone': '+61 400 222 333',
                'instagram': '@mayapatelyoga',
            },
            {
                'name': 'James Torres',
                'bio': "A former athlete, James brings a fitness-forward approach to yoga. His Power Yoga classes are intense, challenging, and results-driven. He believes yoga is for every body — especially those who think they can't do it.",
                'specialties': 'Power Yoga, Ashtanga, HIIT Yoga',
                'years_experience': 7,
                'certifications': 'RYT-500, Ashtanga Authorized Level 2',
                'photo_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&q=80',
                'email': 'james@siriusyoga.com.au',
                'phone': '+61 400 333 444',
                'instagram': '@jamestorresfit',
            },
            {
                'name': 'Luna Williams',
                'bio': 'Luna is a deeply intuitive teacher whose classes feel like a moving meditation. Her yin and restorative practices draw from Taoist philosophy and Chinese medicine. A true healer on and off the mat.',
                'specialties': 'Yin Yoga, Restorative, Meditation, Sound Healing',
                'years_experience': 12,
                'certifications': 'RYT-500, Yin Yoga Teacher Training, Sound Healer Certification',
                'photo_url': 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=400&q=80',
                'email': 'luna@siriusyoga.com.au',
                'phone': '+61 400 444 555',
                'instagram': '@lunawilliamsyoga',
            },
            {
                'name': 'Dr. Priya Sharma',
                'bio': 'A licensed physiotherapist and certified yoga teacher, Priya specialises in prenatal and therapeutic yoga. Her evidence-based approach ensures every pose is safe, effective, and deeply nourishing.',
                'specialties': 'Prenatal Yoga, Therapeutic Yoga, Pilates',
                'years_experience': 9,
                'certifications': 'RYT-500, Prenatal Yoga Specialist, Pilates Mat Instructor',
                'photo_url': 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&q=80',
                'email': 'priya@siriusyoga.com.au',
                'phone': '+61 400 555 666',
                'instagram': '@drpriyayoga',
            },
        ]

        instructors = {}
        for data in instructors_data:
            photo_url = data.pop('photo_url')
            data['photo_url'] = photo_url
            inst, created = Instructor.objects.get_or_create(
                name=data['name'], defaults=data
            )
            if created:
                self.stdout.write(f'  Created instructor: {inst.name}')
            instructors[data['name']] = inst

        # Membership Plans
        plans_data = [
            {'name': 'Single Class', 'plan_type': 'drop_in', 'price': 25.00, 'classes_included': 1, 'validity_days': 30, 'description': 'Try any single class at the studio.', 'is_active': True, 'highlight': False},
            {'name': '5 Class Pack', 'plan_type': 'pack', 'price': 110.00, 'classes_included': 5, 'validity_days': 60, 'description': 'Great for occasional visitors. Use across any class.', 'is_active': True, 'highlight': False},
            {'name': '10 Class Pack', 'plan_type': 'pack', 'price': 200.00, 'classes_included': 10, 'validity_days': 90, 'description': 'Our best value class pack. Attend any class, any time.', 'is_active': True, 'highlight': True},
            {'name': 'Unlimited Monthly', 'plan_type': 'unlimited', 'price': 120.00, 'classes_included': None, 'validity_days': 30, 'description': 'Unlimited classes for one month. Perfect for dedicated practitioners.', 'is_active': True, 'highlight': False},
        ]
        for data in plans_data:
            MembershipPlan.objects.get_or_create(name=data['name'], defaults=data)
        self.stdout.write('  Created membership plans')

        # Class photo URLs from Unsplash (free to embed)
        class_photos = {
            'Morning Flow Vinyasa':        'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=800&q=80',
            'Gentle Hatha Yoga':           'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800&q=80',
            'Power Yoga':                  'https://images.unsplash.com/photo-1599901860904-17e6ed7083a0?w=800&q=80',
            'Yin Yoga & Meditation':       'https://images.unsplash.com/photo-1508672019048-805c876b67e2?w=800&q=80',
            'Prenatal Yoga':               'https://images.unsplash.com/photo-1518310952931-b1de897abd40?w=800&q=80',
            'Reformer Pilates – Foundations': 'https://images.unsplash.com/photo-1545205597-3d9d02c29597?w=800&q=80',
            'Reformer Pilates – Progress': 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=800&q=80',
            'Breathwork & Meditation':     'https://images.unsplash.com/photo-1593811167562-9cef47bfc4d7?w=800&q=80',
        }

        # Yoga Classes
        classes_data = [
            {'name': 'Morning Flow Vinyasa', 'description': 'Energize your morning with a dynamic vinyasa flow that synchronizes breath and movement. Perfect for building strength and flexibility while awakening your body and mind for the day ahead. This class moves at a moderate pace with options given for all levels.', 'instructor': 'Sarah Chen', 'duration_minutes': 60, 'price': 25.00, 'level': 'all', 'category': 'yoga', 'max_participants': 15, 'what_to_bring': 'Yoga mat (loaners available), water bottle, comfortable activewear', 'cancellation_hours': 12},
            {'name': 'Gentle Hatha Yoga', 'description': 'A slow-paced, mindful class focusing on foundational poses, proper alignment, and deep breathing. Ideal for beginners or those seeking a restorative practice. You will leave feeling grounded, stretched, and calm.', 'instructor': 'Maya Patel', 'duration_minutes': 75, 'price': 20.00, 'level': 'beginner', 'category': 'yoga', 'max_participants': 12, 'what_to_bring': 'Comfortable clothing, water, mat (provided)', 'cancellation_hours': 8},
            {'name': 'Power Yoga', 'description': 'An intense, fitness-based approach to vinyasa yoga. Builds serious strength, flexibility, and mental focus. Expect challenging sequences, creative flows, and a serious sweat. Modifications are available but this class is best suited to those with some yoga experience.', 'instructor': 'James Torres', 'duration_minutes': 60, 'price': 30.00, 'level': 'intermediate', 'category': 'yoga', 'max_participants': 10, 'what_to_bring': 'Yoga mat, towel, water bottle, grip socks recommended', 'cancellation_hours': 12, 'prerequisite_note': 'Some yoga experience recommended. Not suitable for complete beginners.'},
            {'name': 'Yin Yoga & Meditation', 'description': 'A deeply relaxing practice that targets the connective tissues through long-held, passive poses. Combined with guided meditation, this class releases deep tension and cultivates inner stillness. Perfect for unwinding after a long day.', 'instructor': 'Luna Williams', 'duration_minutes': 90, 'price': 28.00, 'level': 'all', 'category': 'yin', 'max_participants': 15, 'what_to_bring': 'Blanket, bolster (provided), comfortable warm clothing', 'cancellation_hours': 12},
            {'name': 'Prenatal Yoga', 'description': 'A safe and nurturing practice designed specifically for expecting mothers at all stages of pregnancy. Focuses on gentle stretching, breathing techniques for labour, pelvic floor health, and building community with other expectant mothers.', 'instructor': 'Dr. Priya Sharma', 'duration_minutes': 60, 'price': 35.00, 'level': 'beginner', 'category': 'prenatal', 'max_participants': 8, 'what_to_bring': 'Comfortable clothing, water, pillow for support', 'cancellation_hours': 24, 'prerequisite_note': 'Suitable for all trimesters. Please inform instructor of your stage of pregnancy.'},
            {'name': 'Reformer Pilates \u2013 Foundations', 'description': 'Learn the fundamentals of Reformer Pilates in a small group setting. This class covers spring resistance, carriage movement, and core activation. You will build precision, control, and deep core strength from the very first session.', 'instructor': 'Dr. Priya Sharma', 'duration_minutes': 55, 'price': 45.00, 'level': 'beginner', 'category': 'reformer', 'max_participants': 6, 'what_to_bring': 'Grip socks (required), fitted activewear, water', 'cancellation_hours': 24, 'prerequisite_note': 'No experience necessary. This is the starting point for all Reformer classes.'},
            {'name': 'Reformer Pilates \u2013 Progress', 'description': 'Build on your Reformer foundations with more complex exercises, transitions, and spring configurations. This intermediate class challenges your stability, coordination, and mind-body connection. Small group format for personalised attention.', 'instructor': 'Dr. Priya Sharma', 'duration_minutes': 55, 'price': 48.00, 'level': 'intermediate', 'category': 'reformer', 'max_participants': 6, 'what_to_bring': 'Grip socks (required), fitted activewear, water', 'cancellation_hours': 24, 'prerequisite_note': 'Must have completed at least 5 sessions of Reformer Foundations or equivalent.'},
            {'name': 'Breathwork & Meditation', 'description': 'A powerful practice combining conscious breathwork techniques (pranayama, holotropic breathing, box breathing) with guided meditation. Expect emotional release, mental clarity, and a profound sense of calm. No movement required.', 'instructor': 'Luna Williams', 'duration_minutes': 60, 'price': 22.00, 'level': 'all', 'category': 'breathwork', 'max_participants': 20, 'what_to_bring': 'Comfortable clothing, blanket, open mind', 'cancellation_hours': 8},
        ]

        schedules_map = {
            'Morning Flow Vinyasa':        [('Monday','07:00','08:00'),('Wednesday','07:00','08:00'),('Friday','07:00','08:00'),('Saturday','08:30','09:30')],
            'Gentle Hatha Yoga':           [('Tuesday','09:00','10:15'),('Thursday','09:00','10:15'),('Saturday','10:00','11:15')],
            'Power Yoga':                  [('Monday','18:00','19:00'),('Wednesday','18:00','19:00'),('Saturday','08:00','09:00')],
            'Yin Yoga & Meditation':       [('Tuesday','19:00','20:30'),('Friday','19:00','20:30'),('Sunday','17:00','18:30')],
            'Prenatal Yoga':               [('Wednesday','10:00','11:00'),('Saturday','11:30','12:30')],
            'Reformer Pilates \u2013 Foundations': [('Monday','10:00','10:55'),('Thursday','10:00','10:55')],
            'Reformer Pilates \u2013 Progress': [('Tuesday','17:00','17:55'),('Thursday','17:00','17:55'),('Saturday','09:00','09:55')],
            'Breathwork & Meditation':     [('Wednesday','19:30','20:30'),('Sunday','09:00','10:00')],
        }

        day_map = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}
        today = timezone.now().date()

        for cls_data in classes_data:
            instructor_name = cls_data.pop('instructor')
            photo_url = class_photos.get(cls_data['name'], '')
            cls_data['instructor'] = instructors.get(instructor_name)
            yoga_class, created = YogaClass.objects.get_or_create(
                name=cls_data['name'], defaults=cls_data
            )
            if not created:
                self.stdout.write(f'  Exists: {yoga_class.name}')
                continue

            if photo_url:
                yoga_class.photo_url = photo_url
                yoga_class.save()
            self.stdout.write(f'  Created: {yoga_class.name}')

            for day, start, end in schedules_map.get(yoga_class.name, []):
                Schedule.objects.create(
                    yoga_class=yoga_class, day_of_week=day,
                    start_time=start, end_time=end
                )
            for week in range(4):
                for day, start_str, end_str in schedules_map.get(yoga_class.name, []):
                    target_weekday = day_map[day]
                    days_ahead = (target_weekday - today.weekday()) % 7
                    if days_ahead == 0 and week == 0:
                        days_ahead = 7
                    session_date = today + datetime.timedelta(days=days_ahead + week * 7)
                    start_time = datetime.time(int(start_str.split(':')[0]), int(start_str.split(':')[1]))
                    end_time = datetime.time(int(end_str.split(':')[0]), int(end_str.split(':')[1]))
                    ClassSession.objects.get_or_create(
                        yoga_class=yoga_class, date=session_date, start_time=start_time,
                        defaults={'end_time': end_time, 'status': 'scheduled'}
                    )

        self.stdout.write(self.style.SUCCESS('\n🎉 Done! Visit http://127.0.0.1:8000/'))
        self.stdout.write('Admin: admin / admin123')
