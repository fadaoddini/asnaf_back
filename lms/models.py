import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

MyUser = get_user_model()


# ========== مسیرهای ذخیره فایل ==========
def teacher_profile_path(instance, filename):
    return f'lms/teachers/profiles/{uuid.uuid4()}/{filename}'


def question_image_path(instance, filename):
    return f'lms/questions/images/{uuid.uuid4()}/{filename}'


def option_image_path(instance, filename):
    return f'lms/questions/options/{uuid.uuid4()}/{filename}'


# ========== مدل پایه تحصیلی (کامل) ==========
class Grade(models.Model):
    LEVEL_CHOICES = (
        ('elementary', 'دبستان'),
        ('middle', 'متوسطه اول'),
        ('high', 'متوسطه دوم'),
        ('pre_university', 'پیش دانشگاهی'),
    )

    name = models.CharField(max_length=100,
                            verbose_name='نام پایه')  # اول دبستان, دوم دبستان, ..., هفتم, هشتم, نهم, ...
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, verbose_name='مقطع تحصیلی')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ['level', 'order']
        verbose_name = 'پایه تحصیلی'
        verbose_name_plural = 'پایه‌های تحصیلی'

    def __str__(self):
        return f"{self.get_level_display()} - {self.name}"


# ========== مدل درس ==========
class Subject(models.Model):
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100, verbose_name='نام درس')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'درس'
        verbose_name_plural = 'دروس'

    def __str__(self):
        return f"{self.grade.name} - {self.name}"


# ========== مدل فصل ==========
class Chapter(models.Model):
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, verbose_name='پایه تحصیلی')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='chapters')
    name = models.CharField(max_length=100, verbose_name='عنوان فصل')
    is_active = models.BooleanField(default=True)
    class Meta:
        verbose_name = 'فصل'
        verbose_name_plural = 'فصل‌ها'

    def __str__(self):
        return f"{self.subject.name} - {self.name}"


# ========== مدل معلم ==========

class Teacher(models.Model):
    QUALIFICATION_CHOICES = (
        ('diploma', 'دیپلم'),
        ('associate', 'کاردانی'),
        ('bachelor', 'کارشناسی'),
        ('master', 'کارشناسی ارشد'),
        ('doctorate', 'دکترا'),
    )

    EXPERIENCE_CHOICES = (
        ('0-1', 'کمتر از ۱ سال'),
        ('1-3', '۱ تا ۳ سال'),
        ('3-5', '۳ تا ۵ سال'),
        ('5-10', '۵ تا ۱۰ سال'),
        ('10+', 'بیش از ۱۰ سال'),
    )

    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, related_name='teacher_profile')
    first_name = models.CharField(max_length=50, verbose_name='نام')
    last_name = models.CharField(max_length=50, verbose_name='نام خانوادگی')
    mobile = models.CharField(max_length=11, unique=True, verbose_name='شماره همراه')
    email = models.EmailField(blank=True, null=True, verbose_name='ایمیل')

    # فیلدهای جدید
    school_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='نام مدرسه')
    description = models.TextField(blank=True, null=True, verbose_name='درباره من')
    qualification = models.CharField(max_length=20, choices=QUALIFICATION_CHOICES, blank=True, null=True,
                                     verbose_name='مدرک تحصیلی')
    experience = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES, blank=True, null=True,
                                  verbose_name='سابقه تدریس')
    skills = models.ManyToManyField('Skill', blank=True, related_name='teachers', verbose_name='مهارت‌ها')

    profile_image = models.ImageField(upload_to=teacher_profile_path, null=True, blank=True)
    certificate = models.FileField(upload_to='lms/teachers/certificates/', null=True, blank=True,
                                   verbose_name='مدرک تحصیلی')

    is_approved = models.BooleanField(default=False, verbose_name='تایید شده')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'معلم'
        verbose_name_plural = 'معلمان'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def qualification_display(self):
        return dict(self.QUALIFICATION_CHOICES).get(self.qualification, '')

    @property
    def experience_display(self):
        return dict(self.EXPERIENCE_CHOICES).get(self.experience, '')

    @property
    def status_display(self):
        if self.is_approved:
            return 'تایید شده'
        return 'در انتظار تایید'

    @property
    def profile_image_url(self):
        if self.profile_image:
            return self.profile_image.url
        return None

    @property
    def certificate_url(self):
        if self.certificate:
            return self.certificate.url
        return None


