import random
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db import transaction
from rest_framework_simplejwt.authentication import JWTAuthentication

from ..models import Exam, ExamAttempt, StudentAnswer, Question, Student
from ..serializers import (
    StartExamRequestSerializer,
    SubmitAnswerSerializer,
    ExamAttemptDetailSerializer,
    ExamAttemptListSerializer,
)
from .base import BaseAPIView


class StartExamView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def _select_questions_by_difficulty(self, exam, grade, subject, chapter):
        """انتخاب سوالات بر اساس توزیع درصدی"""
        distribution = exam.get_question_distribution()

        # دریافت سوالات بانک بر اساس پایه، درس، فصل
        questions = Question.objects.filter(
            grade=grade,
            subject=subject,
            chapter=chapter,
            is_active=True
        )

        selected_questions = []

        for difficulty, count in distribution.items():
            if count > 0:
                difficulty_questions = list(questions.filter(difficulty=difficulty))
                if len(difficulty_questions) < count:
                    # اگر به تعداد کافی سوال نبود، از سایر درجات سختی جبران شود
                    other_questions = list(questions.exclude(difficulty=difficulty))
                    needed = count - len(difficulty_questions)
                    selected_questions.extend(difficulty_questions)
                    if needed > 0 and other_questions:
                        selected_questions.extend(random.sample(
                            other_questions,
                            min(needed, len(other_questions))
                        ))
                else:
                    selected_questions.extend(random.sample(difficulty_questions, count))

        # اگر هنوز به تعداد کافی سوال نیست، از همه سوالات پر کن
        if len(selected_questions) < exam.total_questions_count:
            remaining = exam.total_questions_count - len(selected_questions)
            all_questions = list(questions)
            available = [q for q in all_questions if q not in selected_questions]
            if available:
                selected_questions.extend(random.sample(
                    available,
                    min(remaining, len(available))
                ))

        # رندوم کردن ترتیب سوالات در صورت نیاز
        if exam.randomize_questions:
            random.shuffle(selected_questions)

        return selected_questions[:exam.total_questions_count]

    def _shuffle_options(self, question):
        """جابجا کردن گزینه‌ها در صورت نیاز"""
        options = list(question.options.all())
        random.shuffle(options)
        return options

    def post(self, request):
        serializer = StartExamRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return self.error_response(errors=serializer.errors)

        data = serializer.validated_data
        exam_id = data['exam_id']
        mobile = data['mobile']

        # بررسی وجود آزمون
        try:
            exam = Exam.objects.get(id=exam_id, is_published=True)
        except Exam.DoesNotExist:
            return self.error_response(message="آزمون یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # بررسی وجود دانش‌آموز
        try:
            student = Student.objects.get(mobile=mobile)
        except Student.DoesNotExist:
            return self.error_response(message="دانش‌آموزی با این شماره یافت نشد")

        # بررسی دسترسی
        if not exam.invited_students.filter(id=student.id).exists():
            return self.error_response(message="شما به این آزمون دعوت نشده‌اید")

        # بررسی زمان
        now = timezone.now()
        if now < exam.allowed_entry_start:
            return self.error_response(
                message=f"زمان شروع آزمون از {exam.allowed_entry_start.strftime('%H:%M %Y/%m/%d')} می‌باشد")
        if now > exam.allowed_entry_end:
            return self.error_response(message="زمان مجاز شرکت در آزمون به پایان رسیده است")

        # بررسی شرکت قبلی
        existing_attempt = ExamAttempt.objects.filter(
            student=student,
            exam=exam,
            status='completed'
        ).first()

        if existing_attempt:
            return self.error_response(message="شما قبلاً در این آزمون شرکت کرده‌اید")

        # انتخاب سوالات (نیاز به دریافت grade, subject, chapter از جای مناسب)
        # برای سادگی، فرض می‌کنیم آزمون برای یک درس خاص است
        # در نسخه کامل باید از فیلدهای exam استفاده کنید
        grade = student.grade
        subject = exam.teacher.subjects.first()  # نمونه - باید اصلاح شود
        chapter = subject.chapters.first() if subject else None

        if not grade or not subject or not chapter:
            return self.error_response(message="اطلاعات لازم برای ایجاد آزمون موجود نیست")

        selected_questions = self._select_questions_by_difficulty(exam, grade, subject, chapter)

        if not selected_questions:
            return self.error_response(message="هیچ سوالی برای این آزمون یافت نشد")

        # ایجاد تلاش جدید
        attempt = ExamAttempt.objects.create(
            student=student,
            exam=exam,
            total_questions=len(selected_questions),
            status='in_progress'
        )

        # ذخیره سوالات انتخابی و ساخت سوالات با گزینه‌های جابجا شده
        questions_data = []
        for idx, question in enumerate(selected_questions):
            # ذخیره سوال انتخاب شده
            from ..models import ExamQuestionSelection
            ExamQuestionSelection.objects.create(
                exam=exam,
                student=student,
                question=question,
                order=idx + 1
            )

            # آماده‌سازی گزینه‌ها
            options = self._shuffle_options(question) if exam.randomize_options else list(question.options.all())

            questions_data.append({
                'id': question.id,
                'text': question.text,
                'estimated_time': question.estimated_time,
                'image_url': question.image.url if question.image else None,
                'options': [
                    {
                        'id': opt.id,
                        'text': opt.text,
                        'image': opt.image.url if opt.image else None,
                        'order': idx2 + 1
                    }
                    for idx2, opt in enumerate(options)
                ]
            })

        # پاسخ موفق
        response_data = {
            'attempt_id': attempt.id,
            'exam_title': exam.title,
            'duration_minutes': exam.duration_minutes,
            'total_questions': len(selected_questions),
            'student_name': f"{student.first_name} {student.last_name}",
            'questions': questions_data
        }

        return self.success_response(data=response_data, message="آزمون با موفقیت شروع شد")


class GetExamQuestionsView(BaseAPIView):
    """دریافت سوالات آزمون (برای ادامه آزمون)"""
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        try:
            attempt = ExamAttempt.objects.get(id=attempt_id, status='in_progress')
        except ExamAttempt.DoesNotExist:
            return self.error_response(message="تلاش یافت نشد یا به پایان رسیده است")

        # دریافت سوالات انتخابی
        from ..models import ExamQuestionSelection
        selections = ExamQuestionSelection.objects.filter(
            exam=attempt.exam,
            student=attempt.student
        ).order_by('order')

        questions_data = []
        for selection in selections:
            question = selection.question
            options = list(question.options.all())
            if attempt.exam.randomize_options:
                random.shuffle(options)

            questions_data.append({
                'id': question.id,
                'text': question.text,
                'estimated_time': question.estimated_time,
                'image_url': question.image.url if question.image else None,
                'options': [
                    {
                        'id': opt.id,
                        'text': opt.text,
                        'image': opt.image.url if opt.image else None,
                        'order': idx + 1
                    }
                    for idx, opt in enumerate(options)
                ]
            })

        return self.success_response(data={
            'attempt_id': attempt.id,
            'exam_title': attempt.exam.title,
            'duration_minutes': attempt.exam.duration_minutes,
            'total_questions': attempt.total_questions,
            'questions': questions_data
        })


class SubmitAnswerView(BaseAPIView):
    """ثبت پاسخ دانش‌آموز"""
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = SubmitAnswerSerializer(data=request.data)

        if not serializer.is_valid():
            return self.error_response(errors=serializer.errors)

        attempt = serializer.validated_data['attempt']
        question = serializer.validated_data['question']
        option = serializer.validated_data['option']

        # بررسی صحت پاسخ
        is_correct = option.is_correct
        points_earned = 10 if is_correct else 0  # هر سوال ۱۰ نمره

        # ذخیره پاسخ
        student_answer = StudentAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=option,
            is_correct=is_correct
        )

        # بروزرسانی نمره تلاش
        if is_correct:
            attempt.score += points_earned
            attempt.total_correct += 1
            attempt.save()

        # ارسال پاسخ
        response_data = {
            'is_correct': is_correct,
            'points_earned': points_earned,
            'explanation': question.explanation if not is_correct and attempt.exam.show_answer_key_immediately else None
        }

        return self.success_response(
            data=response_data,
            message="پاسخ با موفقیت ثبت شد"
        )


