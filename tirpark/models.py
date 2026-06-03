# tirpark/models.py
from django.db import models
from django.utils import timezone
import json
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomsProcedure(models.Model):
    """
    مدل رویه‌های گمرکی
    """
    code = models.IntegerField(primary_key=True, verbose_name='کد رویه')
    name = models.CharField(max_length=50, unique=True, verbose_name='نام رویه')
    title = models.CharField(max_length=100, verbose_name='عنوان رویه')
    description = models.TextField(null=True, blank=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        db_table = 'tirpark_customs_procedures'
        verbose_name = 'رویه گمرکی'
        verbose_name_plural = 'رویه‌های گمرکی'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.title}"


class LoadType(models.Model):
    """
    مدل انواع بار
    """
    load_id = models.CharField(max_length=50, primary_key=True, verbose_name='شناسه بار')
    title = models.CharField(max_length=200, verbose_name='عنوان بار')
    category = models.CharField(max_length=100, null=True, blank=True, verbose_name='دسته‌بندی')

    class Meta:
        db_table = 'tirpark_load_types'
        verbose_name = 'نوع بار'
        verbose_name_plural = 'انواع بار'

    def __str__(self):
        return self.title


class TruckPlate(models.Model):
    """
    مدل پلاک خودرو (جداسازی شده)
    """
    location_section = models.CharField(max_length=10, verbose_name='بخش مکانی')
    serial_section = models.CharField(max_length=20, verbose_name='سریال')
    letter_section = models.CharField(max_length=5, verbose_name='حرف')
    code_section = models.CharField(max_length=10, verbose_name='کد')
    full_plate = models.CharField(max_length=50, unique=True, verbose_name='پلاک کامل')

    class Meta:
        db_table = 'tirpark_truck_plates'
        verbose_name = 'پلاک خودرو'
        verbose_name_plural = 'پلاک‌های خودرو'
        indexes = [
            models.Index(fields=['full_plate']),
            models.Index(fields=['location_section', 'serial_section']),
        ]

    def __str__(self):
        return self.full_plate

    @classmethod
    def create_from_json(cls, plate_json):
        """ایجاد یا دریافت پلاک از JSON"""
        if not plate_json:
            return None

        try:
            plate_data = json.loads(plate_json)
            location = plate_data.get('location_section', '')
            serial = plate_data.get('serial_section', '')
            letter = plate_data.get('letter_section', '')
            code = plate_data.get('code_section', '')
            full_plate = f"{location} {serial} {letter} {code}".strip()

            obj, created = cls.objects.get_or_create(
                full_plate=full_plate,
                defaults={
                    'location_section': location,
                    'serial_section': serial,
                    'letter_section': letter,
                    'code_section': code
                }
            )
            return obj
        except:
            return None


class Driver(models.Model):
    """
    مدل راننده
    """
    full_name = models.CharField(max_length=200, db_index=True, verbose_name='نام کامل')
    national_code = models.CharField(max_length=10, null=True, blank=True, verbose_name='کد ملی')
    mobile = models.CharField(max_length=11, null=True, blank=True, verbose_name='شماره موبایل')
    first_seen = models.DateTimeField(auto_now_add=True, verbose_name='اولین مشاهده')
    last_seen = models.DateTimeField(auto_now=True, verbose_name='آخرین مشاهده')

    class Meta:
        db_table = 'tirpark_drivers'
        verbose_name = 'راننده'
        verbose_name_plural = 'رانندگان'
        indexes = [
            models.Index(fields=['full_name']),
        ]

    def __str__(self):
        return self.full_name