class Skill(models.Model):
    """مدل مهارت‌های تدریس"""
    name = models.CharField(max_length=100, unique=True, verbose_name='نام مهارت')
    name_en = models.CharField(max_length=100, blank=True, null=True, verbose_name='نام انگلیسی')
    icon = models.CharField(max_length=10, default='📚', verbose_name='آیکون')
    category = models.CharField(max_length=50, default='عمومی', verbose_name='دسته‌بندی')
    color = models.CharField(max_length=20, default='#10B981', verbose_name='رنگ')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'مهارت'
        verbose_name_plural = 'مهارت‌ها'

    def __str__(self):
        return self.name


# ========== مدل سوال (فقط ۴ گزینه‌ای) ==========
class Question(models.Model):
    DIFFICULTY_CHOICES = (
        ('easy', 'آسان'),
        ('medium', 'متوسط'),
        ('hard', 'سخت'),
    )

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name='متن سوال')

    # دسته‌بندی کامل
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, verbose_name='پایه تحصیلی')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='عنوان درس')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, verbose_name='عنوان فصل', null=True, blank=True)

    # ویژگی‌های سوال
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, verbose_name='درجه سختی')
    estimated_time = models.PositiveIntegerField(help_text='ثانیه', verbose_name='مدت زمان لازم برای پاسخ دادن (ثانیه)')

    # امکانات اضافی
    image = models.ImageField(upload_to=question_image_path, null=True, blank=True)
    explanation = models.TextField(blank=True, verbose_name='توضیح پاسخ')

    # وضعیت
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سوال'
        verbose_name_plural = 'بانک سوالات'

    def __str__(self):
        return f"{self.text[:50]}..."


# ========== مدل گزینه‌های سوال (دقیقا ۴ گزینه) ==========
class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.TextField(verbose_name='متن گزینه', blank=True, null=True)
    image = models.ImageField(upload_to=option_image_path, null=True, blank=True)
    is_correct = models.BooleanField(default=False, verbose_name='گزینه صحیح')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        verbose_name = 'گزینه سوال'
        verbose_name_plural = 'گزینه‌های سوال'
        ordering = ['order']
        # اطمینان از حداکثر ۴ گزینه در سطح کد (اجباری نیست در دیتابیس)

    def __str__(self):
        return f"{self.question.text[:30]} - {self.text[:30]}"


# ========== مدل دانش‌آموز ==========

# lms/models.py - اضافه کردن فیلد created_by به Student

class Student(models.Model):
    user = models.OneToOneField(
        MyUser,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True
    )
    first_name = models.CharField(max_length=50, verbose_name='نام')
    last_name = models.CharField(max_length=50, verbose_name='نام خانوادگی')
    mobile = models.CharField(max_length=11, unique=True, verbose_name='شماره همراه')
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='پایه تحصیلی')
    registered_at = models.DateTimeField(auto_now_add=True)

    # اضافه کنید: معلمی که این دانش‌آموز را اضافه کرده
    created_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_students',
        verbose_name='ایجاد شده توسط'
    )

    class Meta:
        verbose_name = 'دانش‌آموز'
        verbose_name_plural = 'دانش‌آموزان'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# ========== مدل آزمون (با تمام شرایط برگزاری) ==========
