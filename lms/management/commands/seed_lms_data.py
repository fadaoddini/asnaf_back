from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from lms.models import Grade, Subject, Chapter, Teacher, Student, Question, QuestionOption, Skill
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed complete initial data for LMS'

    def handle(self, *args, **options):

        # ========== 1. ایجاد پایه‌های تحصیلی کامل ==========
        grades_data = [
            ('اول دبستان', 'elementary', 1),
            ('دوم دبستان', 'elementary', 2),
            ('سوم دبستان', 'elementary', 3),
            ('چهارم دبستان', 'elementary', 4),
            ('پنجم دبستان', 'elementary', 5),
            ('ششم دبستان', 'elementary', 6),
            ('هفتم', 'middle', 1),
            ('هشتم', 'middle', 2),
            ('نهم', 'middle', 3),
            ('دهم', 'high', 1),
            ('یازدهم', 'high', 2),
            ('دوازدهم', 'high', 3),
        ]

        grades = {}
        for name, level, order in grades_data:
            grade, _ = Grade.objects.get_or_create(
                name=name,
                defaults={'level': level, 'order': order, 'is_active': True}
            )
            grades[name] = grade
            self.stdout.write(f"  ✓ پایه {name} ایجاد شد")

        # ========== 2. ایجاد دروس برای هر پایه ==========
        subjects_data = {
            'اول دبستان': ['ریاضی', 'علوم', 'فارسی', 'قرآن'],
            'دوم دبستان': ['ریاضی', 'علوم', 'فارسی', 'قرآن'],
            'سوم دبستان': ['ریاضی', 'علوم', 'فارسی', 'قرآن', 'اجتماعی'],
            'چهارم دبستان': ['ریاضی', 'علوم', 'فارسی', 'قرآن', 'اجتماعی', 'هدیه‌های آسمان'],
            'پنجم دبستان': ['ریاضی', 'علوم', 'فارسی', 'قرآن', 'اجتماعی', 'هدیه‌های آسمان'],
            'ششم دبستان': ['ریاضی', 'علوم', 'فارسی', 'قرآن', 'اجتماعی', 'هدیه‌های آسمان'],
            'هفتم': ['ریاضی', 'علوم', 'فارسی', 'عربی', 'انگلیسی', 'اجتماعی', 'قرآن'],
            'هشتم': ['ریاضی', 'علوم', 'فارسی', 'عربی', 'انگلیسی', 'اجتماعی', 'قرآن'],
            'نهم': ['ریاضی', 'علوم', 'فارسی', 'عربی', 'انگلیسی', 'اجتماعی', 'قرآن'],
            'دهم': ['ریاضی', 'فیزیک', 'شیمی', 'زیست‌شناسی', 'فارسی', 'عربی', 'انگلیسی', 'دین و زندگی'],
            'یازدهم': ['ریاضی', 'فیزیک', 'شیمی', 'زیست‌شناسی', 'فارسی', 'عربی', 'انگلیسی', 'دین و زندگی'],
            'دوازدهم': ['ریاضی', 'فیزیک', 'شیمی', 'زیست‌شناسی', 'فارسی', 'عربی', 'انگلیسی', 'دین و زندگی'],
        }

        for grade_name, subject_list in subjects_data.items():
            grade = grades[grade_name]
            for subj_name in subject_list:
                Subject.objects.get_or_create(
                    grade=grade,
                    name=subj_name,
                    defaults={'is_active': True}
                )
            self.stdout.write(f"  ✓ دروس پایه {grade_name} ایجاد شد")

        # ========== 3. ایجاد فصل‌های نمونه برای ریاضی پایه هفتم ==========
        math_grade7 = Subject.objects.get(grade=grades['هفتم'], name='ریاضی')
        chapters_math7 = [
            'راهبردهای حل مسئله', 'اعداد صحیح', 'جبر و معادله', 'هندسه و استدلال',
            'مساحت و حجم', 'توان و جذر', 'احتمال و آمار'
        ]
        for idx, chapter_name in enumerate(chapters_math7, 1):
            Chapter.objects.get_or_create(
                grade=grades['هفتم'],
                subject=math_grade7,
                name=chapter_name,
                defaults={'is_active': True}
            )
        self.stdout.write(f"  ✓ فصل‌های ریاضی پایه هفتم ایجاد شد")

        # ========== 4. ایجاد معلم نمونه ==========
        mobile = '09121111111'

        # ایجاد کاربر با mobile به جای username
        teacher_user, created = User.objects.get_or_create(
            mobile=mobile,
            defaults={
                'first_name': 'رضا',
                'last_name': 'کریمی',
                'is_staff': True,
            }
        )

        if created:
            teacher_user.set_password('123456')
            teacher_user.save()
            self.stdout.write(f"  ✓ کاربر معلم با شماره {mobile} ایجاد شد")
        else:
            self.stdout.write(f"  ✓ کاربر معلم با شماره {mobile} قبلاً وجود دارد")

        # ایجاد پروفایل معلم
        teacher, created = Teacher.objects.get_or_create(
            user=teacher_user,
            defaults={
                'first_name': 'رضا',
                'last_name': 'کریمی',
                'mobile': mobile,
                'school_name': 'مدرسه نمونه',
                'qualification': 'master',
                'experience': '5-10',
                'is_approved': True
            }
        )

        if created:
            self.stdout.write(f"  ✓ معلم {teacher.first_name} {teacher.last_name} ایجاد شد")
        else:
            self.stdout.write(f"  ✓ معلم {teacher.first_name} {teacher.last_name} قبلاً وجود دارد")

        # ========== 5. ایجاد سوالات نمونه ==========
        first_chapter = Chapter.objects.filter(subject=math_grade7).first()
        chapters_list = list(Chapter.objects.filter(subject=math_grade7))

        # سوال 1 - آسان
        q1 = Question.objects.create(
            teacher=teacher,
            text='حاصل عبارت ۵ - (-۳) برابر است با؟',
            grade=grades['هفتم'],
            subject=math_grade7,
            chapter=first_chapter,
            difficulty='easy',
            estimated_time=45,
            explanation='منفی در منفی میشود مثبت: ۵ + ۳ = ۸'
        )
        QuestionOption.objects.bulk_create([
            QuestionOption(question=q1, text='۲', order=1, is_correct=False),
            QuestionOption(question=q1, text='-۲', order=2, is_correct=False),
            QuestionOption(question=q1, text='۸', order=3, is_correct=True),
            QuestionOption(question=q1, text='-۸', order=4, is_correct=False),
        ])

        # سوال 2 - متوسط
        if len(chapters_list) > 1:
            q2 = Question.objects.create(
                teacher=teacher,
                text='کدام یک از اعداد زیر اول است؟',
                grade=grades['هفتم'],
                subject=math_grade7,
                chapter=chapters_list[1],
                difficulty='medium',
                estimated_time=60,
                explanation='عدد اول فقط بر ۱ و خودش بخش‌پذیر است'
            )
            QuestionOption.objects.bulk_create([
                QuestionOption(question=q2, text='۴', order=1, is_correct=False),
                QuestionOption(question=q2, text='۹', order=2, is_correct=False),
                QuestionOption(question=q2, text='۱۱', order=3, is_correct=True),
                QuestionOption(question=q2, text='۱۵', order=4, is_correct=False),
            ])

        # سوال 3 - سخت
        if len(chapters_list) > 2:
            q3 = Question.objects.create(
                teacher=teacher,
                text='اگر x = ۲ و y = -۳ باشد، مقدار x² - 2xy + y² برابر است با؟',
                grade=grades['هفتم'],
                subject=math_grade7,
                chapter=chapters_list[2],
                difficulty='hard',
                estimated_time=90,
                explanation='x²=4, 2xy=-12, y²=9 → 4 - (-12) + 9 = 4+12+9=25'
            )
            QuestionOption.objects.bulk_create([
                QuestionOption(question=q3, text='۱۶', order=1, is_correct=False),
                QuestionOption(question=q3, text='۲۰', order=2, is_correct=False),
                QuestionOption(question=q3, text='۲۵', order=3, is_correct=True),
                QuestionOption(question=q3, text='۳۰', order=4, is_correct=False),
            ])

        self.stdout.write(f"  ✓ {Question.objects.filter(teacher=teacher).count()} سوال نمونه ایجاد شد")

        # ========== 6. ایجاد دانش‌آموزان نمونه ==========
        students_data = [
            ('احمد', 'رضایی', '09131111111', 'هفتم'),
            ('سارا', 'محمدی', '09132222222', 'هفتم'),
            ('مهدی', 'کریمی', '09133333333', 'هشتم'),
        ]

        for first, last, mobile_student, grade_name in students_data:
            # ایجاد کاربر دانش‌آموز
            student_user, created = User.objects.get_or_create(
                mobile=mobile_student,
                defaults={
                    'first_name': first,
                    'last_name': last,
                }
            )

            if created:
                student_user.set_password('123456')
                student_user.save()
                self.stdout.write(f"  ✓ کاربر دانش‌آموز با شماره {mobile_student} ایجاد شد")

            # ایجاد پروفایل دانش‌آموز
            student, created = Student.objects.get_or_create(
                user=student_user,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'mobile': mobile_student,
                    'grade': grades[grade_name]
                }
            )

            if created:
                self.stdout.write(f"  ✓ دانش‌آموز {first} {last} ایجاد شد")

        self.stdout.write(f"  ✓ مجموع دانش‌آموزان: {Student.objects.count()}")

        # ========== 7. ایجاد مهارت‌ها و اضافه به معلم ==========
        skills_data = [
            {'name': 'ریاضیات', 'name_en': 'Mathematics', 'category': 'ریاضی', 'icon': '📐', 'color': '#3B82F6',
             'description': 'ریاضیات پایه تا پیشرفته'},
            {'name': 'فیزیک', 'name_en': 'Physics', 'category': 'علوم', 'icon': '⚛️', 'color': '#10B981',
             'description': 'فیزیک پایه و مفاهیم بنیادی'},
            {'name': 'برنامه‌نویسی پایتون', 'name_en': 'Python Programming', 'category': 'برنامه‌نویسی', 'icon': '🐍',
             'color': '#8B5CF6', 'description': 'آموزش پایتون از مقدماتی تا پیشرفته'},
            {'name': 'زبان انگلیسی', 'name_en': 'English', 'category': 'زبان', 'icon': '🇬🇧', 'color': '#EF4444',
             'description': 'زبان انگلیسی عمومی و تخصصی'},
        ]

        for skill_data in skills_data:
            skill, created = Skill.objects.get_or_create(
                name=skill_data['name'],
                defaults=skill_data
            )
            if created:
                self.stdout.write(f"  ✓ مهارت {skill.name} ایجاد شد")

        # اضافه کردن مهارت به معلم
        all_skills = Skill.objects.all()
        if all_skills.exists():
            teacher.skills.set(all_skills)
            self.stdout.write(f"  ✓ {all_skills.count()} مهارت به معلم اضافه شد")

        # ========== جمع‌بندی نهایی ==========
        self.stdout.write(self.style.SUCCESS('\n🎉 تمام داده‌های اولیه با موفقیت ایجاد شدند!'))
        self.stdout.write(f'📊 آمار نهایی:')
        self.stdout.write(f'   - پایه‌های تحصیلی: {Grade.objects.count()}')
        self.stdout.write(f'   - دروس: {Subject.objects.count()}')
        self.stdout.write(f'   - فصل‌ها: {Chapter.objects.count()}')
        self.stdout.write(f'   - سوالات: {Question.objects.count()}')
        self.stdout.write(f'   - دانش‌آموزان: {Student.objects.count()}')
        self.stdout.write(f'   - مهارت‌ها: {Skill.objects.count()}')
        self.stdout.write(f'\n📝 اطلاعات ورود:')
        self.stdout.write(f'   - معلم: شماره {mobile} / رمز 123456')
        self.stdout.write(f'   - دانش‌آموزان: شماره‌های 09131111111, 09132222222, 09133333333 / رمز 123456')