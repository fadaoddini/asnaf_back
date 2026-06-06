# portfolio/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Project, ProjectImage, ProjectFeature


class ProjectImageInline(admin.TabularInline):
    """مدیریت تصاویر به صورت جدول ساده"""
    model = ProjectImage
    extra = 3
    fields = ['image', 'alt_text_fa', 'alt_text_en', 'order']
    classes = ['collapse']


class ProjectFeatureInline(admin.TabularInline):
    """مدیریت ویژگی‌ها به صورت جدول ساده"""
    model = ProjectFeature
    extra = 4
    fields = ['title_fa', 'title_en', 'order']
    classes = ['collapse']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """ادمین پروژه - ساده و کاربردی"""

    # فیلدهای نمایش در لیست پروژه‌ها
    list_display = [
        'thumbnail_preview',
        'name_fa',
        'name_en',
        'order',
        'is_active',  # استفاده از خود فیلد is_active
        'images_count',
        'created_at'
    ]

    # فیلترها
    list_filter = ['is_active', 'created_at']

    # فیلدهای قابل جستجو
    search_fields = ['name_fa', 'name_en', 'description_fa', 'description_en']

    # فیلدهای قابل ویرایش مستقیم در لیست (فقط فیلدهای واقعی مدل)
    list_editable = ['order', 'is_active']  # حذف is_active_status

    # لینک‌های مستقیم
    list_display_links = ['thumbnail_preview', 'name_fa', 'name_en']

    # مرتب‌سازی پیش‌فرض
    ordering = ['order', '-created_at']

    # گروه‌بندی فیلدها در صفحه ویرایش
    fieldsets = (
        ('اطلاعات اصلی / Main Information', {
            'fields': ('is_active', 'order')
        }),
        ('فارسی / Persian', {
            'fields': ('name_fa', 'description_fa', 'long_description_fa'),
            'classes': ('wide',),
        }),
        ('English', {
            'fields': ('name_en', 'description_en', 'long_description_en'),
            'classes': ('wide',),
        }),
        ('لینک / Links', {
            'fields': ('demo_link',),
            'classes': ('collapse',),
        }),
    )

    # درج تصاویر و ویژگی‌ها در صفحه ویرایش
    inlines = [ProjectImageInline, ProjectFeatureInline]

    def thumbnail_preview(self, obj):
        """نمایش تصویر بند‌انگشتی در لیست"""
        first_image = obj.images.first()
        if first_image and first_image.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 8px; object-fit: cover;" />',
                first_image.image.url
            )
        return format_html('<span style="color: gray;">📷 بدون تصویر</span>')

    thumbnail_preview.short_description = 'تصویر'

    def images_count(self, obj):
        """تعداد تصاویر پروژه"""
        count = obj.images.count()
        return format_html('<span style="font-size: 12px;">📷 {}</span>', count)

    images_count.short_description = 'تعداد تصاویر'

    # اکشن‌های سفارشی
    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} پروژه فعال شدند.")

    make_active.short_description = "فعال کردن پروژه‌های انتخاب شده"

    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} پروژه غیرفعال شدند.")

    make_inactive.short_description = "غیرفعال کردن پروژه‌های انتخاب شده"

    # ذخیره خودکار ترتیب
    def save_model(self, request, obj, form, change):
        if not obj.order:
            last_order = Project.objects.filter(is_active=True).order_by('-order').first()
            obj.order = (last_order.order + 1) if last_order else 1
        super().save_model(request, obj, form, change)


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'project_link', 'image_preview', 'order']
    list_filter = ['project']
    list_editable = ['order']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="60" height="60" style="border-radius: 8px; object-fit: cover;" />',
                obj.image.url
            )
        return '-'

    image_preview.short_description = 'پیش‌نمایش'

    def project_link(self, obj):
        url = reverse('admin:portfolio_project_change', args=[obj.project.id])
        return format_html('<a href="{}">{}</a>', url, obj.project.name_fa)

    project_link.short_description = 'پروژه'


@admin.register(ProjectFeature)
class ProjectFeatureAdmin(admin.ModelAdmin):
    list_display = ['id', 'project_link', 'title_fa', 'title_en', 'order']
    list_filter = ['project']
    list_editable = ['order']

    def project_link(self, obj):
        url = reverse('admin:portfolio_project_change', args=[obj.project.id])
        return format_html('<a href="{}">{}</a>', url, obj.project.name_fa)

    project_link.short_description = 'پروژه'