# lms/views/exam_views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication

from ..models import Exam, Student, StudentAnswer, ExamAttempt
from ..serializers import (
    ExamSerializer,
    ExamListSerializer,
    ExamCreateSerializer,
    ExamUpdateSerializer,
    ExamStudentCheckSerializer,
)
from .base import BaseAPIView


class ExamListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]
    serializer_class = ExamListSerializer


    def get_queryset(self):
        user = self.request.user

        # معلم: آزمون‌های خودش
        if hasattr(user, 'teacher_profile'):
            return Exam.objects.filter(teacher=user.teacher_profile)

        # دانش‌آموز: آزمون‌هایی که به آنها دعوت شده
        if hasattr(user, 'student_profile'):
            return Exam.objects.filter(
                invited_students=user.student_profile,
                is_published=True
            )

        # ادمین: همه آزمون‌ها
        if user.is_superuser:
            return Exam.objects.all()

        return Exam.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ExamCreateView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # فقط معلم مجاز است
        if not hasattr(request.user, 'teacher_profile'):
            return self.error_response(
                message="فقط معلمان می‌توانند آزمون ایجاد کنند",
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = ExamCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            print(f"Serializer errors: {serializer.errors}")
            return self.error_response(
                message="خطای اعتبارسنجی",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        exam = serializer.save()

        # اضافه کردن دانش‌آموزان دعوت شده (فقط دانش‌آموزانی که این معلم اضافه کرده)
        invited_mobiles = request.data.get('invited_students_mobiles', [])
        if invited_mobiles:
            teacher = request.user.teacher_profile
            # فقط دانش‌آموزانی که این معلم اضافه کرده
            students = Student.objects.filter(
                mobile__in=invited_mobiles,
                created_by=teacher
            )

            # بررسی کنیم همه شماره‌ها یافت شده باشند
            found_mobiles = set(students.values_list('mobile', flat=True))
            not_found = set(invited_mobiles) - found_mobiles

            if not_found:
                return self.error_response(
                    message="برخی دانش‌آموزان یافت نشدند یا توسط شما اضافه نشده‌اند",
                    errors={"not_found": list(not_found)},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            exam.invited_students.set(students)
            print(f"Added {students.count()} students to exam")

        response_serializer = ExamSerializer(exam)

        return self.success_response(
            data=response_serializer.data,
            message="آزمون با موفقیت ایجاد شد",
            status_code=status.HTTP_201_CREATED
        )


class ExamDetailView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            return self.error_response(message="آزمون یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # بررسی دسترسی
        user = request.user
        if hasattr(user, 'teacher_profile'):
            if exam.teacher != user.teacher_profile and not user.is_superuser:
                return self.error_response(message="شما به این آزمون دسترسی ندارید",
                                           status_code=status.HTTP_403_FORBIDDEN)
        elif hasattr(user, 'student_profile'):
            if not exam.invited_students.filter(id=user.student_profile.id).exists():
                return self.error_response(message="شما به این آزمون دسترسی ندارید",
                                           status_code=status.HTTP_403_FORBIDDEN)
        elif not user.is_superuser:
            return self.error_response(message="شما به این آزمون دسترسی ندارید", status_code=status.HTTP_403_FORBIDDEN)

        serializer = ExamSerializer(exam)
        return self.success_response(data=serializer.data)


class ExamUpdateView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            return self.error_response(message="آزمون یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # فقط معلم ایجاد کننده می‌تواند ویرایش کند
        if not hasattr(request.user, 'teacher_profile') or exam.teacher != request.user.teacher_profile:
            return self.error_response(message="شما به این آزمون دسترسی ندارید", status_code=status.HTTP_403_FORBIDDEN)

        # اگر آزمون منتشر شده باشد نمی‌توان ویرایش کرد
        if exam.is_published:
            return self.error_response(message="آزمون منتشر شده قابل ویرایش نیست",
                                       status_code=status.HTTP_400_BAD_REQUEST)

        serializer = ExamUpdateSerializer(exam, data=request.data, partial=True)

        if not serializer.is_valid():
            return self.error_response(errors=serializer.errors)

        exam = serializer.save()

        # به‌روزرسانی دانش‌آموزان دعوت شده (اگر در درخواست آمده باشد)
        invited_mobiles = request.data.get('invited_students_mobiles')
        if invited_mobiles is not None:
            teacher = request.user.teacher_profile
            students = Student.objects.filter(
                mobile__in=invited_mobiles,
                created_by=teacher
            )
            exam.invited_students.set(students)

        response_serializer = ExamSerializer(exam)

        return self.success_response(
            data=response_serializer.data,
            message="آزمون با موفقیت بروزرسانی شد"
        )


class ExamDeleteView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            return self.error_response(message="آزمون یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # فقط معلم ایجاد کننده می‌تواند حذف کند
        if not hasattr(request.user, 'teacher_profile') or exam.teacher != request.user.teacher_profile:
            return self.error_response(message="شما به این آزمون دسترسی ندارید", status_code=status.HTTP_403_FORBIDDEN)

        exam.delete()
        return self.success_response(message="آزمون با موفقیت حذف شد")


class ExamPublishView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            return self.error_response(message="آزمون یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # فقط معلم ایجاد کننده می‌تواند منتشر کند
        if not hasattr(request.user, 'teacher_profile') or exam.teacher != request.user.teacher_profile:
            return self.error_response(message="شما به این آزمون دسترسی ندارید", status_code=status.HTTP_403_FORBIDDEN)

        # اعتبارسنجی قبل از انتشار
        if exam.total_questions_count == 0:
            return self.error_response(message="تعداد سوالات آزمون باید بیشتر از صفر باشد")

        if exam.easy_percent + exam.medium_percent + exam.hard_percent != 100:
            return self.error_response(message="مجموع درصدهای سختی باید برابر ۱۰۰ باشد")

        if exam.allowed_entry_start >= exam.allowed_entry_end:
            return self.error_response(message="زمان شروع باید قبل از زمان پایان باشد")

        if exam.invited_students.count() == 0:
            return self.error_response(message="حداقل یک دانش‌آموز باید به آزمون دعوت شود")

        exam.is_published = True
        exam.save()

        return self.success_response(message="آزمون با موفقیت منتشر شد")


class ExamAddStudentsView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            return self.error_response(message="آزمون یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # فقط معلم ایجاد کننده می‌تواند
        if not hasattr(request.user, 'teacher_profile') or exam.teacher != request.user.teacher_profile:
            return self.error_response(message="شما به این آزمون دسترسی ندارید", status_code=status.HTTP_403_FORBIDDEN)

        # اگر آزمون منتشر شده باشد نمی‌توان اضافه کرد
        if exam.is_published:
            return self.error_response(message="آزمون منتشر شده قابل ویرایش نیست",
                                       status_code=status.HTTP_400_BAD_REQUEST)

        mobiles = request.data.get('mobiles', [])
        if not mobiles:
            return self.error_response(message="لیست شماره موبایل دانش‌آموزان را ارسال کنید")

        # فقط دانش‌آموزانی که این معلم اضافه کرده
        teacher = request.user.teacher_profile
        students = Student.objects.filter(
            mobile__in=mobiles,
            created_by=teacher
        )

        found_mobiles = set(students.values_list('mobile', flat=True))
        not_found = set(mobiles) - found_mobiles

        if not_found:
            return self.error_response(
                message="برخی دانش‌آموزان یافت نشدند یا توسط شما اضافه نشده‌اند",
                errors={"not_found": list(not_found)}
            )

        exam.invited_students.add(*students)

        return self.success_response(
            data={"added_count": students.count()},
            message=f"{students.count()} دانش‌آموز به آزمون اضافه شد"
        )


class ExamRemoveStudentView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, student_id):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            return self.error_response(message="آزمون یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # فقط معلم ایجاد کننده می‌تواند
        if not hasattr(request.user, 'teacher_profile') or exam.teacher != request.user.teacher_profile:
            return self.error_response(message="شما به این آزمون دسترسی ندارید", status_code=status.HTTP_403_FORBIDDEN)

        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return self.error_response(message="دانش‌آموز یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        exam.invited_students.remove(student)

        return self.success_response(message="دانش‌آموز با موفقیت از آزمون حذف شد")


class ExamStudentsListView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            return self.error_response(message="آزمون یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # فقط معلم ایجاد کننده می‌تواند ببیند
        if not hasattr(request.user, 'teacher_profile') or exam.teacher != request.user.teacher_profile:
            if not request.user.is_superuser:
                return self.error_response(message="شما به این آزمون دسترسی ندارید",
                                           status_code=status.HTTP_403_FORBIDDEN)

        students = exam.invited_students.all()
        from ..serializers import StudentListSerializer
        serializer = StudentListSerializer(students, many=True)
        return self.success_response(data=serializer.data)


class ExamCheckAccessView(BaseAPIView):
    authentication_classes = [JWTAuthentication]  # اضافه شد
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ExamStudentCheckSerializer(data=request.data)

        if not serializer.is_valid():
            return self.error_response(errors=serializer.errors)

        exam = serializer.validated_data['exam']
        student = serializer.validated_data['student']

        # بررسی می‌کنیم که دانش‌آموز توسط معلم این آزمون اضافه شده باشد
        if student.created_by != exam.teacher:
            return self.error_response(
                message="شما دسترسی لازم برای شرکت در این آزمون را ندارید",
                status_code=status.HTTP_403_FORBIDDEN
            )

        return self.success_response(
            data={
                "can_access": True,
                "exam_id": exam.id,
                "exam_title": exam.title,
                "student_id": student.id,
                "student_name": f"{student.first_name} {student.last_name}"
            },
            message="دسترسی مجاز است"
        )



class ExamResultsView(BaseAPIView):
    """مشاهده نتایج دانش‌آموزان یک آزمون (فقط معلم)"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            return self.error_response(message="آزمون یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # بررسی دسترسی (فقط معلم صاحب آزمون یا ادمین)
        if not hasattr(request.user, 'teacher_profile') or exam.teacher != request.user.teacher_profile:
            if not request.user.is_superuser:
                return self.error_response(message="شما به این آزمون دسترسی ندارید",
                                           status_code=status.HTTP_403_FORBIDDEN)

        # دریافت تمام تلاش‌های دانش‌آموزان این آزمون
        attempts = ExamAttempt.objects.filter(exam=exam).select_related('student').order_by('-score', '-end_time')

        results = []
        for attempt in attempts:
            max_score = attempt.total_questions * 10
            percentage = (attempt.score / max_score * 100) if max_score > 0 else 0

            results.append({
                'attempt_id': attempt.id,
                'student': {
                    'id': attempt.student.id,
                    'name': f"{attempt.student.first_name} {attempt.student.last_name}",
                    'mobile': attempt.student.mobile,
                    'grade': attempt.student.grade.name if attempt.student.grade else None
                },
                'score': attempt.score,
                'max_score': max_score,
                'percentage': round(percentage, 2),
                'correct_count': attempt.total_correct,
                'wrong_count': attempt.total_questions - attempt.total_correct,
                'total_questions': attempt.total_questions,
                'status': attempt.status,
                'start_time': attempt.start_time,
                'end_time': attempt.end_time,
                'passed': percentage >= 60
            })

        # آمار کلی آزمون
        total_students = exam.invited_students.count()
        completed_count = attempts.filter(status='completed').count()
        in_progress_count = attempts.filter(status='in_progress').count()

        if completed_count > 0:
            avg_score = sum(r['score'] for r in results if r['status'] == 'completed') / completed_count
            avg_percentage = sum(r['percentage'] for r in results if r['status'] == 'completed') / completed_count
        else:
            avg_score = 0
            avg_percentage = 0

        stats = {
            'total_students': total_students,
            'completed_count': completed_count,
            'in_progress_count': in_progress_count,
            'not_started_count': total_students - completed_count - in_progress_count,
            'avg_score': round(avg_score, 2),
            'avg_percentage': round(avg_percentage, 2),
            'pass_count': sum(1 for r in results if r['passed'] and r['status'] == 'completed'),
            'fail_count': sum(1 for r in results if not r['passed'] and r['status'] == 'completed')
        }

        exam_data = {
            'id': exam.id,
            'title': exam.title,
            'description': exam.description,
            'duration_minutes': exam.duration_minutes,
            'total_questions': exam.total_questions_count,
            'easy_percent': exam.easy_percent,
            'medium_percent': exam.medium_percent,
            'hard_percent': exam.hard_percent,
            'allowed_entry_start': exam.allowed_entry_start,
            'allowed_entry_end': exam.allowed_entry_end,
            'is_published': exam.is_published
        }

        return self.success_response(data={
            'exam': exam_data,
            'stats': stats,
            'results': results
        })


class ExamStudentResultDetailView(BaseAPIView):
    """مشاهده جزئیات کامل پاسخ‌های یک دانش‌آموز (فقط معلم)"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, exam_id, student_id):
        try:
            exam = Exam.objects.get(pk=exam_id)
        except Exam.DoesNotExist:
            return self.error_response(message="آزمون یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # بررسی دسترسی
        if not hasattr(request.user, 'teacher_profile') or exam.teacher != request.user.teacher_profile:
            if not request.user.is_superuser:
                return self.error_response(message="شما به این آزمون دسترسی ندارید",
                                           status_code=status.HTTP_403_FORBIDDEN)

        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return self.error_response(message="دانش‌آموز یافت نشد", status_code=status.HTTP_404_NOT_FOUND)

        # دریافت تلاش دانش‌آموز
        attempt = ExamAttempt.objects.filter(exam=exam, student=student).first()

        if not attempt:
            return self.error_response(message="این دانش‌آموز هنوز در آزمون شرکت نکرده است",
                                       status_code=status.HTTP_404_NOT_FOUND)

        # دریافت پاسخ‌ها
        answers = StudentAnswer.objects.filter(attempt=attempt).select_related('question', 'selected_option')

        questions_data = []
        for answer in answers:
            correct_option = answer.question.options.filter(is_correct=True).first()
            questions_data.append({
                'id': answer.question.id,
                'text': answer.question.text,
                'difficulty': answer.question.difficulty,
                'selected_option': {
                    'id': answer.selected_option.id if answer.selected_option else None,
                    'text': answer.selected_option.text if answer.selected_option else None,
                    'is_correct': answer.is_correct
                } if answer.selected_option else None,
                'is_correct': answer.is_correct,
                'correct_option': {
                    'id': correct_option.id if correct_option else None,
                    'text': correct_option.text if correct_option else None
                } if correct_option else None,
                'explanation': answer.question.explanation
            })

        max_score = attempt.total_questions * 10
        percentage = (attempt.score / max_score * 100) if max_score > 0 else 0

        return self.success_response(data={
            'student': {
                'id': student.id,
                'name': f"{student.first_name} {student.last_name}",
                'mobile': student.mobile,
                'grade': student.grade.name if student.grade else None
            },
            'attempt': {
                'id': attempt.id,
                'score': attempt.score,
                'max_score': max_score,
                'percentage': round(percentage, 2),
                'correct_count': attempt.total_correct,
                'wrong_count': attempt.total_questions - attempt.total_correct,
                'total_questions': attempt.total_questions,
                'status': attempt.status,
                'start_time': attempt.start_time,
                'end_time': attempt.end_time,
                'passed': percentage >= 60
            },
            'answers': questions_data
        })