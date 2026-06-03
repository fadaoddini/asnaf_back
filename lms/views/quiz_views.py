# lms/views/quiz_views.py - نسخه کامل و درست

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from ..models import Exam, Student, ExamAttempt, StudentAnswer, Question, QuestionOption, ExamQuestionSelection, Grade, \
    Subject
from ..serializers import ExamSerializer
from .base import BaseAPIView
import random


# lms/views/quiz_views.py - اصلاح کامل StudentDashboardView

class StudentDashboardView(BaseAPIView):
    """دریافت اطلاعات دانش‌آموز و تمام آزمون‌ها با دسته‌بندی"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_or_create_student(self, user):
        """دریافت یا ایجاد خودکار Student برای کاربر"""
        if hasattr(user, 'student_profile') and user.student_profile:
            return user.student_profile, False

        try:
            student = Student.objects.get(mobile=user.mobile)
            student.user = user
            student.save()
            return student, False
        except Student.DoesNotExist:
            pass

        student = Student.objects.create(
            user=user,
            first_name=user.first_name or '',
            last_name=user.last_name or '',
            mobile=user.mobile,
            created_by=None
        )
        return student, True

    def get(self, request):
        user = request.user
        student, created = self._get_or_create_student(user)

        if not student:
            return self.error_response(
                message="امکان ایجاد پروفایل دانش‌آموزی وجود ندارد",
                status_code=status.HTTP_403_FORBIDDEN
            )

        now = timezone.now()

        # دریافت تمام آزمون‌هایی که دانش‌آموز به آنها دعوت شده
        all_invited_exams = student.invited_exams.filter(is_published=True)

        # دریافت ID آزمون‌های تکمیل شده با جزئیات نمره
        completed_attempts = ExamAttempt.objects.filter(
            student=student,
            status='completed'
        ).select_related('exam')

        completed_exam_ids = [attempt.exam_id for attempt in completed_attempts]

        # دسته‌بندی آزمون‌ها
        available_exams = []  # آزمون‌های قابل شرکت (زمانش رسیده و کامل نشده)
        waiting_exams = []  # آزمون‌هایی که هنوز شروع نشده
        expired_exams = []  # آزمون‌هایی که زمانشان تمام شده
        completed_exams_data = []  # آزمون‌هایی که تکمیل شده با نمره

        for exam in all_invited_exams:
            exam_data = {
                'id': exam.id,
                'title': exam.title,
                'description': exam.description,
                'duration_minutes': exam.duration_minutes,
                'total_questions_count': exam.total_questions_count,
                'allowed_entry_start': exam.allowed_entry_start,
                'allowed_entry_end': exam.allowed_entry_end,
                'created_at': exam.created_at,
            }

            # بررسی تکمیل شده
            if exam.id in completed_exam_ids:
                attempt = next((a for a in completed_attempts if a.exam_id == exam.id), None)
                if attempt:
                    max_score = attempt.total_questions * 10
                    percentage = (attempt.score / max_score * 100) if max_score > 0 else 0
                    completed_exams_data.append({
                        **exam_data,
                        'attempt_id': attempt.id,
                        'score': attempt.score,
                        'max_score': max_score,
                        'percentage': round(percentage, 2),
                        'correct_count': attempt.total_correct,
                        'wrong_count': attempt.total_questions - attempt.total_correct,
                        'completed_at': attempt.end_time
                    })
            # بررسی زمان
            elif now < exam.allowed_entry_start:
                waiting_exams.append(exam_data)
            elif now > exam.allowed_entry_end:
                expired_exams.append(exam_data)
            else:
                available_exams.append(exam_data)

        # سریالایزر برای آزمون‌های فعال
        serializer = ExamSerializer(available_exams, many=True)

        return self.success_response(
            data={
                "student": {
                    "id": student.id,
                    "name": f"{student.first_name} {student.last_name}",
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "mobile": student.mobile,
                },
                "available_exams": serializer.data,
                "waiting_exams": waiting_exams,
                "expired_exams": expired_exams,
                "completed_exams": completed_exams_data,
                # آمار کلی
                "stats": {
                    "total": all_invited_exams.count(),
                    "available": len(available_exams),
                    "waiting": len(waiting_exams),
                    "expired": len(expired_exams),
                    "completed": len(completed_exams_data)
                }
            },
            message="اطلاعات با موفقیت دریافت شد"
        )


class CheckExamAccessView(BaseAPIView):
    """بررسی دسترسی به آزمون قبل از شروع"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        exam_id = request.data.get('exam_id')

        if not exam_id:
            return self.error_response(message="شناسه آزمون وارد نشده است")

        user = request.user
        if not hasattr(user, 'student_profile'):
            return self.error_response(
                message="شما دسترسی لازم را ندارید",
                status_code=status.HTTP_403_FORBIDDEN
            )

        student = user.student_profile

        try:
            exam = Exam.objects.get(id=exam_id, is_published=True)
        except Exam.DoesNotExist:
            return self.error_response(message="آزمون یافت نشد")

        if not exam.invited_students.filter(id=student.id).exists():
            return self.error_response(
                message="شما به این آزمون دعوت نشده‌اید",
                status_code=status.HTTP_403_FORBIDDEN
            )

        now = timezone.now()
        if now < exam.allowed_entry_start:
            return self.error_response(
                message=f"زمان شروع آزمون از {exam.allowed_entry_start.strftime('%Y/%m/%d %H:%M')} می‌باشد",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if now > exam.allowed_entry_end:
            return self.error_response(
                message="زمان مجاز شرکت در آزمون به پایان رسیده است",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        existing_attempt = ExamAttempt.objects.filter(
            student=student,
            exam=exam,
            status='completed'
        ).first()

        if existing_attempt:
            return self.error_response(
                message="شما قبلاً در این آزمون شرکت کرده‌اید",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.success_response(
            data={
                "can_start": True,
                "exam_id": exam.id,
                "exam_title": exam.title,
                "duration_minutes": exam.duration_minutes,
                "total_questions": exam.total_questions_count
            },
            message="امکان شروع آزمون وجود دارد"
        )


class StartQuizView(BaseAPIView):
    """شروع آزمون توسط دانش‌آموز"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_lock_key(self, student_id, exam_id):
        return f"exam_start_lock_{student_id}_{exam_id}"

    def _select_questions(self, exam, student):
        """انتخاب سوالات بر اساس شرایط آزمون"""
        print(f"\n=== Selecting Questions ===")
        print(f"Exam Grade: {exam.grade_id}, Subject: {exam.subject_id}, Chapter: {exam.chapter_id}")
        print(f"Student Grade: {student.grade_id}")

        # ساخت query پایه - سوالات معلم که فعال هستند
        questions = Question.objects.filter(
            teacher=exam.teacher,
            is_active=True
        )

        print(f"Total teacher questions: {questions.count()}")

        # فیلتر بر اساس پایه (از exam یا student)
        target_grade = exam.grade or student.grade
        if target_grade:
            questions = questions.filter(grade=target_grade)
            print(f"After grade filter ({target_grade.name}): {questions.count()}")

        # فیلتر بر اساس درس (از exam)
        if exam.subject:
            questions = questions.filter(subject=exam.subject)
            print(f"After subject filter ({exam.subject.name}): {questions.count()}")

        # فیلتر بر اساس فصل (اگر انتخاب شده باشد)
        if exam.chapter:
            questions = questions.filter(chapter=exam.chapter)
            print(f"After chapter filter ({exam.chapter.name}): {questions.count()}")

        if questions.count() == 0:
            print("No questions found!")
            return []

        # دریافت توزیع سوالات
        distribution = exam.get_question_distribution()
        print(
            f"Distribution: easy={distribution['easy']}, medium={distribution['medium']}, hard={distribution['hard']}")

        selected_questions = []
        used_ids = set()

        # انتخاب سوالات بر اساس درجه سختی
        for difficulty, needed in distribution.items():
            if needed <= 0:
                continue

            available = list(questions.filter(difficulty=difficulty).exclude(id__in=used_ids))
            print(f"{difficulty}: available={len(available)}, needed={needed}")

            if len(available) >= needed:
                selected = random.sample(available, needed)
                selected_questions.extend(selected)
                used_ids.update([q.id for q in selected])
            else:
                selected_questions.extend(available)
                used_ids.update([q.id for q in available])

        # اگر به تعداد کافی سوال نداریم، از بقیه سوالات پر کن
        if len(selected_questions) < exam.total_questions_count:
            remaining = exam.total_questions_count - len(selected_questions)
            other_questions = list(questions.exclude(id__in=used_ids))
            if other_questions:
                extra = random.sample(other_questions, min(remaining, len(other_questions)))
                selected_questions.extend(extra)
                print(f"Added {len(extra)} extra questions from other difficulties")

        # رندوم کردن ترتیب
        if exam.randomize_questions:
            random.shuffle(selected_questions)

        final = selected_questions[:exam.total_questions_count]
        print(f"Final selected: {len(final)} questions")

        return final

    @transaction.atomic
    def post(self, request):
        exam_id = request.data.get('exam_id')

        print(f"\n=== StartQuizView POST ===")
        print(f"Exam ID: {exam_id}")
        print(f"User: {request.user.id} - {request.user.mobile}")

        if not exam_id:
            return self.error_response(message="شناسه آزمون وارد نشده است")

        user = request.user

        if not hasattr(user, 'student_profile'):
            return self.error_response(
                message="این بخش فقط برای دانش‌آموزان است",
                status_code=status.HTTP_403_FORBIDDEN
            )

        student = user.student_profile

        # قفل برای جلوگیری از درخواست همزمان
        lock_key = self._get_lock_key(student.id, exam_id)
        if cache.get(lock_key):
            print("Another request is processing, waiting...")
            import time
            time.sleep(1)
            existing = ExamAttempt.objects.filter(
                student=student, exam_id=exam_id, status='in_progress'
            ).first()
            if existing:
                return self._continue_exam(existing)

        cache.set(lock_key, True, timeout=10)

        try:
            # پیدا کردن آزمون
            try:
                exam = Exam.objects.get(id=exam_id, is_published=True)
            except Exam.DoesNotExist:
                return self.error_response(message="آزمون یافت نشد")

            # بررسی دعوت شدن
            if not exam.invited_students.filter(id=student.id).exists():
                return self.error_response(message="شما به این آزمون دعوت نشده‌اید")

            # بررسی زمان
            now = timezone.now()
            if now < exam.allowed_entry_start:
                return self.error_response(message="زمان شروع آزمون فرا نرسیده است")
            if now > exam.allowed_entry_end:
                return self.error_response(message="زمان مجاز شرکت در آزمون به پایان رسیده است")

            # بررسی تکمیل شده
            if ExamAttempt.objects.filter(student=student, exam=exam, status='completed').exists():
                return self.error_response(message="شما قبلاً در این آزمون شرکت کرده‌اید")

            # بررسی در حال انجام
            in_progress = ExamAttempt.objects.filter(
                student=student, exam=exam, status='in_progress'
            ).first()

            if in_progress:
                return self._continue_exam(in_progress)

            # انتخاب سوالات
            selected_questions = self._select_questions(exam, student)

            if len(selected_questions) < exam.total_questions_count:
                return self.error_response(
                    message=f"تعداد سوالات موجود ({len(selected_questions)}) کمتر از تعداد مورد نیاز ({exam.total_questions_count}) است",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # ایجاد تلاش جدید
            attempt = ExamAttempt.objects.create(
                student=student,
                exam=exam,
                total_questions=len(selected_questions),
                status='in_progress'
            )

            # ذخیره سوالات
            for idx, q in enumerate(selected_questions):
                ExamQuestionSelection.objects.create(
                    exam=exam,
                    student=student,
                    question=q,
                    order=idx + 1
                )

            # آماده‌سازی پاسخ
            questions_data = []
            for q in selected_questions:
                options = list(q.options.all())
                if exam.randomize_options:
                    random.shuffle(options)

                questions_data.append({
                    'id': q.id,
                    'text': q.text,
                    'estimated_time': q.estimated_time,
                    'image_url': q.image.url if q.image else None,
                    'options': [
                        {
                            'id': opt.id,
                            'text': opt.text,
                            'image_url': opt.image.url if opt.image else None,
                            'order': idx + 1
                        }
                        for idx, opt in enumerate(options)
                    ]
                })

            return self.success_response(
                data={
                    'attempt_id': attempt.id,
                    'exam_title': exam.title,
                    'duration_minutes': exam.duration_minutes,
                    'total_questions': len(selected_questions),
                    'questions': questions_data
                },
                message="آزمون شروع شد"
            )

        finally:
            cache.delete(lock_key)

    def _continue_exam(self, attempt):
        """ادامه آزمون نیمه‌کاره"""
        print(f"\n=== Continuing exam attempt {attempt.id} ===")

        exam = attempt.exam
        student = attempt.student

        selections = ExamQuestionSelection.objects.filter(
            exam=exam,
            student=student
        ).order_by('order')

        # پیدا کردن سوالات پاسخ داده شده
        answered_q_ids = StudentAnswer.objects.filter(
            attempt=attempt
        ).values_list('question_id', flat=True)

        questions_data = []
        for selection in selections:
            q = selection.question
            is_answered = q.id in answered_q_ids

            options = list(q.options.all())
            if exam.randomize_options and not is_answered:
                random.shuffle(options)

            questions_data.append({
                'id': q.id,
                'text': q.text,
                'estimated_time': q.estimated_time,
                'image_url': q.image.url if q.image else None,
                'is_answered': is_answered,
                'options': [
                    {
                        'id': opt.id,
                        'text': opt.text,
                        'image_url': opt.image.url if opt.image else None,
                        'order': idx + 1
                    }
                    for idx, opt in enumerate(options)
                ]
            })

        return self.success_response(
            data={
                'attempt_id': attempt.id,
                'exam_title': exam.title,
                'duration_minutes': exam.duration_minutes,
                'total_questions': attempt.total_questions,
                'questions': questions_data
            },
            message="ادامه آزمون"
        )


class SubmitQuizAnswerView(BaseAPIView):
    """ثبت پاسخ دانش‌آموز"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        attempt_id = request.data.get('attempt_id')
        question_id = request.data.get('question_id')
        option_id = request.data.get('option_id')

        if not all([attempt_id, question_id, option_id]):
            return self.error_response(message="اطلاعات ناقص است")

        user = request.user
        if not hasattr(user, 'student_profile'):
            return self.error_response(message="شما دسترسی لازم را ندارید")

        student = user.student_profile

        try:
            attempt = ExamAttempt.objects.get(id=attempt_id, student=student, status='in_progress')
            question = Question.objects.get(id=question_id)
            option = QuestionOption.objects.get(id=option_id, question=question)
        except (ExamAttempt.DoesNotExist, Question.DoesNotExist, QuestionOption.DoesNotExist):
            return self.error_response(message="اطلاعات نامعتبر")

        if StudentAnswer.objects.filter(attempt=attempt, question=question).exists():
            return self.error_response(message="پاسخ این سوال قبلاً ثبت شده است")

        is_correct = option.is_correct
        points_earned = 10 if is_correct else 0

        StudentAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=option,
            is_correct=is_correct
        )

        if is_correct:
            attempt.score += points_earned
            attempt.total_correct += 1
            attempt.save()

        return self.success_response(
            data={
                'is_correct': is_correct,
                'points_earned': points_earned,
                'explanation': question.explanation if attempt.exam.show_answer_key_immediately else None
            },
            message="پاسخ ثبت شد"
        )


class FinishQuizView(BaseAPIView):
    """پایان آزمون"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        attempt_id = request.data.get('attempt_id')

        if not attempt_id:
            return self.error_response(message="شناسه تلاش وارد نشده است")

        user = request.user
        if not hasattr(user, 'student_profile'):
            return self.error_response(message="شما دسترسی لازم را ندارید")

        student = user.student_profile

        try:
            attempt = ExamAttempt.objects.get(id=attempt_id, student=student, status='in_progress')
        except ExamAttempt.DoesNotExist:
            return self.error_response(message="تلاش یافت نشد یا قبلاً پایان یافته است")

        attempt.end_time = timezone.now()
        attempt.status = 'completed'
        attempt.save()

        max_score = attempt.total_questions * 10
        percentage = (attempt.score / max_score * 100) if max_score > 0 else 0
        passed = percentage >= 60

        return self.success_response(
            data={
                'attempt_id': attempt.id,
                'score': attempt.score,
                'max_score': max_score,
                'percentage': round(percentage, 2),
                'correct_count': attempt.total_correct,
                'wrong_count': attempt.total_questions - attempt.total_correct,
                'passed': passed,
                'message': "تبریک! قبول شدید" if passed else "متاسفانه قبول نشدید"
            },
            message="آزمون با موفقیت پایان یافت"
        )


class QuizResultView(BaseAPIView):
    """مشاهده نتیجه آزمون"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        user = request.user
        if not hasattr(user, 'student_profile'):
            return self.error_response(message="شما دسترسی لازم را ندارید")

        student = user.student_profile

        try:
            attempt = ExamAttempt.objects.get(id=attempt_id, student=student)
        except ExamAttempt.DoesNotExist:
            return self.error_response(message="نتیجه‌ای یافت نشد")

        answers = StudentAnswer.objects.filter(attempt=attempt).select_related('question', 'selected_option')

        questions_data = []
        for answer in answers:
            correct_option = answer.question.options.filter(is_correct=True).first()
            questions_data.append({
                'question_text': answer.question.text,
                'selected_option_text': answer.selected_option.text if answer.selected_option else None,
                'is_correct': answer.is_correct,
                'correct_option_text': correct_option.text if correct_option else None,
                'explanation': answer.question.explanation
            })

        max_score = attempt.total_questions * 10
        percentage = (attempt.score / max_score * 100) if max_score > 0 else 0

        return self.success_response(
            data={
                'exam_title': attempt.exam.title,
                'score': attempt.score,
                'max_score': max_score,
                'percentage': round(percentage, 2),
                'correct_count': attempt.total_correct,
                'wrong_count': attempt.total_questions - attempt.total_correct,
                'start_time': attempt.start_time,
                'end_time': attempt.end_time,
                'answers': questions_data,
                'show_correct_answers': attempt.exam.show_answer_key_immediately
            },
            message="نتیجه آزمون"
        )