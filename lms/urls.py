from django.urls import path
from .views import (
    # ویوهای عمومی (پایه‌ها، دروس، فصل‌ها)
    GradeListView,
    SubjectListView,
    ChapterListView,

    # ویوهای معلم
    TeacherRegisterView,
    TeacherProfileView,
    TeacherListView,

    # ویوهای دانش‌آموز
    StudentRegisterView,
    StudentProfileView,
    StudentListView,

    # ویوهای مدیریت سوالات
    QuestionListView,
    QuestionCreateView,
    QuestionDetailView,
    QuestionUpdateView,
    QuestionDeleteView,

    # ویوهای مدیریت آزمون
    ExamListView,
    ExamCreateView,
    ExamDetailView,
    ExamUpdateView,
    ExamDeleteView,
    ExamPublishView,
    ExamAddStudentsView,
    ExamCheckAccessView,

    # ویوهای شرکت در آزمون
    StartExamView,
    GetExamQuestionsView,
    SubmitAnswerView,
    FinishExamView,
    ExamResultView,
    StudentExamAttemptsView,
)
from .views.exam_views import ExamStudentsListView, ExamRemoveStudentView, ExamResultsView, ExamStudentResultDetailView
from .views.quiz_views import StartQuizView, SubmitQuizAnswerView, FinishQuizView, QuizResultView, \
    CheckExamAccessView, StudentDashboardView
from .views.teacher_views import TeacherCheckStatusView, SkillListView

urlpatterns = [
    # ==================== مسیرهای عمومی (بدون احراز هویت) ====================
    # پایه‌های تحصیلی
    path('v1/grades/', GradeListView.as_view(), name='grade-list'),

    # دروس (با فیلتر base_id)
    path('v1/subjects/', SubjectListView.as_view(), name='subject-list'),

    # فصل‌ها (با فیلتر subject_id)
    path('v1/chapters/', ChapterListView.as_view(), name='chapter-list'),

    # بررسی دسترسی دانش‌آموز به آزمون (قبل از شروع)
    path('v1/exam/check-access/', ExamCheckAccessView.as_view(), name='exam-check-access'),

    # شروع آزمون (بدون احراز هویت - با موبایل)
    path('v1/exam/start/', StartExamView.as_view(), name='exam-start'),

    # دریافت سوالات آزمون (برای ادامه)
    path('v1/exam/attempt/<int:attempt_id>/questions/', GetExamQuestionsView.as_view(), name='exam-questions'),

    # ثبت پاسخ
    path('v1/exam/answer/', SubmitAnswerView.as_view(), name='exam-submit-answer'),

    # پایان آزمون
    path('v1/exam/attempt/<int:attempt_id>/finish/', FinishExamView.as_view(), name='exam-finish'),

    # ==================== مسیرهای معلم (نیازمند احراز هویت) ====================

    path('v1/teacher/check-status/', TeacherCheckStatusView.as_view(), name='teacher-check-status'),



    # مسیر مهارت‌ها
    path('v1/skills/', SkillListView.as_view(), name='skill-list'),
    # ثبت‌نام معلم (بدون احراز هویت)
    path('v1/teacher/register/', TeacherRegisterView.as_view(), name='teacher-register'),

    # پروفایل معلم
    path('v1/teacher/profile/', TeacherProfileView.as_view(), name='teacher-profile'),

    # لیست معلمان (فقط ادمین)
    path('v1/teachers/', TeacherListView.as_view(), name='teacher-list'),

    # ==================== مسیرهای دانش‌آموز (نیازمند احراز هویت) ====================
    # ثبت‌نام دانش‌آموز (بدون احراز هویت - برای دعوت)
    path('v1/student/register/', StudentRegisterView.as_view(), name='student-register'),

    # پروفایل دانش‌آموز
    path('v1/student/profile/', StudentProfileView.as_view(), name='student-profile'),

    # لیست دانش‌آموزان (برای معلم)
    path('v1/students/', StudentListView.as_view(), name='student-list'),

    # لیست تلاش‌های دانش‌آموز
    path('v1/student/attempts/', StudentExamAttemptsView.as_view(), name='student-attempts'),

    # مشاهده نتیجه یک تلاش
    path('v1/exam/result/<int:attempt_id>/', ExamResultView.as_view(), name='exam-result'),

    # ==================== مسیرهای مدیریت سوالات (فقط معلم) ====================
    # لیست سوالات (با فیلتر)
    path('v1/questions/', QuestionListView.as_view(), name='question-list'),

    # ایجاد سوال جدید
    path('v1/questions/create/', QuestionCreateView.as_view(), name='question-create'),

    # دریافت، ویرایش و حذف سوال
    path('v1/questions/<int:pk>/', QuestionDetailView.as_view(), name='question-detail'),
    path('v1/questions/<int:pk>/update/', QuestionUpdateView.as_view(), name='question-update'),
    path('v1/questions/<int:pk>/delete/', QuestionDeleteView.as_view(), name='question-delete'),

    # ==================== مسیرهای مدیریت آزمون (فقط معلم) ====================
    # لیست آزمون‌ها
    path('v1/exams/', ExamListView.as_view(), name='exam-list'),

    # ایجاد آزمون جدید
    path('v1/exams/create/', ExamCreateView.as_view(), name='exam-create'),

    # دریافت، ویرایش و حذف آزمون
    path('v1/exams/<int:pk>/', ExamDetailView.as_view(), name='exam-detail'),
    path('v1/exams/<int:pk>/update/', ExamUpdateView.as_view(), name='exam-update'),
    path('v1/exams/<int:pk>/delete/', ExamDeleteView.as_view(), name='exam-delete'),

    # انتشار آزمون
    path('v1/exams/<int:pk>/publish/', ExamPublishView.as_view(), name='exam-publish'),

    # اضافه کردن دانش‌آموز به آزمون
    path('v1/exams/<int:pk>/add-students/', ExamAddStudentsView.as_view(), name='exam-add-students'),
    path('v1/exams/<int:pk>/students/', ExamStudentsListView.as_view(), name='exam-students-list'),
    path('v1/exams/<int:pk>/students/<int:student_id>/', ExamRemoveStudentView.as_view(), name='exam-remove-student'),

    # ==================== مسیرهای دانش‌آموز (Quiz) ====================
    path('v1/quiz/dashboard/', StudentDashboardView.as_view(), name='quiz-dashboard'),
    path('v1/quiz/check/', CheckExamAccessView.as_view(), name='quiz-check'),
    path('v1/quiz/start/', StartQuizView.as_view(), name='quiz-start'),
    path('v1/quiz/answer/', SubmitQuizAnswerView.as_view(), name='quiz-answer'),
    path('v1/quiz/finish/', FinishQuizView.as_view(), name='quiz-finish'),
    path('v1/quiz/result/<int:attempt_id>/', QuizResultView.as_view(), name='quiz-result'),

    path('v1/exams/<int:pk>/results/', ExamResultsView.as_view(), name='exam-results'),
    path('v1/exams/<int:exam_id>/students/<int:student_id>/result/', ExamStudentResultDetailView.as_view(),
         name='exam-student-result'),

]

