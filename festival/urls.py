from django.urls import path
from .views import (
    FestivalView,
    FestivalDetailView,
    RoomView,
    RoomDetailView,
    FestivalRoomsMatrixView,
    AvailableRoomsView, RoomReservationView, UserReservationsView, ReservationDetailView, RoomReservationInfoView,
    ReservationStatusUpdateView
)

urlpatterns = [
    # نمایشگاه‌ها
    path('v1/festival', FestivalView.as_view(), name='festival-list'),
    path('v1/festival/<int:festival_id>', FestivalDetailView.as_view(), name='festival-detail'),

    # غرفه‌ها
    path('v1/festival/<int:festival_id>/room', RoomView.as_view(), name='room-list'),
    path('v1/festival/<int:festival_id>/room/<int:room_id>', RoomDetailView.as_view(), name='room-detail'),

    # ماتریس و وضعیت
    path('v1/festival/<int:festival_id>/matrix', FestivalRoomsMatrixView.as_view(), name='festival-matrix'),
    path('v1/festival/<int:festival_id>/available-rooms', AvailableRoomsView.as_view(), name='available-rooms'),

    path('v1/room/reservation', RoomReservationView.as_view(), name='room-reservation'),
    path('v1/user/reservations', UserReservationsView.as_view(), name='user-reservations'),
    path('v1/reservation/<int:reservation_id>', ReservationDetailView.as_view(), name='reservation-detail'),

    # مدیریت رزرو برای ادمین
    path('v1/room/<int:room_id>/reservation-info', RoomReservationInfoView.as_view(), name='room-reservation-info'),
    path('v1/reservation/<int:reservation_id>/status', ReservationStatusUpdateView.as_view(),
         name='reservation-status-update'),
]