from django.contrib import admin
from django.utils.html import format_html
from . import models


# ========== 1. مدیریت پایه تحصیلی ==========
@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'level', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['level', 'is_active']
    search_fields = ['name']


# ========== 2. مدیریت درس ==========
@admin.register(models.Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'grade', 'is_active']
    list_editable = ['is_active']
    list_filter = ['grade', 'is_active']
    search_fields = ['name']


# ========== 3. مدیریت فصل ==========
@admin.register(models.Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'subject', 'grade', 'is_active']
    list_editable = ['is_active']
    list_filter = ['subject', 'grade', 'is_active']
    search_fields = ['name']


# ========== 4. مدیریت معلم ==========
@admin.register(models.Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'mobile', 'is_approved']
    list_editable = ['is_approved']
    search_fields = ['first_name', 'last_name', 'mobile']


# ========== 5. مدیریت سوال (با گزینه‌ها) ==========
class QuestionOptionInline(admin.TabularInline):
    model = models.QuestionOption
    extra = 4
    max_num = 4
    fields = ['text', 'image', 'is_correct', 'order']


@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'short_text', 'teacher', 'subject', 'difficulty', 'estimated_time', 'is_active']
    list_editable = ['is_active']
    list_filter = ['subject', 'difficulty', 'grade', 'is_active']
    search_fields = ['text', 'teacher__first_name', 'teacher__last_name']
    inlines = [QuestionOptionInline]

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    short_text.short_description = 'متن سوال'


# ========== 6. مدیریت گزینه سوال ==========
@admin.register(models.QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'short_text', 'question', 'is_correct', 'order']
    list_editable = ['is_correct', 'order']
    list_filter = ['is_correct']
    search_fields = ['text', 'question__text']

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    short_text.short_description = 'متن گزینه'


# ========== 7. مدیریت دانش‌آموز ==========
@admin.register(models.Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'mobile', 'grade']
    search_fields = ['first_name', 'last_name', 'mobile']


# ========== 8. مدیریت آزمون ==========
@admin.register(models.Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'teacher', 'duration_minutes', 'total_questions_count', 'is_published']
    list_editable = ['is_published']
    list_filter = ['is_published', 'teacher']
    search_fields = ['title', 'teacher__first_name']
    filter_horizontal = ['invited_students']
    readonly_fields = ['created_at']


# ========== 9. مدیریت سوالات انتخابی آزمون ==========
@admin.register(models.ExamQuestionSelection)
class ExamQuestionSelectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'exam', 'student', 'question', 'order']
    list_filter = ['exam']
    search_fields = ['exam__title', 'student__first_name']


# ========== 10. مدیریت تلاش دانش‌آموز ==========
@admin.register(models.ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'exam', 'score', 'total_correct', 'total_questions', 'status', 'start_time']
    list_filter = ['status', 'exam']
    search_fields = ['student__first_name', 'student__last_name', 'exam__title']
    readonly_fields = ['start_time']


# ========== 11. مدیریت پاسخ‌ها ==========
@admin.register(models.StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'attempt', 'question', 'selected_option', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['question__text']


# ========== تنظیمات ظاهری پنل ادمین ==========
admin.site.site_header = 'پنل مدیریت سامانه آزمون'
admin.site.site_title = 'مدیریت سامانه'
admin.site.index_title = 'داشبورد مدیریت'