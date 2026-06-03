from rest_framework import serializers
from django.utils import timezone
from ..models import ExamAttempt, StudentAnswer, Question, QuestionOption, Exam, Student


class ExamQuestionOptionSerializer(serializers.ModelSerializer):
    """سریالایزر گزینه سوال برای دانش‌آموز (بدون مشخص کردن صحیح/غلط)"""

    class Meta:
        model = QuestionOption
        fields = ['id', 'text', 'image', 'order']


class ExamQuestionSerializer(serializers.ModelSerializer):
    """سریالایزر سوال برای نمایش در آزمون"""

    options = ExamQuestionOptionSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'text', 'estimated_time', 'image_url', 'options'
        ]

    def get_image_url(self, obj):
        if obj.image and obj.image.name:
            try:
                return obj.image.url
            except:
                return None
        return None


class StudentAnswerSerializer(serializers.ModelSerializer):
    """سریالایزر پاسخ دانش‌آموز"""

    question_text = serializers.CharField(source='question.text', read_only=True)
    selected_option_text = serializers.CharField(source='selected_option.text', read_only=True, allow_null=True)

    class Meta:
        model = StudentAnswer
        fields = [
            'id', 'question', 'question_text', 'selected_option',
            'selected_option_text', 'is_correct', 'answer_time'
        ]


class ExamAttemptSerializer(serializers.ModelSerializer):
    """سریالایزر شرکت در آزمون"""

    student_name = serializers.SerializerMethodField(read_only=True)
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    score_percentage = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ExamAttempt
        fields = [
            'id', 'student', 'student_name', 'exam', 'exam_title',
            'score', 'total_correct', 'total_questions', 'start_time',
            'end_time', 'status', 'status_display', 'score_percentage'
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_score_percentage(self, obj):
        if obj.total_questions == 0:
            return 0
        max_score = obj.total_questions * 10
        if max_score == 0:
            return 0
        return round((obj.score / max_score) * 100, 2)


class ExamAttemptListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست شرکت‌های در آزمون"""

    student_name = serializers.SerializerMethodField(read_only=True)
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    score_percentage = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ExamAttempt
        fields = [
            'id', 'student', 'student_name', 'exam', 'exam_title',
            'score', 'total_questions', 'score_percentage',
            'start_time', 'end_time', 'status'
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_score_percentage(self, obj):
        if obj.total_questions == 0:
            return 0
        max_score = obj.total_questions * 10
        if max_score == 0:
            return 0
        return round((obj.score / max_score) * 100, 2)


class ExamAttemptDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات کامل شرکت در آزمون"""

    student_name = serializers.SerializerMethodField(read_only=True)
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    answers = StudentAnswerSerializer(many=True, read_only=True)
    score_percentage = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ExamAttempt
        fields = [
            'id', 'student', 'student_name', 'exam', 'exam_title',
            'score', 'total_correct', 'total_questions', 'start_time',
            'end_time', 'status', 'score_percentage', 'answers'
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_score_percentage(self, obj):
        if obj.total_questions == 0:
            return 0
        max_score = obj.total_questions * 10
        if max_score == 0:
            return 0
        return round((obj.score / max_score) * 100, 2)


class StartExamRequestSerializer(serializers.Serializer):
    """سریالایزر درخواست شروع آزمون"""

    exam_id = serializers.IntegerField(required=True)
    mobile = serializers.CharField(max_length=11, required=True)

    def validate_mobile(self, value):
        import re
        if not re.match(r'^09[0-9]{9}$', value):
            raise serializers.ValidationError("شماره همراه معتبر نیست")
        return value


class StartExamResponseSerializer(serializers.Serializer):
    """سریالایزر پاسخ شروع آزمون"""

    attempt_id = serializers.IntegerField()
    exam_title = serializers.CharField()
    duration_minutes = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    student_name = serializers.CharField()
    questions = ExamQuestionSerializer(many=True)


class SubmitAnswerSerializer(serializers.Serializer):
    """سریالایزر ثبت پاسخ دانش‌آموز"""

    attempt_id = serializers.IntegerField(required=True)
    question_id = serializers.IntegerField(required=True)
    selected_option_id = serializers.IntegerField(required=True)

    def validate(self, data):
        attempt_id = data.get('attempt_id')
        question_id = data.get('question_id')
        selected_option_id = data.get('selected_option_id')

        # بررسی وجود تلاش
        try:
            attempt = ExamAttempt.objects.get(id=attempt_id, status='in_progress')
        except ExamAttempt.DoesNotExist:
            raise serializers.ValidationError({"attempt_id": "تلاش معتبری یافت نشد"})

        # بررسی وجود سوال
        try:
            question = Question.objects.get(id=question_id, is_active=True)
        except Question.DoesNotExist:
            raise serializers.ValidationError({"question_id": "سوال معتبری یافت نشد"})

        # بررسی وجود گزینه
        try:
            option = QuestionOption.objects.get(id=selected_option_id, question=question)
        except QuestionOption.DoesNotExist:
            raise serializers.ValidationError({"selected_option_id": "گزینه انتخاب شده معتبر نیست"})

        # بررسی عدم ثبت پاسخ قبلی
        if StudentAnswer.objects.filter(attempt=attempt, question=question).exists():
            raise serializers.ValidationError("پاسخ این سوال قبلاً ثبت شده است")

        data['attempt'] = attempt
        data['question'] = question
        data['option'] = option

        return data


class FinishExamResponseSerializer(serializers.Serializer):
    """سریالایزر پاسخ پایان آزمون"""

    score = serializers.IntegerField()
    max_score = serializers.IntegerField()
    percentage = serializers.FloatField()
    correct_answers = serializers.IntegerField()
    wrong_answers = serializers.IntegerField()
    message = serializers.CharField()

    # در صورت فعال بودن گزینه نمایش پاسخ‌نامه
    answer_key = serializers.ListField(child=serializers.DictField(), required=False)

    # در صورت فعال بودن گزینه نمایش نمره
    show_score = serializers.BooleanField(default=True)