class ParkingQueue(models.Model):
    """
    مدل اصلی صف پارکینگ
    """

    STATUS_CHOICES = [
        ('in', 'در پارکینگ'),
        ('out', 'خارج شده'),
        ('waiting', 'در انتظار'),
        ('processing', 'در حال بررسی'),
    ]

    # اطلاعات پایه
    id = models.BigIntegerField(primary_key=True, verbose_name='شناسه')
    receipt_number = models.CharField(max_length=100, db_index=True, verbose_name='شماره رسید')

    # روابط خارجی
    customs_procedure = models.ForeignKey(
        CustomsProcedure,
        on_delete=models.PROTECT,
        related_name='parking_queues',
        verbose_name='رویه گمرکی'
    )
    load_type = models.ForeignKey(
        LoadType,
        on_delete=models.PROTECT,
        related_name='parking_queues',
        null=True,
        blank=True,
        verbose_name='نوع بار'
    )
    truck_plate = models.ForeignKey(
        TruckPlate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parking_queues',
        verbose_name='پلاک خودرو'
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parking_queues',
        verbose_name='راننده'
    )

    # وضعیت
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True, default='in', verbose_name='وضعیت')

    # اطلاعات اضافی پلاک
    transit_number_plate = models.CharField(max_length=50, null=True, blank=True, verbose_name='پلاک ترانزیت')
    number_plate_json = models.TextField(null=True, blank=True, verbose_name='JSON پلاک')

    # زمان‌ها
    entry_date_time = models.DateTimeField(verbose_name='زمان ورود')
    exit_date_time = models.DateTimeField(null=True, blank=True, verbose_name='زمان خروج')
    entry_jdate = models.CharField(max_length=50, verbose_name='تاریخ ورود (جلالی)')
    exit_jdate = models.CharField(max_length=50, null=True, blank=True, verbose_name='تاریخ خروج (جلالی)')
    entry_gdate = models.CharField(max_length=50, verbose_name='تاریخ ورود (میلادی)')
    exit_gdate = models.CharField(max_length=50, null=True, blank=True, verbose_name='تاریخ خروج (میلادی)')

    # اطلاعات بار (داده‌های تکراری برای سرعت)
    load_id = models.CharField(max_length=50, verbose_name='شناسه بار')
    load_title = models.CharField(max_length=200, verbose_name='عنوان بار')

    # سایر اطلاعات
    imperative = models.BooleanField(default=False, verbose_name='ضروری')
    truck_model_title = models.CharField(max_length=100, null=True, blank=True, verbose_name='مدل کامیون')
    killer_type = models.CharField(max_length=50, null=True, blank=True, verbose_name='نوع کیلر')

    # وضعیت همگام‌سازی
    is_synced = models.BooleanField(default=True, verbose_name='همگام‌سازی شده')
    sync_date = models.DateTimeField(default=timezone.now, verbose_name='تاریخ همگام‌سازی')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        db_table = 'tirpark_parking_queue'
        verbose_name = 'صف پارکینگ'
        verbose_name_plural = 'صف‌های پارکینگ'
        ordering = ['-entry_date_time']
        indexes = [
            models.Index(fields=['receipt_number']),
            models.Index(fields=['status', 'entry_date_time']),
            models.Index(fields=['entry_date_time']),
            models.Index(fields=['sync_date']),
        ]

    def __str__(self):
        return f"{self.receipt_number} - {self.driver.full_name if self.driver else 'نامشخص'} - {self.entry_jdate}"

    def save(self, *args, **kwargs):
        """ذخیره خودکار با بررسی وابستگی‌ها"""
        # ایجاد یا دریافت خودکار نوع بار
        if self.load_id and not self.load_type:
            self.load_type, _ = LoadType.objects.get_or_create(
                load_id=self.load_id,
                defaults={'title': self.load_title}
            )

        # ایجاد یا دریافت خودکار راننده
        if self.full_name_clean and not self.driver:
            self.driver, _ = Driver.objects.get_or_create(
                full_name=self.full_name_clean,
                defaults={'last_seen': timezone.now()}
            )
        elif self.driver:
            # بروزرسانی آخرین مشاهده راننده
            Driver.objects.filter(id=self.driver.id).update(last_seen=timezone.now())

        # ایجاد یا دریافت خودکار پلاک
        if self.number_plate_json and not self.truck_plate:
            self.truck_plate = TruckPlate.create_from_json(self.number_plate_json)

        super().save(*args, **kwargs)

    @property
    def full_name_clean(self):
        """دریافت نام تمیز راننده"""
        if self.driver:
            return self.driver.full_name
        return None

    @property
    def duration_hours(self):
        """محاسبه مدت زمان حضور در پارکینگ به ساعت"""
        if self.entry_date_time:
            end_time = self.exit_date_time or timezone.now()
            delta = end_time - self.entry_date_time
            return round(delta.total_seconds() / 3600, 2)
        return 0

    @property
    def is_overdue(self):
        """بررسی آیا مدت زمان بیشتری از 24 ساعت است"""
        return self.duration_hours > 24 if self.status == 'in' else False


