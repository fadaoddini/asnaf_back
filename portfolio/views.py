# portfolio/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Project
from .serializers import ProjectSerializer, ProjectListSerializer


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet فقط خواندنی برای پروژه‌ها"""
    queryset = Project.objects.filter(is_active=True)
    permission_classes = [permissions.AllowAny]  # برای مشاهده عمومی

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer

    @action(detail=False, methods=['get'], url_path='by-language')
    def by_language(self, request):
        """دریافت پروژه‌ها با ساختار مناسب برای فرانت‌اند"""
        lang = request.query_params.get('lang', 'fa')
        queryset = self.get_queryset().order_by('order')
        serializer = ProjectSerializer(queryset, many=True, context={'request': request})

        # بر اساس زبان فیلتر کن (اختیاری - همه رو برمیگردونه چون فرانت خودش مدیریت میکنه)
        return Response(serializer.data)