class FinishExamView(BaseAPIView):
    """پایان آزمون و محاسبه نتایج نهایی"""
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, attempt_id):
        try:
            attempt = ExamAttempt.objects.get(id=attempt_id, status='in_progress')
        except ExamAttempt.DoesNotExist:
            return self.error_response(message="تلاش یافت نشد یا قبلاً پایان یافته است")

        # محاسبه نمره نهایی
        answers = StudentAnswer.objects.filter(attempt=attempt)
        total_correct = answers.filter(is_correct=True).count()
        total_score = total_correct * 10
        total_questions = attempt.total_questions
        max_score = total_questions * 10

        # بروزرسانی تلاش
        attempt.score = total_score
        attempt.total_correct = total_correct
        attempt.end_time = timezone.now()
        attempt.status = 'completed'
        attempt.save()

        # آماده‌سازی پاسخ
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        message = "قبول شدید" if percentage >= 60 else "متاسفانه قبول نشدید"

        response_data = {
            'score': total_score,
            'max_score': max_score,
            'percentage': round(percentage, 2),
            'correct_answers': total_correct,
            'wrong_answers': total_questions - total_correct,
            'message': message,
            'show_score': attempt.exam.show_score_immediately
        }

        # اگر نمایش پاسخ‌نامه فعال باشد
        if attempt.exam.show_answer_key_immediately:
            answer_key = []
            for answer in answers.order_by('id'):
                answer_key.append({
                    'question_text': answer.question.text,
                    'selected_option_text': answer.selected_option.text if answer.selected_option else None,
                    'is_correct': answer.is_correct,
                    'correct_option_text': next(
                        (opt.text for opt in answer.question.options.all() if opt.is_correct),
                        None
                    )
                })
            response_data['answer_key'] = answer_key

        return self.success_response(
            data=response_data,
            message="آزمون با موفقیت پایان یافت"
        )


