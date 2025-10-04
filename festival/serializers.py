# serializers.py
from rest_framework import serializers
from .models import Festival, Room, Reserve


class RoomSerializer(serializers.ModelSerializer):
    position = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    festival_name = serializers.CharField(source='festival.name', read_only=True)

    class Meta:
        model = Room
        fields = [
            'id', 'festival', 'festival_name', 'name', 'nabsh', 'metraj',
            'description', 'price', 'is_label', 'status', 'status_display',
            'w_i', 'h_i', 'position', 'is_available'
        ]
        read_only_fields = ['id']

    def get_position(self, obj):
        return obj.get_position()

    def validate(self, data):
        # بررسی موقعیت در ماتریس
        festival = data.get('festival') or (self.instance.festival if self.instance else None)
        w_i = data.get('w_i')
        h_i = data.get('h_i')

        if festival and w_i is not None and h_i is not None:
            if w_i >= festival.number_width:
                raise serializers.ValidationError({
                    'w_i': f'موقعیت عرض باید کمتر از {festival.number_width} باشد'
                })
            if h_i >= festival.number_height:
                raise serializers.ValidationError({
                    'h_i': f'موقعیت ارتفاع باید کمتر از {festival.number_height} باشد'
                })

            # بررسی تکراری نبودن موقعیت
            existing_room = Room.objects.filter(
                festival=festival,
                w_i=w_i,
                h_i=h_i
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing_room.exists():
                raise serializers.ValidationError({
                    'position': 'این موقعیت قبلاً پر شده است'
                })

        return data


class FestivalSerializer(serializers.ModelSerializer):
    rooms_count = serializers.IntegerField(source='rooms.count', read_only=True)
    available_rooms_count = serializers.SerializerMethodField()
    matrix_dimensions = serializers.SerializerMethodField()
    total_cells = serializers.IntegerField(source='get_total_cells', read_only=True)

    class Meta:
        model = Festival
        fields = [
            'id', 'name', 'description', 'create_time',
            'number_room', 'number_width', 'number_height',
            'rooms_count', 'available_rooms_count', 'matrix_dimensions', 'total_cells'
        ]
        read_only_fields = ['id', 'create_time']

    def get_available_rooms_count(self, obj):
        return obj.rooms.filter(status=0).count()

    def get_matrix_dimensions(self, obj):
        return obj.get_matrix_dimensions()

    def validate(self, data):
        # بررسی منطقی بودن ابعاد ماتریس
        number_width = data.get('number_width')
        number_height = data.get('number_height')
        number_room = data.get('number_room')

        if number_width and number_height and number_room:
            total_cells = number_width * number_height
            if number_room > total_cells:
                raise serializers.ValidationError({
                    'number_room': f'تعداد غرفه نمی‌تواند از کل سلول‌های ماتریس ({total_cells}) بیشتر باشد'
                })

        return data


class FestivalDetailSerializer(FestivalSerializer):
    rooms = RoomSerializer(many=True, read_only=True)
    matrix_visualization = serializers.SerializerMethodField()

    class Meta(FestivalSerializer.Meta):
        fields = FestivalSerializer.Meta.fields + ['rooms', 'matrix_visualization']

    def get_matrix_visualization(self, obj):
        """ویژوالایز کردن ماتریس برای API"""
        rooms = obj.rooms.all()
        matrix = []

        for h in range(obj.number_height):
            row = []
            for w in range(obj.number_width):
                room = rooms.filter(w_i=w, h_i=h).first()
                if room:
                    room_data = {
                        'id': room.id,
                        'name': room.name,
                        'status': room.status,
                        'status_display': room.get_status_display(),
                        'price': str(room.price),
                        'is_available': room.is_available()
                    }
                    row.append(room_data)
                else:
                    row.append(None)
            matrix.append(row)

        return matrix


class RoomPositionUpdateSerializer(serializers.Serializer):
    w_i = serializers.IntegerField(min_value=0)
    h_i = serializers.IntegerField(min_value=0)

    def validate(self, data):
        festival = self.context.get('festival')
        room = self.context.get('room')

        if festival:
            w_i = data['w_i']
            h_i = data['h_i']

            if w_i >= festival.number_width:
                raise serializers.ValidationError({
                    'w_i': f'موقعیت عرض باید کمتر از {festival.number_width} باشد'
                })
            if h_i >= festival.number_height:
                raise serializers.ValidationError({
                    'h_i': f'موقعیت ارتفاع باید کمتر از {festival.number_height} باشد'
                })

            # بررسی تکراری نبودن موقعیت
            existing_room = Room.objects.filter(
                festival=festival,
                w_i=w_i,
                h_i=h_i
            ).exclude(pk=room.pk if room else None)

            if existing_room.exists():
                raise serializers.ValidationError({
                    'position': 'این موقعیت قبلاً پر شده است'
                })

        return data


class BulkRoomCreateSerializer(serializers.Serializer):
    positions = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()),
        min_length=1
    )
    name_template = serializers.CharField(default="غرفه {position}")
    default_price = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    default_metraj = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)

    def validate_positions(self, positions):
        for pos in positions:
            if 'w_i' not in pos or 'h_i' not in pos:
                raise serializers.ValidationError("هر موقعیت باید دارای w_i و h_i باشد")
        return positions


class ReserveSerializer(serializers.ModelSerializer):
    user_mobile = serializers.CharField(source='user.mobile', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    festival_name = serializers.CharField(source='room.festival.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = Reserve
        fields = [
            'id', 'user', 'user_mobile', 'room', 'room_name', 'festival_name',
            'first_name', 'last_name', 'full_name', 'national_code', 'phone',
            'email', 'address', 'company_name', 'company_registration_number',
            'activity_type', 'receipt_image', 'description', 'status',
            'status_display', 'created_at', 'updated_at', 'reserved_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'reserved_at']

    def validate(self, data):
        # بررسی اینکه غرفه قابل رزرو باشد
        room = data.get('room')
        if room and not room.can_be_reserved():
            raise serializers.ValidationError({
                'room': 'این غرفه قابل رزرو نیست'
            })

        # بررسی اینکه کاربر قبلاً این غرفه را رزرو نکرده باشد
        user = self.context['request'].user
        if room and Reserve.objects.filter(user=user, room=room, status__in=[0, 1]).exists():
            raise serializers.ValidationError({
                'room': 'شما قبلاً این غرفه را رزرو کرده‌اید'
            })

        return data


class ReserveCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserve
        fields = [
            'room', 'first_name', 'last_name', 'national_code', 'phone',
            'email', 'address', 'company_name', 'company_registration_number',
            'activity_type', 'receipt_image', 'description'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        room = validated_data['room']

        # بررسی اینکه غرفه قابل رزرو باشد
        if not room.can_be_reserved():
            raise serializers.ValidationError("این غرفه قابل رزرو نیست")

        # بررسی اینکه کاربر قبلاً این غرفه را رزرو نکرده باشد
        if Reserve.objects.filter(user=user, room=room, status__in=[0, 1]).exists():
            raise serializers.ValidationError("شما قبلاً این غرفه را رزرو کرده‌اید")

        # ایجاد رزرو
        reservation = Reserve.objects.create(
            user=user,
            **validated_data
        )

        # تغییر وضعیت غرفه به "رزرو شده"
        room.status = 1
        room.save()

        return reservation