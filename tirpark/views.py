# tirpark/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .services.sync_service import ParkingQueueSyncService
from .models import ParkingQueue, SyncHistory
from .serializers import ParkingQueueSerializer, SyncHistorySerializer
import json


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_parking_list(request):
    """
    دریافت لیست صف پارکینگ با فیلتر و صفحه‌بندی
    """
    # فیلترها
    status_filter = request.GET.get('status', 'in')
    customs_procedure = request.GET.get('customs_procedure', '')
    search = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))

    queryset = ParkingQueue.objects.select_related('driver', 'customs_procedure', 'load_type', 'truck_plate')

    if status_filter:
        queryset = queryset.filter(status=status_filter)

    if customs_procedure:
        queryset = queryset.filter(customs_procedure__code=customs_procedure)

    if search:
        queryset = queryset.filter(
            Q(driver__full_name__icontains=search) |
            Q(receipt_number__icontains=search) |
            Q(load_title__icontains=search)
        )

    # صفحه‌بندی
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    serializer = ParkingQueueSerializer(page_obj, many=True)

    return Response({
        'data': serializer.data,
        'total': paginator.count,
        'page': page,
        'per_page': per_page,
        'total_pages': paginator.num_pages,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_parking_data(request):
    try:
        print("=== SYNC STARTED ===")  # لاگ ساده
        sync_service = ParkingQueueSyncService()
        max_pages = request.data.get('max_pages')
        if max_pages:
            max_pages = int(max_pages)

        result = sync_service.sync_all(max_pages=max_pages)

        if result['success']:
            return Response({
                'status': 'success',
                'message': f"همگام‌سازی با موفقیت انجام شد",
                'data': result
            })
        else:
            return Response({
                'status': 'error',
                'message': result.get('error', 'خطا در همگام‌سازی'),
                'data': result
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        import traceback
        traceback.print_exc()  # چاپ کامل خطا در ترمینال Django
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sync_history(request):
    """
    دریافت تاریخچه همگام‌سازی‌ها
    """
    history = SyncHistory.objects.all()[:20]
    serializer = SyncHistorySerializer(history, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_parking_stats(request):
    """
    دریافت آمار پارکینگ
    """
    from django.utils import timezone

    today = timezone.now().date()

    stats = {
        'total_in_queue': ParkingQueue.objects.filter(status='in').count(),
        'today_entries': ParkingQueue.objects.filter(entry_date_time__date=today).count(),
        'today_exits': ParkingQueue.objects.filter(exit_date_time__date=today).count(),
        'overdue_count': ParkingQueue.objects.filter(status='in').extra(
            where=["EXTRACT(EPOCH FROM (now() - entry_date_time))/3600 > 24"]
        ).count(),
        'by_procedure': list(ParkingQueue.objects.filter(
            status='in'
        ).values('customs_procedure__title').annotate(
            count=Count('id')
        )),
    }

    return Response(stats)