class SyncHistory(models.Model):
    """
    مدل تاریخچه همگام‌سازی با API
    """
    SYNC_STATUS_CHOICES = [
        ('pending', 'در حال انجام'),
        ('processing', 'در حال پردازش'),
        ('success', 'موفق'),
        ('failed', 'ناموفق'),
        ('partial', 'بخشی'),
    ]

    sync_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ همگام‌سازی')
    pages_fetched = models.IntegerField(default=0, verbose_name='تعداد صفحات دریافت شده')
    records_fetched = models.IntegerField(default=0, verbose_name='تعداد رکوردهای دریافت شده')
    records_created = models.IntegerField(default=0, verbose_name='تعداد رکوردهای جدید')
    records_updated = models.IntegerField(default=0, verbose_name='تعداد رکوردهای بروزشده')
    records_skipped = models.IntegerField(default=0, verbose_name='تعداد رکوردهای نادیده گرفته شده')
    status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    error_message = models.TextField(null=True, blank=True, verbose_name='پیام خطا')
    duration_seconds = models.FloatField(default=0, verbose_name='مدت زمان بر حسب ثانیه')
    sync_type = models.CharField(max_length=50, default='auto', verbose_name='نوع همگام‌سازی')
    metadata = models.JSONField(default=dict, verbose_name='اطلاعات اضافی')

    class Meta:
        db_table = 'tirpark_sync_history'
        verbose_name = 'تاریخچه همگام‌سازی'
        verbose_name_plural = 'تاریخچه همگام‌سازی‌ها'
        ordering = ['-sync_date']

    def __str__(self):
        return f"همگام‌سازی {self.sync_date.strftime('%Y-%m-%d %H:%M:%S')} - {self.records_fetched} رکورد"

    def get_duration_display(self):
        """نمایش مدت زمان به صورت خوانا"""
        if self.duration_seconds < 60:
            return f"{self.duration_seconds:.1f} ثانیه"
        elif self.duration_seconds < 3600:
            return f"{self.duration_seconds / 60:.1f} دقیقه"
        else:
            return f"{self.duration_seconds / 3600:.1f} ساعت"


class ParkingStatistics(models.Model):
    """
    مدل آمار و تحلیل (برای کش کردن آمارها)
    """
    stat_date = models.DateField(verbose_name='تاریخ آمار')
    total_in_queue = models.IntegerField(default=0, verbose_name='مجموع در صف')
    total_out_queue = models.IntegerField(default=0, verbose_name='مجموع خارج شده')
    avg_waiting_hours = models.FloatField(default=0, verbose_name='میانگین زمان انتظار')
    max_waiting_hours = models.FloatField(default=0, verbose_name='حداکثر زمان انتظار')
    stats_by_procedure = models.JSONField(default=dict, verbose_name='آمار بر اساس رویه')
    stats_by_load = models.JSONField(default=dict, verbose_name='آمار بر اساس بار')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        db_table = 'tirpark_statistics'
        verbose_name = 'آمار پارکینگ'
        verbose_name_plural = 'آمارهای پارکینگ'
        unique_together = ['stat_date']
        ordering = ['-stat_date']

    def __str__(self):
        return f"آمار {self.stat_date}"