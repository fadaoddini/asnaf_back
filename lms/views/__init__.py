# lms/views/__init__.py

from .base import BaseAPIView
from .common_views import (
    GradeListView,
    SubjectListView,
    ChapterListView,
)
from .teacher_views import (
    TeacherRegisterView,
    TeacherProfileView,
    TeacherListView,
)
from .student_views import (
    StudentRegisterView,
    StudentProfileView,
    StudentListView,
    StudentDetailView,
    StudentDeleteView,
    StudentByMobileView,
)
from .question_views import (
    QuestionListView,
    QuestionCreateView,
    QuestionDetailView,
    QuestionUpdateView,
    QuestionDeleteView,
)
from .exam_views import (
    ExamListView,
    ExamCreateView,
    ExamDetailView,
    ExamUpdateView,
    ExamDeleteView,
    ExamPublishView,
    ExamAddStudentsView,
    ExamCheckAccessView,
)
from .exam_attempt_views import (
    StartExamView,
    GetExamQuestionsView,
    SubmitAnswerView,
    FinishExamView,
    ExamResultView,
    StudentExamAttemptsView,
)

__all__ = [
    # Base
    'BaseAPIView',

    # Common
    'GradeListView',
    'SubjectListView',
    'ChapterListView',

    # Teacher
    'TeacherRegisterView',
    'TeacherProfileView',
    'TeacherListView',

    # Student
    'StudentRegisterView',
    'StudentProfileView',
    'StudentListView',
    'StudentDetailView',
    'StudentDeleteView',
    'StudentByMobileView',

    # Question
    'QuestionListView',
    'QuestionCreateView',
    'QuestionDetailView',
    'QuestionUpdateView',
    'QuestionDeleteView',

    # Exam
    'ExamListView',
    'ExamCreateView',
    'ExamDetailView',
    'ExamUpdateView',
    'ExamDeleteView',
    'ExamPublishView',
    'ExamAddStudentsView',
    'ExamCheckAccessView',

    # Exam Attempt
    'StartExamView',
    'GetExamQuestionsView',
    'SubmitAnswerView',
    'FinishExamView',
    'ExamResultView',
    'StudentExamAttemptsView',
]