class ExamResultView(BaseAPIView):
    """مشاهده نتایج یک تلاش"""
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        try:
            attempt = ExamAttempt.objects.get(id=attempt_id)
        except ExamAttempt.DoesNotExist:
            return self.error_response(message="نتیجه‌ای یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # بررسی دسترسی
        user = request.user
        if hasattr(user, 'student_profile'):
            if attempt.student != user.student_profile:
                return self.error_response(message="شما به این نتیجه دسترسی ندارید",
                                           status_code=status.HTTP_403_FORBIDDEN)
        elif hasattr(user, 'teacher_profile'):
            if attempt.exam.teacher != user.teacher_profile:
                return self.error_response(message="شما به این نتیجه دسترسی ندارید",
                                           status_code=status.HTTP_403_FORBIDDEN)
        elif not user.is_superuser:
            return self.error_response(message="شما به این نتیجه دسترسی ندارید", status_code=status.HTTP_403_FORBIDDEN)

        serializer = ExamAttemptDetailSerializer(attempt)
        return self.success_response(data=serializer.data)


class StudentExamAttemptsView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]
    serializer_class = ExamAttemptListSerializer


    def get_queryset(self):
        user = self.request.user

        if hasattr(user, 'student_profile'):
            return ExamAttempt.objects.filter(
                student=user.student_profile
            ).order_by('-start_time')

        student_id = self.request.query_params.get('student_id')
        if student_id and user.is_superuser:
            return ExamAttempt.objects.filter(student_id=student_id).order_by('-start_time')

        return ExamAttempt.objects.none()