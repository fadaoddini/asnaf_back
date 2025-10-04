from django.db import models
from django.utils import timezone

from login.models import MyUser


class Festival(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام نمایشگاه")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    create_time = models.DateTimeField(default=timezone.now, verbose_name="زمان ایجاد")
    number_room = models.PositiveIntegerField(verbose_name="تعداد غرفه")
    number_width = models.PositiveIntegerField(verbose_name="عرض ماتریس")
    number_height = models.PositiveIntegerField(verbose_name="ارتفاع ماتریس")

    class Meta:
        verbose_name = "نمایشگاه"
        verbose_name_plural = "نمایشگاه‌ها"

    def __str__(self):
        return self.name

    def get_matrix_dimensions(self):
        """ابعاد ماتریس نمایشگاه"""
        return (self.number_width, self.number_height)

    def get_total_cells(self):
        """تعداد کل سلول‌های ماتریس"""
        return self.number_width * self.number_height



class Room(models.Model):
    STATUS_CHOICES = [
        (0, 'آزاد'),
        (1, 'رزرو شده'),
        (2, 'قطعی شده'),
        (3, 'غیرقابل فروش'),
    ]

    festival = models.ForeignKey(
        Festival,
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name="نمایشگاه"
    )
    name = models.CharField(max_length=255, verbose_name="نام غرفه")
    nabsh = models.BooleanField(default=True, verbose_name="نبش دارد")
    metraj = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="متراژ"
    )
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="قیمت"
    )
    is_label = models.BooleanField(default=False, verbose_name="لیبل دارد")
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=0,
        verbose_name="وضعیت"
    )

    # موقعیت در ماتریس
    w_i = models.PositiveIntegerField(verbose_name="موقعیت در عرض")  # ستون
    h_i = models.PositiveIntegerField(verbose_name="موقعیت در ارتفاع")  # ردیف

    class Meta:
        verbose_name = "غرفه"
        verbose_name_plural = "غرفه‌ها"
        unique_together = ['festival', 'w_i', 'h_i']  # هر موقعیت فقط یک غرفه

    def __str__(self):
        return f"{self.name} - {self.festival.name}"

    def get_position(self):
        """موقعیت غرفه در ماتریس"""
        return (self.w_i, self.h_i)

    def get_matrix_index(self):
        """ایندکس در ماتریس (برای محاسبات)"""
        return self.h_i * self.festival.number_width + self.w_i

    def is_available(self):
        """آیا غرفه قابل فروش است؟"""
        return self.status == 0

    def get_adjacent_positions(self):
        """موقعیت‌های مجاور غرفه"""
        adjacent = []
        width, height = self.festival.get_matrix_dimensions()

        # چک کردن چهار جهت اصلی
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dw, dh in directions:
            new_w = self.w_i + dw
            new_h = self.h_i + dh

            # چک کردن مرزهای ماتریس
            if 0 <= new_w < width and 0 <= new_h < height:
                adjacent.append((new_w, new_h))

        return adjacent


    def get_active_reservation(self):
        """دریافت رزرو فعال برای این غرفه"""
        return self.reservations.filter(status__in=[0, 1]).first()

    def is_reserved(self):
        """آیا غرفه رزرو شده است؟"""
        return self.status == 1

    def can_be_reserved(self):
        """آیا غرفه قابل رزرو است؟"""
        return self.status == 0 and self.nabsh


class Reserve(models.Model):
    STATUS_CHOICES = [
        (0, 'در انتظار تایید'),
        (1, 'تایید شده'),
        (2, 'رد شده'),
        (3, 'لغو شده'),
    ]

    # ارتباط با کاربر
    user = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name="کاربر"
    )

    # ارتباط با غرفه
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name="غرفه"
    )

    # اطلاعات تماس و شخصی
    first_name = models.CharField(max_length=100, verbose_name="نام")
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی")
    national_code = models.CharField(max_length=10, verbose_name="کد ملی")
    phone = models.CharField(max_length=15, verbose_name="تلفن ثابت")
    email = models.EmailField(blank=True, null=True, verbose_name="ایمیل")
    address = models.TextField(verbose_name="آدرس")

    # اطلاعات کسب و کار
    company_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="نام شرکت/مؤسسه")
    company_registration_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="شماره ثبت شرکت"
    )
    activity_type = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="نوع فعالیت"
    )

    # اطلاعات پرداخت و فایل‌ها
    receipt_image = models.ImageField(
        upload_to='receipts/%Y/%m/%d/',
        verbose_name="تصویر فیش واریزی"
    )
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات اضافی")

    # وضعیت رزرو
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=0,
        verbose_name="وضعیت رزرو"
    )

    # تاریخ‌ها
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    reserved_at = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ رزرو")

    class Meta:
        verbose_name = "رزرو"
        verbose_name_plural = "رزروها"
        ordering = ['-created_at']

    def __str__(self):
        return f"رزرو {self.id} - {self.user.mobile} - {self.room.name}"

    def save(self, *args, **kwargs):
        # اگر وضعیت به "تایید شده" تغییر کرد، تاریخ رزرو را تنظیم کن
        if self.status == 1 and not self.reserved_at:
            self.reserved_at = timezone.now()

        # بروزرسانی اطلاعات کاربر اگر لازم است
        if not self.user.first_name and self.first_name:
            self.user.first_name = self.first_name
        if not self.user.last_name and self.last_name:
            self.user.last_name = self.last_name
        if not self.user.email and self.email:
            self.user.email = self.email

        self.user.save()

        super().save(*args, **kwargs)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def is_pending(self):
        return self.status == 0

    def is_approved(self):
        return self.status == 1

    def is_rejected(self):
        return self.status == 2

    def is_cancelled(self):
        return self.status == 3