# ==================== نام‌های مستند برای استفاده در reverse ====================
"""
نام‌های URLها برای استفاده در کد:

عمومی:
- 'grade-list' : لیست پایه‌های تحصیلی
- 'subject-list' : لیست دروس (با فیلتر grade_id)
- 'chapter-list' : لیست فصل‌ها (با فیلتر subject_id)
- 'exam-check-access' : بررسی دسترسی دانش‌آموز به آزمون
- 'exam-start' : شروع آزمون
- 'exam-questions' : دریافت سوالات آزمون
- 'exam-submit-answer' : ثبت پاسخ
- 'exam-finish' : پایان آزمون

معلم:
- 'teacher-register' : ثبت‌نام معلم
- 'teacher-profile' : پروفایل معلم
- 'teacher-list' : لیست معلمان (ادمین)

دانش‌آموز:
- 'student-register' : ثبت‌نام دانش‌آموز
- 'student-profile' : پروفایل دانش‌آموز
- 'student-list' : لیست دانش‌آموزان
- 'student-attempts' : لیست تلاش‌های دانش‌آموز
- 'exam-result' : مشاهده نتیجه یک تلاش

سوالات:
- 'question-list' : لیست سوالات
- 'question-create' : ایجاد سوال جدید
- 'question-detail' : جزئیات سوال
- 'question-update' : ویرایش سوال
- 'question-delete' : حذف سوال

آزمون‌ها:
- 'exam-list' : لیست آزمون‌ها
- 'exam-create' : ایجاد آزمون جدید
- 'exam-detail' : جزئیات آزمون
- 'exam-update' : ویرایش آزمون
- 'exam-delete' : حذف آزمون
- 'exam-publish' : انتشار آزمون
- 'exam-add-students' : اضافه کردن دانش‌آموز به آزمون
"""