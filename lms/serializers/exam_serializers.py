from rest_framework import serializers
from django.utils import timezone
from ..models import Exam, Student, Teacher, Grade, Subject, Chapter, ExamAttempt


# lms/serializers/exam_serializers.py

class ExamSerializer(serializers.ModelSerializer):
    """سریالایزر کامل آزمون"""

    teacher_name = serializers.SerializerMethodField(read_only=True)
    invited_students_count = serializers.SerializerMethodField(read_only=True)
    invited_students_detail = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.SerializerMethodField(read_only=True)
    entry_window_display = serializers.SerializerMethodField(read_only=True)

    # اضافه کردن این سه فیلد برای نمایش اطلاعات پایه، درس و فصل
    grade_id = serializers.IntegerField(source='grade.id', read_only=True)
    grade_name = serializers.CharField(source='grade.name', read_only=True)
    subject_id = serializers.IntegerField(source='subject.id', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    chapter_id = serializers.IntegerField(source='chapter.id', read_only=True)
    chapter_name = serializers.CharField(source='chapter.name', read_only=True)

    class Meta:
        model = Exam
        fields = [
            'id', 'title', 'description', 'teacher', 'teacher_name',
            'duration_minutes', 'allowed_entry_start', 'allowed_entry_end',
            'entry_window_display', 'is_limited', 'allow_go_back',
            'total_questions_count', 'easy_percent', 'medium_percent', 'hard_percent',
            'randomize_questions', 'randomize_options',
            'show_answer_key_immediately', 'show_score_immediately',
            'is_published', 'created_at', 'invited_students_count',
            'invited_students_detail', 'status_display',
            # اضافه کردن فیلدهای جدید
            'grade', 'grade_id', 'grade_name',
            'subject', 'subject_id', 'subject_name',
            'chapter', 'chapter_id', 'chapter_name'
        ]
        read_only_fields = ['id', 'teacher', 'created_at']

    def get_teacher_name(self, obj):
        if obj.teacher:
            return f"{obj.teacher.first_name} {obj.teacher.last_name}"
        return ''

    def get_invited_students_count(self, obj):
        return obj.invited_students.count()

    def get_invited_students_detail(self, obj):
        return [
            {
                'id': s.id,
                'first_name': s.first_name,
                'last_name': s.last_name,
                'name': f"{s.first_name} {s.last_name}",
                'mobile': s.mobile,
                'grade_name': s.grade.name if s.grade else None
            }
            for s in obj.invited_students.all()
        ]

    def get_status_display(self, obj):
        now = timezone.now()
        if not obj.is_published:
            return 'پیش‌نویس'
        if now < obj.allowed_entry_start:
            return 'در انتظار شروع'
        if obj.allowed_entry_start <= now <= obj.allowed_entry_end:
            return 'فعال'
        return 'پایان یافته'

    def get_entry_window_display(self, obj):
        start = obj.allowed_entry_start.strftime('%Y/%m/%d %H:%M')
        end = obj.allowed_entry_end.strftime('%Y/%m/%d %H:%M')
        return f"{start} تا {end}"


# lms/serializers/exam_serializers.py

class ExamListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست آزمون‌ها"""

    teacher_name = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.SerializerMethodField(read_only=True)
    invited_count = serializers.SerializerMethodField(read_only=True)

    # اضافه کردن فیلدهای پایه، درس و فصل
    grade_name = serializers.CharField(source='grade.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    chapter_name = serializers.CharField(source='chapter.name', read_only=True)

    class Meta:
        model = Exam
        fields = [
            'id', 'title', 'teacher', 'teacher_name', 'duration_minutes',
            'total_questions_count', 'is_published', 'created_at',
            'invited_count', 'status_display', 'easy_percent', 'medium_percent', 'hard_percent',
            'allowed_entry_start', 'allowed_entry_end',
            'grade', 'grade_name', 'subject', 'subject_name', 'chapter', 'chapter_name'
        ]

    def get_teacher_name(self, obj):
        if obj.teacher:
            return f"{obj.teacher.first_name} {obj.teacher.last_name}"
        return ''

    def get_status_display(self, obj):
        now = timezone.now()
        if not obj.is_published:
            return 'پیش‌نویس'
        if now < obj.allowed_entry_start:
            return 'در انتظار شروع'
        if obj.allowed_entry_start <= now <= obj.allowed_entry_end:
            return 'فعال'
        return 'پایان یافته'

    def get_invited_count(self, obj):
        """تعداد دانش‌آموزان دعوت شده به آزمون"""
        return obj.invited_students.count()


class ExamCreateSerializer(serializers.ModelSerializer):
    invited_students_mobiles = serializers.ListField(
        child=serializers.CharField(max_length=11),
        write_only=True,
        required=False,
        default=list
    )

    class Meta:
        model = Exam
        fields = [
            'title', 'description', 'duration_minutes',
            'allowed_entry_start', 'allowed_entry_end', 'is_limited',
            'allow_go_back', 'total_questions_count', 'easy_percent',
            'medium_percent', 'hard_percent', 'randomize_questions',
            'randomize_options', 'show_answer_key_immediately',
            'show_score_immediately', 'is_published',
            'grade', 'subject', 'chapter',  # اضافه کردن این سه فیلد
            'invited_students_mobiles'
        ]

    def validate(self, data):
        # اعتبارسنجی شرایط آزمون
        easy = data.get('easy_percent', 0)
        medium = data.get('medium_percent', 0)
        hard = data.get('hard_percent', 0)

        if easy + medium + hard != 100:
            raise serializers.ValidationError(
                "مجموع درصدهای سختی باید برابر ۱۰۰ باشد"
            )

        start = data.get('allowed_entry_start')
        end = data.get('allowed_entry_end')

        if start and end and start >= end:
            raise serializers.ValidationError(
                "زمان پایان باید بعد از زمان شروع باشد"
            )

        if start and start < timezone.now():
            raise serializers.ValidationError(
                "زمان شروع نمی‌تواند در گذشته باشد"
            )

        return data

    def create(self, validated_data):
        invited_mobiles = validated_data.pop('invited_students_mobiles', [])
        teacher = self.context['request'].user.teacher_profile

        exam = Exam.objects.create(teacher=teacher, **validated_data)

        if invited_mobiles:
            students = Student.objects.filter(mobile__in=invited_mobiles)
            exam.invited_students.set(students)

        return exam


# lms/serializers/exam_serializers.py

class ExamUpdateSerializer(serializers.ModelSerializer):
    """سریالایزر بروزرسانی آزمون"""

    # اضافه کردن این فیلد برای دریافت دانش‌آموزان دعوت شده
    invited_students_mobiles = serializers.ListField(
        child=serializers.CharField(max_length=11),
        write_only=True,
        required=False,
        default=list
    )

    class Meta:
        model = Exam
        fields = [
            'title', 'description', 'duration_minutes',
            'allowed_entry_start', 'allowed_entry_end', 'is_limited',
            'allow_go_back', 'total_questions_count', 'easy_percent',
            'medium_percent', 'hard_percent', 'randomize_questions',
            'randomize_options', 'show_answer_key_immediately',
            'show_score_immediately', 'is_published',
            'grade', 'subject', 'chapter',  # فیلدهای جدید
            'invited_students_mobiles'  # اضافه شده
        ]

    def validate(self, data):
        easy = data.get('easy_percent', 0)
        medium = data.get('medium_percent', 0)
        hard = data.get('hard_percent', 0)

        if easy + medium + hard != 100:
            raise serializers.ValidationError(
                "مجموع درصدهای سختی باید برابر ۱۰۰ باشد"
            )

        return data

    def update(self, instance, validated_data):
        # جدا کردن دانش‌آموزان از بقیه داده‌ها
        invited_mobiles = validated_data.pop('invited_students_mobiles', None)

        # بروزرسانی فیلدهای دیگر
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # بروزرسانی دانش‌آموزان دعوت شده
        if invited_mobiles is not None:
            from ..models import Student
            students = Student.objects.filter(mobile__in=invited_mobiles)
            instance.invited_students.set(students)

        return instance


class ExamStudentCheckSerializer(serializers.Serializer):
    """سریالایزر بررسی دسترسی دانش‌آموز به آزمون"""

    exam_id = serializers.IntegerField()
    mobile = serializers.CharField(max_length=11)

    def validate_mobile(self, value):
        import re
        if not re.match(r'^09[0-9]{9}$', value):
            raise serializers.ValidationError("شماره همراه معتبر نیست")
        return value

    def validate(self, data):
        from ..models import Exam, Student

        exam_id = data.get('exam_id')
        mobile = data.get('mobile')

        try:
            exam = Exam.objects.get(id=exam_id, is_published=True)
        except Exam.DoesNotExist:
            raise serializers.ValidationError({"exam_id": "آزمون یافت نشد یا منتشر نشده است"})

        try:
            student = Student.objects.get(mobile=mobile)
        except Student.DoesNotExist:
            raise serializers.ValidationError({"mobile": "دانش‌آموزی با این شماره همراه یافت نشد"})

        # بررسی دعوت شدن
        if not exam.invited_students.filter(id=student.id).exists():
            raise serializers.ValidationError(
                "شما به این آزمون دعوت نشده‌اید"
            )

        # بررسی زمان مجاز
        now = timezone.now()
        if now < exam.allowed_entry_start:
            raise serializers.ValidationError(
                f"زمان ورود به آزمون از {exam.allowed_entry_start.strftime('%Y/%m/%d %H:%M')} شروع می‌شود"
            )

        if now > exam.allowed_entry_end:
            raise serializers.ValidationError(
                "زمان مجاز برای شرکت در این آزمون به پایان رسیده است"
            )

        # بررسی شرکت قبلی
        if ExamAttempt.objects.filter(
                student=student,
                exam=exam,
                status='completed'
        ).exists():
            raise serializers.ValidationError("شما قبلاً در این آزمون شرکت کرده‌اید")

        data['exam'] = exam
        data['student'] = student
        return data