class Exam(models.Model):
    # اطلاعات پایه
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=200, verbose_name='عنوان آزمون')
    description = models.TextField(blank=True, verbose_name='توضیحات')

    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='پایه تحصیلی')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='درس')
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='فصل')


    # شرایط برگزاری آزمون
    duration_minutes = models.PositiveIntegerField(verbose_name='مدت زمان آزمون (دقیقه)')
    allowed_entry_start = models.DateTimeField(verbose_name='ساعت مجاز برای ورود به آزمون (از)')
    allowed_entry_end = models.DateTimeField(verbose_name='ساعت مجاز برای ورود به آزمون (تا)')
    is_limited = models.BooleanField(default=False, verbose_name='آیا برگزاری محدود دارد؟')
    allow_go_back = models.BooleanField(default=True, verbose_name='امکان بازگشت به سوال قبل')
    total_questions_count = models.PositiveIntegerField(verbose_name='تعداد سوالات آزمون')

    # توزیع درجه سختی (پیش‌فرض همه ۰ - یعنی در صورت نبودن سوال با آن سختی، مشکلی ایجاد نشود)
    easy_percent = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)],
                                               verbose_name='درصد سوالات آسان')
    medium_percent = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)],
                                                 verbose_name='درصد سوالات متوسط')
    hard_percent = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)],
                                               verbose_name='درصد سوالات سخت')

    # تنظیمات رندوم
    randomize_questions = models.BooleanField(default=True, verbose_name='آزمون به صورت رندم ایجاد شود')
    randomize_options = models.BooleanField(default=False, verbose_name='پاسخ‌ها به صورت رندوم گزینه‌ها جابجا شوند')

    # نمایش نتایج
    show_answer_key_immediately = models.BooleanField(default=False,
                                                      verbose_name='پاسخ‌نامه بلافاصله بعد از آزمون در دسترس باشد')
    show_score_immediately = models.BooleanField(default=True, verbose_name='نمایش نمره آزمون بلافاصله نمایش داده شود')

    # وضعیت
    is_published = models.BooleanField(default=False, verbose_name='منتشر شده')
    created_at = models.DateTimeField(auto_now_add=True)

    # دانش‌آموزان دعوت شده (بر اساس موبایل)
    invited_students = models.ManyToManyField(Student, related_name='invited_exams', blank=True,
                                              verbose_name='دانش‌آموزان شرکت‌کننده')

    class Meta:
        verbose_name = 'آزمون'
        verbose_name_plural = 'آزمون‌ها'

    def __str__(self):
        return self.title

    def can_student_enter(self, student):
        """بررسی آیا دانش‌آموز مجاز به ورود است"""
        now = timezone.now()
        if not self.is_published:
            return False
        if not (self.allowed_entry_start <= now <= self.allowed_entry_end):
            return False
        if not self.invited_students.filter(id=student.id).exists():
            return False
        return True

    def get_question_distribution(self):
        """محاسبه تعداد سوالات بر اساس درصدها (با در نظر گرفتن عدم وجود سوال با درجه سختی خاص)"""
        total = self.total_questions_count
        easy_q = int(total * self.easy_percent / 100)
        medium_q = int(total * self.medium_percent / 100)
        hard_q = total - easy_q - medium_q

        return {
            'easy': easy_q,
            'medium': medium_q,
            'hard': hard_q
        }


# ========== مدل سوالات انتخاب شده برای هر دانش‌آموز (ساخت شخصی‌سازی شده) ==========
class ExamQuestionSelection(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='question_selections')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب سوال در آزمون این دانش‌آموز')

    class Meta:
        unique_together = ['exam', 'student', 'question']
        ordering = ['order']

    def __str__(self):
        return f"{self.student} - {self.exam.title} - Q{self.order}"


# ========== مدل تلاش دانش‌آموز در آزمون ==========
class ExamAttempt(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('timeout', 'زمان تمام شده'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attempts')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')

    # نتایج
    score = models.PositiveIntegerField(default=0, verbose_name='نمره کسب شده')
    total_correct = models.PositiveIntegerField(default=0, verbose_name='تعداد پاسخ صحیح')
    total_questions = models.PositiveIntegerField(default=0, verbose_name='تعداد کل سوالات')

    # زمان
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')

    class Meta:
        verbose_name = 'شرکت در آزمون'
        verbose_name_plural = 'شرکت‌های در آزمون'

    def __str__(self):
        return f"{self.student} - {self.exam.title}"

    @property
    def score_percentage(self):
        if self.total_questions == 0:
            return 0
        return (self.score / (self.total_questions * 10)) * 100


# ========== مدل پاسخ‌های دانش‌آموز ==========
class StudentAnswer(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    answer_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'پاسخ دانش‌آموز'
        verbose_name_plural = 'پاسخ‌های دانش‌آموزان'
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"{self.attempt.student} - {self.question.text[:30]}"