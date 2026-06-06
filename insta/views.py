# insta/views.py
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Post, Like, Comment, CommentLike, Story
from .serializers import (
    PostSerializer, CommentSerializer, CommentCreateSerializer,
    StorySerializer
)
from django.contrib.auth import get_user_model

User = get_user_model()


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت پست‌ها"""
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Post.objects.filter(is_active=True)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """لایک کردن پست"""
        post = self.get_object()
        like, created = Like.objects.get_or_create(post=post, user=request.user)

        if created:
            post.likes_count += 1
            post.save()
            return Response({'status': 'liked', 'likes_count': post.likes_count})
        else:
            like.delete()
            post.likes_count -= 1
            post.save()
            return Response({'status': 'unliked', 'likes_count': post.likes_count})

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """دریافت کامنت‌های تایید شده یک پست"""
        post = self.get_object()
        comments = post.comments.filter(status='approved')
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """افزودن کامنت جدید (نیاز به تایید)"""
        post = self.get_object()
        serializer = CommentCreateSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save(post=post)
            post.comments_count += 1
            post.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت کامنت‌ها"""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # ادمین همه کامنت‌ها را می‌بیند، کاربر فقط کامنت‌های خودش
        if self.request.user.is_staff:
            return Comment.objects.all()
        return Comment.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """لایک کردن کامنت"""
        comment = self.get_object()
        like, created = CommentLike.objects.get_or_create(comment=comment, user=request.user)

        if created:
            comment.likes_count += 1
            comment.save()
            return Response({'status': 'liked', 'likes_count': comment.likes_count})
        else:
            like.delete()
            comment.likes_count -= 1
            comment.save()
            return Response({'status': 'unliked', 'likes_count': comment.likes_count})

    @action(detail=False, methods=['get'], url_path='pending')
    def pending_comments(self, request):
        """کامنت‌های در انتظار تایید (فقط ادمین)"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        comments = Comment.objects.filter(status='pending')
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """تایید کامنت (فقط ادمین)"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        comment = self.get_object()
        comment.status = 'approved'
        comment.save()
        return Response({'status': 'approved'})


class StoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای استوری‌ها"""
    serializer_class = StorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # فقط استوری‌های منقضی نشده
        from django.utils import timezone
        return Story.objects.filter(expires_at__gt=timezone.now()).order_by('-created_at')