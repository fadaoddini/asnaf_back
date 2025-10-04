# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Festival, Room


@admin.register(Festival)
class FestivalAdmin(admin.ModelAdmin):
    list_display = ['name', 'create_time', 'number_room', 'number_width', 'number_height', 'matrix_display']
    list_filter = ['create_time']
    search_fields = ['name', 'description']
    readonly_fields = ['create_time']
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'description', 'create_time')
        }),
        ('ابعاد ماتریس', {
            'fields': ('number_room', 'number_width', 'number_height')
        }),
    )

    def matrix_display(self, obj):
        return f"{obj.number_width} × {obj.number_height}"

    matrix_display.short_description = 'ابعاد ماتریس'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'festival',
        'position_display',
        'status',  # اضافه کردن status به list_display
        'status_display',
        'price',
        'is_available_display'
    ]
    list_filter = ['festival', 'status', 'nabsh', 'is_label']
    search_fields = ['name', 'festival__name', 'description']
    list_editable = ['status', 'price']  # حالا status در list_display وجود دارد
    readonly_fields = ['position_display_admin']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('festival', 'name', 'description')
        }),
        ('موقعیت و ابعاد', {
            'fields': ('w_i', 'h_i', 'position_display_admin', 'metraj', 'nabsh')
        }),
        ('وضعیت و قیمت', {
            'fields': ('status', 'price', 'is_label')
        }),
    )

    def position_display(self, obj):
        return f"({obj.w_i}, {obj.h_i})"

    position_display.short_description = 'موقعیت'

    def position_display_admin(self, obj):
        return f"ستون: {obj.w_i}, ردیف: {obj.h_i}"

    position_display_admin.short_description = 'موقعیت در ماتریس'

    def status_display(self, obj):
        status_colors = {
            0: 'green',  # آزاد
            1: 'orange',  # رزرو شده
            2: 'red',  # قطعی شده
            3: 'gray'  # غیرقابل فروش
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_display.short_description = 'وضعیت (رنگی)'

    def is_available_display(self, obj):
        return obj.is_available()

    is_available_display.boolean = True
    is_available_display.short_description = 'قابل فروش'