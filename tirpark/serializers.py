# tirpark/serializers.py
from rest_framework import serializers
from .models import ParkingQueue, CustomsProcedure, Driver, LoadType, TruckPlate, SyncHistory


class CustomsProcedureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomsProcedure
        fields = ['code', 'title', 'name']


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['id', 'full_name', 'mobile', 'national_code']


class LoadTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoadType
        fields = ['load_id', 'title', 'category']


class TruckPlateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TruckPlate
        fields = ['full_plate', 'location_section', 'serial_section', 'letter_section', 'code_section']


class ParkingQueueSerializer(serializers.ModelSerializer):
    customs_procedure = CustomsProcedureSerializer(read_only=True)
    driver = DriverSerializer(read_only=True)
    load_type = LoadTypeSerializer(read_only=True)
    truck_plate = TruckPlateSerializer(read_only=True)
    waiting_hours = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = ParkingQueue
        fields = [
            'id', 'receipt_number', 'status', 'customs_procedure', 'driver',
            'load_type', 'truck_plate', 'load_title', 'entry_jdate',
            'exit_jdate', 'entry_gdate', 'exit_gdate', 'imperative',
            'waiting_hours', 'is_overdue', 'transit_number_plate'
        ]

    def get_waiting_hours(self, obj):
        return obj.duration_hours

    def get_is_overdue(self, obj):
        return obj.is_overdue


class SyncHistorySerializer(serializers.ModelSerializer):
    duration_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = SyncHistory
        fields = [
            'id', 'sync_date', 'records_fetched', 'records_created',
            'records_updated', 'status', 'status_display', 'duration_seconds',
            'duration_display', 'error_message'
        ]

    def get_duration_display(self, obj):
        return obj.get_duration_display()

    def get_status_display(self, obj):
        status_map = {
            'success': 'موفق',
            'failed': 'ناموفق',
            'pending': 'در حال انجام',
            'processing': 'در حال پردازش'
        }
        return status_map.get(obj.status, obj.status)