# portfolio/models.py
import uuid
from django.db import models
from django.conf import settings


def project_image_path(instance, filename):
    """مسیر ذخیره تصاویر پروژه"""
    return f'portfolio/project_{instance.project.id}/{filename}'


class Project(models.Model):
    """مدل پروژه‌ها / محصولات - نسخه ساده با فیلدهای جداگانه برای هر زبان"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # فیلدهای فارسی
    name_fa = models.CharField(max_length=200, verbose_name="نام پروژه (فارسی)")
    description_fa = models.TextField(verbose_name="توضیح کوتاه (فارسی)")
    long_description_fa = models.TextField(blank=True, null=True, verbose_name="توضیح کامل (فارسی)")

    # فیلدهای انگلیسی
    name_en = models.CharField(max_length=200, verbose_name="Project Name (English)")
    description_en = models.TextField(verbose_name="Short Description (English)")
    long_description_en = models.TextField(blank=True, null=True, verbose_name="Full Description (English)")

    # فیلدهای عمومی
    demo_link = models.URLField(max_length=500, blank=True, null=True, verbose_name="لینک دمو / Demo Link")
    order = models.IntegerField(default=0, verbose_name="ترتیب نمایش")
    is_active = models.BooleanField(default=True, verbose_name="فعال / Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "پروژه"
        verbose_name_plural = "پروژه‌ها"

    def __str__(self):
        return self.name_fa or self.name_en or str(self.id)

    def get_name(self, lang='fa'):
        return self.name_fa if lang == 'fa' else self.name_en

    def get_description(self, lang='fa'):
        return self.description_fa if lang == 'fa' else self.description_en

    def get_long_description(self, lang='fa'):
        desc = self.long_description_fa if lang == 'fa' else self.long_description_en
        return desc or self.get_description(lang)


class ProjectImage(models.Model):
    """مدل تصاویر پروژه"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=project_image_path, verbose_name="تصویر")
    alt_text_fa = models.CharField(max_length=200, blank=True, verbose_name="متن جایگزین (فارسی)")
    alt_text_en = models.CharField(max_length=200, blank=True, verbose_name="Alt Text (English)")
    order = models.IntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        ordering = ['order']
        verbose_name = "تصویر"
        verbose_name_plural = "تصاویر"

    def __str__(self):
        return f"تصویر {self.order} - {self.project.name_fa}"


class ProjectFeature(models.Model):
    """مدل ویژگی‌های پروژه"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='features')
    title_fa = models.CharField(max_length=200, verbose_name="عنوان ویژگی (فارسی)")
    title_en = models.CharField(max_length=200, verbose_name="Feature Title (English)")
    order = models.IntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        ordering = ['order']
        verbose_name = "ویژگی"
        verbose_name_plural = "ویژگی‌ها"

    def __str__(self):
        return self.title_fa or self.title_en

    def get_title(self, lang='fa'):
        return self.title_fa if lang == 'fa' else self.title_en