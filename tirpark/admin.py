# tirpark/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    CustomsProcedure, LoadType, TruckPlate, Driver,
    ParkingQueue, SyncHistory, ParkingStatistics
)


@admin.register(CustomsProcedure)
class CustomsProcedureAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'title', 'name']
    list_editable = ['is_active']


@admin.register(LoadType)
class LoadTypeAdmin(admin.ModelAdmin):
    list_display = ['load_id', 'title', 'category']
    search_fields = ['load_id', 'title']
    list_filter = ['category']


@admin.register(TruckPlate)
class TruckPlateAdmin(admin.ModelAdmin):
    list_display = ['full_plate', 'location_section', 'serial_section', 'letter_section']
    search_fields = ['full_plate', 'location_section', 'serial_section']
    list_filter = ['letter_section']


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'mobile', 'national_code', 'last_seen', 'trip_count']
    search_fields = ['full_name', 'national_code', 'mobile']
    list_filter = ['last_seen']

    def trip_count(self, obj):
        return obj.parking_queues.count()

    trip_count.short_description = 'تعداد سفرها'


@admin.register(ParkingQueue)
class ParkingQueueAdmin(admin.ModelAdmin):
    list_display = [
        'receipt_number', 'driver_link', 'load_title', 'status_badge',
        'entry_jdate', 'duration', 'is_overdue_badge'
    ]
    list_filter = ['status', 'customs_procedure', 'imperative', 'entry_date_time']
    search_fields = ['receipt_number', 'driver__full_name', 'load_title', 'transit_number_plate']
    date_hierarchy = 'entry_date_time'
    readonly_fields = ['id', 'created_at', 'updated_at', 'sync_date']
    list_per_page = 50
    list_select_related = ['driver', 'customs_procedure', 'load_type', 'truck_plate']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('id', 'receipt_number', 'status', 'driver', 'customs_procedure')
        }),
        ('اطلاعات پلاک', {
            'fields': ('truck_plate', 'transit_number_plate', 'number_plate_json')
        }),
        ('اطلاعات بار', {
            'fields': ('load_type', 'load_id', 'load_title')
        }),
        ('زمان‌ها', {
            'fields': ('entry_date_time', 'exit_date_time', 'entry_jdate', 'exit_jdate', 'entry_gdate', 'exit_gdate')
        }),
        ('سایر اطلاعات', {
            'fields': ('imperative', 'truck_model_title', 'killer_type', 'is_synced', 'sync_date'),
            'classes': ('collapse',)
        }),
        ('سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def driver_link(self, obj):
        if obj.driver:
            url = reverse('admin:tirpark_driver_change', args=[obj.driver.id])
            return format_html('<a href="{}">{}</a>', url, obj.driver.full_name)
        return '-'

    driver_link.short_description = 'راننده'
    driver_link.admin_order_field = 'driver__full_name'

    def status_badge(self, obj):
        colors = {
            'in': 'blue',
            'out': 'green',
            'waiting': 'orange',
            'processing': 'purple'
        }
        status_text = {
            'in': 'در پارکینگ',
            'out': 'خارج شده',
            'waiting': 'در انتظار',
            'processing': 'در حال بررسی'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'),
            status_text.get(obj.status, obj.status)
        )

    status_badge.short_description = 'وضعیت'

    def duration(self, obj):
        hours = obj.duration_hours
        if hours < 1:
            minutes = int(hours * 60)
            return f"{minutes} دقیقه"
        elif hours < 24:
            return f"{hours:.1f} ساعت"
        else:
            days = int(hours / 24)
            remaining_hours = hours % 24
            return f"{days} روز {remaining_hours:.0f} ساعت"

    duration.short_description = 'مدت زمان'

    def is_overdue_badge(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">⚠️ دیرکرد</span>')
        return '-'

    is_overdue_badge.short_description = 'وضعیت دیرکرد'

    actions = ['mark_as_out', 'sync_selected']

    def mark_as_out(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='in').update(
            status='out',
            exit_date_time=timezone.now()
        )
        self.message_user(request, f'{updated} رکورد به وضعیت خروج تغییر یافت.')

    mark_as_out.short_description = 'تغییر وضعیت به خارج شده'

    def sync_selected(self, request, queryset):
        queryset.update(is_synced=False, sync_date=None)
        self.message_user(request, 'رکوردهای انتخاب شده برای همگام‌سازی مجدد علامت‌گذاری شدند.')

    sync_selected.short_description = 'علامت‌گذاری برای همگام‌سازی مجدد'


@admin.register(SyncHistory)
class SyncHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'sync_date', 'records_fetched', 'records_created', 'records_updated',
        'status_badge', 'duration_display', 'sync_type'
    ]
    list_filter = ['status', 'sync_type', 'sync_date']
    readonly_fields = ['sync_date', 'duration_seconds', 'metadata']
    search_fields = ['error_message']

    def status_badge(self, obj):
        colors = {
            'success': 'green',
            'failed': 'red',
            'pending': 'orange',
            'processing': 'blue',
            'partial': 'purple'
        }
        status_text = {
            'success': 'موفق',
            'failed': 'ناموفق',
            'pending': 'در حال انجام',
            'processing': 'در حال پردازش',
            'partial': 'بخشی'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'),
            status_text.get(obj.status, obj.status)
        )

    status_badge.short_description = 'وضعیت'

    def duration_display(self, obj):
        return obj.get_duration_display()

    duration_display.short_description = 'مدت زمان'


@admin.register(ParkingStatistics)
class ParkingStatisticsAdmin(admin.ModelAdmin):
    list_display = ['stat_date', 'total_in_queue', 'total_out_queue', 'avg_waiting_hours', 'max_waiting_hours']
    list_filter = ['stat_date']
    readonly_fields = ['stats_by_procedure', 'stats_by_load']
    date_hierarchy = 'stat_date'