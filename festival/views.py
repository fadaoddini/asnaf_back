# views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Festival, Room, Reserve
from .serializers import FestivalSerializer, FestivalDetailSerializer, RoomSerializer, ReserveSerializer, \
    ReserveCreateSerializer


class FestivalView(APIView):
    def get(self, request):
        """دریافت لیست همه نمایشگاه‌ها"""
        festivals = Festival.objects.all()
        serializer = FestivalSerializer(festivals, many=True)
        return Response(serializer.data)

    def post(self, request):
        """ایجاد نمایشگاه جدید"""
        serializer = FestivalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FestivalDetailView(APIView):
    def get(self, request, festival_id):
        """دریافت جزئیات یک نمایشگاه به همراه غرفه‌هایش"""
        festival = get_object_or_404(Festival, id=festival_id)
        serializer = FestivalDetailSerializer(festival)
        return Response(serializer.data)

    def put(self, request, festival_id):
        """ویرایش نمایشگاه"""
        festival = get_object_or_404(Festival, id=festival_id)
        serializer = FestivalSerializer(festival, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, festival_id):
        """حذف نمایشگاه"""
        festival = get_object_or_404(Festival, id=festival_id)
        festival.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoomView(APIView):
    def get(self, request, festival_id):
        """دریافت همه غرفه‌های یک نمایشگاه"""
        festival = get_object_or_404(Festival, id=festival_id)
        rooms = festival.rooms.all()
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    def post(self, request, festival_id):
        """ایجاد غرفه جدید برای نمایشگاه"""
        festival = get_object_or_404(Festival, id=festival_id)

        # اضافه کردن festival به داده‌ها
        data = request.data.copy()
        data['festival'] = festival_id

        serializer = RoomSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoomDetailView(APIView):
    def get(self, request, festival_id, room_id):
        """دریافت جزئیات یک غرفه"""
        festival = get_object_or_404(Festival, id=festival_id)
        room = get_object_or_404(Room, id=room_id, festival=festival)
        serializer = RoomSerializer(room)
        return Response(serializer.data)

    def put(self, request, festival_id, room_id):
        """ویرایش غرفه"""
        festival = get_object_or_404(Festival, id=festival_id)
        room = get_object_or_404(Room, id=room_id, festival=festival)

        serializer = RoomSerializer(room, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, festival_id, room_id):
        """حذف غرفه"""
        festival = get_object_or_404(Festival, id=festival_id)
        room = get_object_or_404(Room, id=room_id, festival=festival)
        room.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FestivalRoomsMatrixView(APIView):
    def get(self, request, festival_id):
        """دریافت ماتریس کامل غرفه‌های یک نمایشگاه"""
        festival = get_object_or_404(Festival, id=festival_id)

        # ایجاد ماتریس
        matrix = []
        for h in range(festival.number_height):
            row = []
            for w in range(festival.number_width):
                room = Room.objects.filter(festival=festival, w_i=w, h_i=h).first()
                if room:
                    room_data = RoomSerializer(room).data
                    row.append(room_data)
                else:
                    row.append({
                        'empty': True,
                        'position': (w, h),
                        'available': True
                    })
            matrix.append(row)

        festival_data = FestivalSerializer(festival).data
        response_data = {
            'festival': festival_data,
            'matrix': matrix,
            'dimensions': {
                'width': festival.number_width,
                'height': festival.number_height
            }
        }

        return Response(response_data)


class AvailableRoomsView(APIView):
    def get(self, request, festival_id):
        """دریافت غرفه‌های خالی یک نمایشگاه"""
        festival = get_object_or_404(Festival, id=festival_id)
        available_rooms = festival.rooms.filter(status=0)
        serializer = RoomSerializer(available_rooms, many=True)
        return Response(serializer.data)


class RoomReservationView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReserveCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            try:
                reservation = serializer.save()

                # سریالایز کردن داده‌های بازگشتی
                response_serializer = ReserveSerializer(reservation)

                return Response({
                    'status': 'success',
                    'message': 'رزرو با موفقیت ثبت شد',
                    'data': response_serializer.data
                }, status=status.HTTP_201_CREATED)

            except ValueError as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'error',
            'message': 'خطا در ثبت رزرو',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserReservationsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reservations = Reserve.objects.filter(user=request.user).order_by('-created_at')
        serializer = ReserveSerializer(reservations, many=True)
        return Response(serializer.data)


class ReservationDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, reservation_id):
        reservation = get_object_or_404(
            Reserve,
            id=reservation_id,
            user=request.user
        )
        serializer = ReserveSerializer(reservation)
        return Response(serializer.data)

    def delete(self, request, reservation_id):
        reservation = get_object_or_404(
            Reserve,
            id=reservation_id,
            user=request.user
        )

        if reservation.status != 0:  # فقط رزروهای در انتظار قابل لغو هستند
            return Response({
                'status': 'error',
                'message': 'فقط رزروهای در انتظار تایید قابل لغو هستند'
            }, status=status.HTTP_400_BAD_REQUEST)

        reservation.status = 3  # لغو شده
        reservation.save()

        # آزاد کردن غرفه
        reservation.room.status = 0
        reservation.room.save()

        return Response({
            'status': 'success',
            'message': 'رزرو با موفقیت لغو شد'
        })


class RoomReservationInfoView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)

        # فقط ادمین‌ها می‌توانند اطلاعات رزرو را ببینند
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'error': 'دسترسی غیرمجاز'
            }, status=status.HTTP_403_FORBIDDEN)

        reservation = room.get_active_reservation()
        if not reservation:
            return Response({
                'error': 'هیچ رزرو فعالی برای این غرفه وجود ندارد'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ReserveSerializer(reservation)
        return Response(serializer.data)


class ReservationStatusUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, reservation_id):
        # فقط ادمین‌ها می‌توانند وضعیت را تغییر دهند
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'error': 'دسترسی غیرمجاز'
            }, status=status.HTTP_403_FORBIDDEN)

        reservation = get_object_or_404(Reserve, id=reservation_id)
        serializer = ReserveSerializer(reservation, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)