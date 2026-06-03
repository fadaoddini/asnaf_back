# lms/serializers/question_serializers.py
from rest_framework import serializers
from ..models import Question, QuestionOption, Grade, Subject, Chapter


class QuestionOptionSerializer(serializers.ModelSerializer):
    """سریالایزر گزینه‌های سوال"""

    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = QuestionOption
        fields = ['id', 'text', 'image', 'image_url', 'is_correct', 'order']
        extra_kwargs = {
            'text': {'required': False, 'allow_blank': True, 'allow_null': True},
            'image': {'required': False},
        }

    def get_image_url(self, obj):
        if obj.image and obj.image.name:
            try:
                return obj.image.url
            except:
                return None
        return None


class QuestionSerializer(serializers.ModelSerializer):
    """سریالایزر کامل سوال"""

    options = QuestionOptionSerializer(many=True, read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    grade_name = serializers.CharField(source='grade.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    chapter_name = serializers.CharField(source='chapter.name', read_only=True, allow_null=True)
    teacher_name = serializers.SerializerMethodField(read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'text', 'grade', 'grade_name', 'subject', 'subject_name',
            'chapter', 'chapter_name', 'difficulty', 'difficulty_display',
            'estimated_time', 'image', 'image_url', 'explanation',
            'options', 'teacher', 'teacher_name', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'teacher', 'created_at']

    def get_teacher_name(self, obj):
        if obj.teacher:
            return f"{obj.teacher.first_name} {obj.teacher.last_name}"
        return ''

    def get_image_url(self, obj):
        if obj.image and obj.image.name:
            try:
                return obj.image.url
            except:
                return None
        return None


class QuestionListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست سوالات - برای نمایش در لیست"""

    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    grade_name = serializers.CharField(source='grade.name', read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'text', 'subject', 'subject_name', 'grade', 'grade_name',
            'difficulty', 'difficulty_display', 'estimated_time',
            'is_active', 'created_at'
        ]


class QuestionCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد سوال جدید"""

    options = serializers.CharField(write_only=True)  # دریافت به صورت JSON string
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Question
        fields = [
            'text', 'grade', 'subject', 'chapter', 'difficulty',
            'estimated_time', 'image', 'explanation', 'options'
        ]

    def validate_chapter(self, value):
        """فصل می‌تواند null باشد"""
        return value

    def validate_options(self, value):
        """اعتبارسنجی گزینه‌ها - JSON string را parse می‌کند"""
        import json

        # اگر string است، parse کن
        if isinstance(value, str):
            try:
                options_data = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("فرمت گزینه‌ها صحیح نیست")
        else:
            options_data = value

        # بررسی تعداد گزینه‌ها
        if len(options_data) != 4:
            raise serializers.ValidationError("سوال باید دقیقاً ۴ گزینه داشته باشد")

        # بررسی وجود گزینه صحیح
        correct_options = [opt for opt in options_data if opt.get('is_correct')]
        if len(correct_options) != 1:
            raise serializers.ValidationError("سوال باید دقیقاً یک گزینه صحیح داشته باشد")

        # بررسی هر گزینه
        for idx, opt in enumerate(options_data):
            text = opt.get('text', '')
            if not text and not opt.get('image'):
                raise serializers.ValidationError(
                    f"گزینه {chr(65 + idx)}: حداقل باید متن یا تصویر داشته باشد"
                )

        return options_data

    def validate_estimated_time(self, value):
        if value < 10:
            raise serializers.ValidationError("زمان تخمینی پاسخ حداقل ۱۰ ثانیه باشد")
        if value > 300:
            raise serializers.ValidationError("زمان تخمینی پاسخ حداکثر ۳۰۰ ثانیه باشد")
        return value

    def create(self, validated_data):
        options_data = validated_data.pop('options')
        teacher = self.context['request'].user.teacher_profile

        image = validated_data.pop('image', None)

        question = Question.objects.create(teacher=teacher, **validated_data)

        if image:
            question.image = image
            question.save()

        for idx, opt_data in enumerate(options_data):
            QuestionOption.objects.create(
                question=question,
                text=opt_data.get('text', ''),
                order=idx + 1,
                is_correct=opt_data.get('is_correct', False)
            )

        return question


class QuestionUpdateSerializer(serializers.ModelSerializer):
    """سریالایزر بروزرسانی سوال"""

    options = serializers.CharField(write_only=True, required=False)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Question
        fields = [
            'text', 'grade', 'subject', 'chapter', 'difficulty',
            'estimated_time', 'image', 'explanation', 'options', 'is_active'
        ]

    def validate_chapter(self, value):
        return value

    def validate_options(self, value):
        import json

        if value:
            if isinstance(value, str):
                try:
                    options_data = json.loads(value)
                except json.JSONDecodeError:
                    raise serializers.ValidationError("فرمت گزینه‌ها صحیح نیست")
            else:
                options_data = value

            if len(options_data) != 4:
                raise serializers.ValidationError("سوال باید دقیقاً ۴ گزینه داشته باشد")

            correct_options = [opt for opt in options_data if opt.get('is_correct')]
            if len(correct_options) != 1:
                raise serializers.ValidationError("سوال باید دقیقاً یک گزینه صحیح داشته باشد")

            return options_data
        return None

    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)
        image = validated_data.pop('image', None)

        # بروزرسانی فیلدها
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if image is not None:
            instance.image = image

        instance.save()

        # بروزرسانی گزینه‌ها
        if options_data is not None:
            instance.options.all().delete()
            for idx, opt_data in enumerate(options_data):
                QuestionOption.objects.create(
                    question=instance,
                    text=opt_data.get('text', ''),
                    order=idx + 1,
                    is_correct=opt_data.get('is_correct', False)
                )

        return instance