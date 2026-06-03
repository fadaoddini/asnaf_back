# tirpark/services/sync_service.py
import requests
import json
import time
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from typing import Dict, List, Tuple, Optional
from ..models import ParkingQueue, SyncHistory, CustomsProcedure, LoadType, Driver, TruckPlate


class TirParkAPIClient:
    """
    کلید ارتباط با API سایت tirpark.ir
    """

    BASE_URL = "https://tirpark.ir/api/v1/parking/queue"
    PER_PAGE = 30
    TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'fa-IR,fa;q=0.9',
        })

    def fetch_page(self, page: int, retry_count: int = 0) -> Tuple[List[Dict], int, int]:
        """
        دریافت یک صفحه از API با قابلیت تلاش مجدد
        """
        url = f"{self.BASE_URL}?page={page}&per_page={self.PER_PAGE}"

        try:
            response = self.session.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()
            data = response.json()

            items = data.get('data', [])
            total = data.get('total', 0)
            current_page = data.get('current_page', page)

            # کش کردن تعداد کل برای استفاده بعدی
            if page == 1 and total > 0:
                cache.set('tirpark_total_records', total, 3600)

            return items, total, current_page

        except requests.exceptions.RequestException as e:
            if retry_count < self.MAX_RETRIES:
                time.sleep(self.RETRY_DELAY)
                return self.fetch_page(page, retry_count + 1)
            raise Exception(f"خطا در دریافت صفحه {page} بعد از {self.MAX_RETRIES} تلاش: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"خطا در پردازش JSON صفحه {page}: {str(e)}")

    def get_all_pages(self, max_pages: Optional[int] = None, progress_callback=None) -> List[Dict]:
        """
        دریافت تمام صفحات
        """
        all_data = []

        # دریافت صفحه اول
        print("در حال دریافت صفحه اول...")
        first_page_data, total_records, _ = self.fetch_page(1)
        all_data.extend(first_page_data)

        if progress_callback:
            progress_callback(1, 1, len(all_data))

        # محاسبه تعداد کل صفحات
        import math
        total_pages = math.ceil(total_records / self.PER_PAGE)

        if max_pages:
            total_pages = min(total_pages, max_pages)

        print(f"کل صفحات: {total_pages}، کل رکوردها: {total_records}")

        # دریافت صفحات باقی‌مانده
        for page in range(2, total_pages + 1):
            print(f"در حال دریافت صفحه {page} از {total_pages}...")
            page_data, _, _ = self.fetch_page(page)
            all_data.extend(page_data)

            if progress_callback:
                progress_callback(page, total_pages, len(all_data))

            # تاخیر برای جلوگیری از محدودیت
            time.sleep(0.3)

        return all_data


class ParkingQueueSyncService:
    """
    سرویس همگام‌سازی اطلاعات پارکینگ
    """

    def __init__(self):
        self.api_client = TirParkAPIClient()

    def sync_all(self, max_pages: Optional[int] = None, progress_callback=None) -> Dict:
        """
        همگام‌سازی کامل اطلاعات
        """
        sync_history = SyncHistory.objects.create(status='pending', sync_type='manual')
        start_time = time.time()

        try:
            # دریافت اطلاعات از API
            all_data = self.api_client.get_all_pages(max_pages, progress_callback)

            # بروزرسانی تاریخچه
            sync_history.pages_fetched = len(set([d.get('id') for d in all_data]))  # تقریبی
            sync_history.records_fetched = len(all_data)
            sync_history.status = 'processing'
            sync_history.save()

            # ذخیره در دیتابیس
            created, updated, skipped = self.save_to_database(all_data, progress_callback)

            # بروزرسانی نهایی تاریخچه
            duration = time.time() - start_time
            sync_history.records_created = created
            sync_history.records_updated = updated
            sync_history.records_skipped = skipped
            sync_history.status = 'success'
            sync_history.duration_seconds = duration
            sync_history.metadata = {
                'max_pages': max_pages,
                'total_pages': sync_history.pages_fetched,
                'api_url': self.api_client.BASE_URL
            }
            sync_history.save()

            # محاسبه آمار جدید
            self.calculate_statistics()

            return {
                'success': True,
                'total_records': len(all_data),
                'records_created': created,
                'records_updated': updated,
                'records_skipped': skipped,
                'duration': duration,
                'sync_id': sync_history.id
            }

        except Exception as e:
            sync_history.status = 'failed'
            sync_history.error_message = str(e)
            sync_history.duration_seconds = time.time() - start_time
            sync_history.save()

            return {
                'success': False,
                'error': str(e),
                'sync_id': sync_history.id
            }

    @transaction.atomic
    def save_to_database(self, data: List[Dict], progress_callback=None) -> Tuple[int, int, int]:
        """
        ذخیره اطلاعات در دیتابیس
        """
        created_count = 0
        updated_count = 0
        skipped_count = 0

        # پیش‌بارگذاری رویه‌های گمرکی
        customs_procedures = {}
        for proc in CustomsProcedure.objects.all():
            customs_procedures[proc.code] = proc

        for index, item in enumerate(data):
            try:
                # ایجاد یا دریافت رویه گمرکی
                proc_code = item.get('customs_procedure')
                if proc_code not in customs_procedures:
                    customs_procedures[proc_code], _ = CustomsProcedure.objects.get_or_create(
                        code=proc_code,
                        defaults={
                            'name': item.get('customs_procedure_name', ''),
                            'title': item.get('customs_procedure_title', '')
                        }
                    )

                # ایجاد یا دریافت نوع بار
                load_type, _ = LoadType.objects.get_or_create(
                    load_id=item.get('load_id', '0'),
                    defaults={'title': item.get('load_title', 'متفرقه')}
                )

                # ایجاد یا دریافت راننده
                full_name = item.get('full_name', '').strip()
                driver = None
                if full_name:
                    driver, _ = Driver.objects.get_or_create(
                        full_name=full_name,
                        defaults={'last_seen': timezone.now()}
                    )
                    if driver and not driver.last_seen:
                        driver.last_seen = timezone.now()
                        driver.save()

                # ایجاد یا دریافت پلاک
                truck_plate = None
                number_plate_json = item.get('number_plate')
                if number_plate_json:
                    truck_plate = TruckPlate.create_from_json(number_plate_json)

                # تبدیل زمان
                entry_datetime = self.parse_datetime(item.get('entry_date_time'))
                exit_datetime = self.parse_datetime(item.get('exit_date_time')) if item.get('exit_date_time') else None

                # ایجاد یا بروزرسانی رکورد
                obj, created = ParkingQueue.objects.update_or_create(
                    id=item.get('id'),
                    defaults={
                        'receipt_number': item.get('receipt_number'),
                        'customs_procedure': customs_procedures[proc_code],
                        'load_type': load_type,
                        'driver': driver,
                        'truck_plate': truck_plate,
                        'status': item.get('status', 'in'),
                        'transit_number_plate': item.get('transit_number_plate'),
                        'number_plate_json': number_plate_json,
                        'entry_date_time': entry_datetime,
                        'exit_date_time': exit_datetime,
                        'entry_jdate': item.get('entry_jdate'),
                        'exit_jdate': item.get('exit_jdate'),
                        'entry_gdate': item.get('entry_gdate'),
                        'exit_gdate': item.get('exit_gdate', ''),
                        'load_id': item.get('load_id'),
                        'load_title': item.get('load_title'),
                        'imperative': bool(item.get('imperative', 0)),
                        'truck_model_title': item.get('truck_model_title'),
                        'killer_type': item.get('killer_type'),
                        'is_synced': True,
                        'sync_date': timezone.now(),
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                # گزارش پیشرفت
                if progress_callback and (index + 1) % 100 == 0:
                    progress_callback(index + 1, len(data), None)

            except Exception as e:
                print(f"خطا در ذخیره رکورد {item.get('id')}: {str(e)}")
                skipped_count += 1

        return created_count, updated_count, skipped_count

    def parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """
        تبدیل رشته datetime به شیء datetime
        """
        if not datetime_str:
            return None
        try:
            # فرمت: '2026-05-06 00:41:53.000'
            clean_str = datetime_str.split('.')[0]
            return datetime.strptime(clean_str, '%Y-%m-%d %H:%M:%S')
        except:
            return None

    def calculate_statistics(self):
        """
        محاسبه آمار روزانه
        """
        from django.db.models import Count, Avg, Max, Q
        from ..models import ParkingStatistics

        today = timezone.now().date()

        # محاسبه آمار
        stats = ParkingQueue.objects.filter(entry_date_time__date=today)

        total_in = stats.filter(status='in').count()
        total_out = stats.filter(status='out').count()

        # محاسبه میانگین زمان انتظار برای رکوردهای خارج شده
        avg_waiting = stats.filter(
            status='out',
            exit_date_time__isnull=False
        ).extra(
            select={'waiting_hours': "EXTRACT(EPOCH FROM (exit_date_time - entry_date_time))/3600"}
        ).aggregate(Avg('waiting_hours'))['waiting_hours__avg'] or 0

        max_waiting = stats.filter(
            status='out',
            exit_date_time__isnull=False
        ).extra(
            select={'waiting_hours': "EXTRACT(EPOCH FROM (exit_date_time - entry_date_time))/3600"}
        ).aggregate(Max('waiting_hours'))['waiting_hours__max'] or 0

        # آمار بر اساس رویه
        stats_by_procedure = {}
        procedure_stats = stats.values('customs_procedure__title').annotate(
            count=Count('id'),
            in_count=Count('id', filter=Q(status='in')),
            out_count=Count('id', filter=Q(status='out'))
        )
        for proc in procedure_stats:
            stats_by_procedure[proc['customs_procedure__title']] = {
                'total': proc['count'],
                'in': proc['in_count'],
                'out': proc['out_count']
            }

        # ذخیره آمار
        ParkingStatistics.objects.update_or_create(
            stat_date=today,
            defaults={
                'total_in_queue': total_in,
                'total_out_queue': total_out,
                'avg_waiting_hours': avg_waiting,
                'max_waiting_hours': max_waiting,
                'stats_by_procedure': stats_by_procedure,
                'stats_by_load': {},
            }
        )