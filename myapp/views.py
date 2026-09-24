from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .filters import (
    filter_channels, filter_chats, filter_contacts, filter_groups, filter_media,
    filter_messages, filter_notifications, filter_stories, filter_story_views,
    search_channels, search_chats, search_contacts, search_groups, search_messages,
    search_notifications, search_stories,
)
from .models import (
    Block, Chat, ChatMember, Channel, Contact, Group, Media, Message,
    Notification, Story, StoryView,
)
from .pagination import CustomPagination
from .permissions import IsChatAdmin, IsMediaSender, IsOwner, IsSender
from .serializers import (
    BlockSerializer, ChannelSerializer, ChatMemberSerializer, ChatSerializer,
    ContactSerializer, GroupSerializer, MediaSerializer, MemberActionSerializer,
    MessageSerializer, NotificationSerializer, StorySerializer, StoryViewSerializer,
)

class ChatListCreate(generics.ListCreateAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Chat.objects.none()
        queryset = Chat.objects.filter(members__user=self.request.user).distinct()
        queryset = filter_chats(queryset, self.request.query_params)
        queryset = search_chats(queryset, self.request.query_params)
        return queryset

    def perform_create(self, serializer):
        chat = serializer.save()
        ChatMember.objects.create(chat=chat, user=self.request.user, is_admin=True)
        if chat.chat_type == 'group':
            Group.objects.create(chat=chat, name=chat.title or f'Group {chat.pk}')
        elif chat.chat_type == 'channel':
            Channel.objects.create(chat=chat, name=chat.title or f'Channel {chat.pk}')

class ChatDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated, IsChatAdmin]

