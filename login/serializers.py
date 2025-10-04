from rest_framework import serializers
from django.utils import timezone
from login.models import MyUser, Follow, Address


class EditProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['first_name', 'last_name', 'email', 'mobile']
        read_only_fields = ['mobile']

    def validate_email(self, value):
        user = self.instance
        if MyUser.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("این ایمیل قبلاً استفاده شده است.")
        return value


class MyUserSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = MyUser
        fields = ('first_name', 'last_name', 'email', 'display_name', 'status', 'image', 'mobile', 'id', 'followers_count', 'following_count', 'product_count')

    def get_status(self, obj):
        status = "Nothing"
        first_name = obj.first_name
        last_name = obj.last_name
        if (first_name != "") and (last_name != ""):
            status = "Ok"

        return status

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_product_count(self, obj):
        return obj.products.count()

    def get_display_name(self, obj):
        # بررسی اینکه first_name و last_name خالی هستند یا نه
        if not obj.first_name and not obj.last_name:
            return "کاربر محترم"
        return f"{obj.first_name} {obj.last_name}".strip()



class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ['follower', 'followed', 'created_at']



class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id','receiver_name', 'address', 'postal_code', 'phone', 'city', 'sub_city', 'is_active']


class MyProfileSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    bid_count = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    bids = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()  # اضافه کردن فیلد جدید

    class Meta:
        model = MyUser
        fields = (
            'first_name',
            'last_name',
            'display_name',  # اضافه کردن فیلد جدید به لیست
            'status',
            'image',
            'mobile',
            'email',
            'id',
            'followers_count',
            'following_count',
            'product_count',
            'bid_count',
            'products',
            'bids',
        )

    def get_display_name(self, obj):
        if not obj.first_name and not obj.last_name:
            return "کاربر محترم"
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_status(self, obj):
        status = "Nothing"
        first_name = obj.first_name
        last_name = obj.last_name
        if first_name and last_name:
            status = "Ok"
        return status

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_product_count(self, obj):
        return obj.products.count()

    def get_bid_count(self, obj):
        return obj.bids.count()

    def get_products(self, obj):
        products = obj.products.filter(
            status=2,
            is_active=True,
            expire_time__gte=timezone.now()
        ).all()
        from catalogue.serializers import ApiAllProductSerializer
        return ApiAllProductSerializer(products, many=True).data

    def get_bids(self, obj):
        bids = obj.bids.all()
        from bid.serializers import BidSerializer
        return BidSerializer(bids, many=True).data