class ChatMembers(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        chat = get_object_or_404(Chat, pk=pk, members__user=request.user)
        return Response(ChatMemberSerializer(chat.members.all(), many=True).data)
    
class AddMember(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MemberActionSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def post(self, request, pk):
        chat = get_object_or_404(Chat, pk=pk, members__user=request.user)
        if not IsChatAdmin().has_object_permission(request, self, chat):
            return Response({'detail': 'Only chat admins can add members'}, status=status.HTTP_403_FORBIDDEN)
        serializer = MemberActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data['user_id']
        member, created = ChatMember.objects.get_or_create(chat=chat, user_id=user_id)
        if created:
            Notification.objects.create(
                user=member.user, notification_type='added_to_chat',
                text=f'You were added to {chat}',
            )
        return Response(ChatMemberSerializer(member).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class RemoveMember(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MemberActionSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def post(self, request, pk):
        chat = get_object_or_404(Chat, pk=pk, members__user=request.user)
        if not IsChatAdmin().has_object_permission(request, self, chat):
            return Response({'detail': 'Only chat admins can remove members'}, status=status.HTTP_403_FORBIDDEN)
        serializer = MemberActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data['user_id']
        ChatMember.objects.filter(chat=chat, user_id=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LeaveChat(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        chat = get_object_or_404(Chat, pk=pk, members__user=request.user)
        ChatMember.objects.filter(chat=chat, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MessageListCreate(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()
        queryset = Message.objects.filter(chat__members__user=self.request.user, is_deleted=False).distinct()
        queryset = filter_messages(queryset, self.request.query_params)
        queryset = search_messages(queryset, self.request.query_params)
        return queryset

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class MessageDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Message.objects.filter(is_deleted=False)
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsSender]

    def perform_update(self, serializer):
        serializer.save(is_edited=True)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])

class MediaListCreate(generics.ListCreateAPIView):
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Media.objects.none()
        queryset = Media.objects.filter(message__chat__members__user=self.request.user).distinct()
        queryset = filter_media(queryset, self.request.query_params)
        return queryset

class MediaDetail(generics.RetrieveDestroyAPIView):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated, IsMediaSender]

class GroupList(generics.ListAPIView):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Group.objects.none()
        queryset = Group.objects.filter(chat__members__user=self.request.user).distinct()
        queryset = filter_groups(queryset, self.request.query_params)
        queryset = search_groups(queryset, self.request.query_params)
        return queryset

class GroupDetail(generics.RetrieveUpdateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsChatAdmin]

class ChannelList(generics.ListAPIView):
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    def get_queryset(self):
        queryset = Channel.objects.all()
        queryset = filter_channels(queryset, self.request.query_params)
        queryset = search_channels(queryset, self.request.query_params)
        return queryset

class ChannelDetail(generics.RetrieveUpdateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated, IsChatAdmin]

class ChannelSubscribers(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        channel = get_object_or_404(Channel, pk=pk)
        return Response(ChatMemberSerializer(channel.chat.members.all(), many=True).data)

class ChannelMessages(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        channel = get_object_or_404(Channel, pk=pk)
        queryset = Message.objects.filter(chat=channel.chat, is_deleted=False)
        return Response(MessageSerializer(queryset, many=True).data)

class SubscribeChannel(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        channel = get_object_or_404(Channel, pk=pk)
        member, created = ChatMember.objects.get_or_create(chat=channel.chat, user=request.user)
        return Response(ChatMemberSerializer(member).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class UnsubscribeChannel(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        channel = get_object_or_404(Channel, pk=pk)
        ChatMember.objects.filter(chat=channel.chat, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class NotificationList(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        queryset = Notification.objects.filter(user=self.request.user)
        queryset = filter_notifications(queryset, self.request.query_params)
        queryset = search_notifications(queryset, self.request.query_params)
        return queryset

class MarkNotificationRead(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data)

class MarkAllNotificationsRead(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        Notification.objects.filter(user=request.user).update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ContactListCreate(generics.ListCreateAPIView):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Contact.objects.none()
        queryset = Contact.objects.filter(user=self.request.user)
        queryset = filter_contacts(queryset, self.request.query_params)
        queryset = search_contacts(queryset, self.request.query_params)
        return queryset
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ContactDetail(generics.DestroyAPIView):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Contact.objects.none()
        return Contact.objects.filter(user=self.request.user)

class BlockListCreate(generics.ListCreateAPIView):
    serializer_class = BlockSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Block.objects.none()
        return Block.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BlockDetail(generics.DestroyAPIView):
    serializer_class = BlockSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Block.objects.none()
        return Block.objects.filter(user=self.request.user)

class UnblockUser(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, user_id):
        deleted, _ = Block.objects.filter(user=request.user, blocked_user_id=user_id).delete()
        if not deleted:
            return Response({'detail': 'Block not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

class StoryListCreate(generics.ListCreateAPIView):
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Story.objects.none()
        queryset = Story.objects.filter(is_active=True, expires_at__gt=timezone.now())
        queryset = queryset.exclude(user__blocked_users__blocked_user=self.request.user)
        queryset = filter_stories(queryset, self.request.query_params)
        queryset = search_stories(queryset, self.request.query_params)
        return queryset
    def perform_create(self, serializer):
        expires_at = serializer.validated_data.get('expires_at') or (timezone.now() + timedelta(hours=24))
        serializer.save(user=self.request.user, expires_at=expires_at)

class StoryDetail(generics.RetrieveDestroyAPIView):
    queryset = Story.objects.all()
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [permissions.IsAuthenticated(), IsOwner()]
        return [permissions.IsAuthenticated()]

class MyStories(generics.ListAPIView):
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Story.objects.none()
        return Story.objects.filter(user=self.request.user)

class ViewStory(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        story = get_object_or_404(Story, pk=pk)
        story_view, created = StoryView.objects.get_or_create(story=story, user=request.user)
        return Response(StoryViewSerializer(story_view).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class StoryViewers(generics.ListAPIView):
    serializer_class = StoryViewSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return StoryView.objects.none()
        story = get_object_or_404(Story, pk=self.kwargs['pk'], user=self.request.user)
        queryset = StoryView.objects.filter(story=story)
        queryset = filter_story_views(queryset, self.request.query_params)
        return queryset