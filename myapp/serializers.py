import re

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import (
    Chat, ChatMember, Message, Media, Group, Channel,
    Notification, Contact, Block, Story, StoryView,
)

User = get_user_model()


class MemberActionSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError("User with this id does not exist.")
        return value


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ["id", "chat_type", "title", "photo", "created_at", "updated_at"]

    def validate_title(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Title cannot be blank spaces.")
        return value.strip() if value else value


class ChatMemberSerializer(serializers.ModelSerializer):
    chat = ChatSerializer(read_only=True)
    chat_id = serializers.PrimaryKeyRelatedField(queryset=Chat.objects.all(), source="chat", write_only=True)
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="user", write_only=True)

    class Meta:
        model = ChatMember
        fields = ["id", "chat", "chat_id", "user", "user_id", "is_admin", "joined_at"]


class MessageSerializer(serializers.ModelSerializer):
    chat = ChatSerializer(read_only=True)
    chat_id = serializers.PrimaryKeyRelatedField(queryset=Chat.objects.all(), source="chat", write_only=True)
    sender = UserSerializer(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="sender", write_only=True, required=False
    )
    is_edited = serializers.BooleanField(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)

    class Meta:
        model = Message
        fields = [
            "id", "chat", "chat_id", "sender", "sender_id", "message_type",
            "text", "created_at", "is_edited", "is_deleted",
        ]

    def validate(self, attrs):
        message_type = attrs.get('message_type', getattr(self.instance, 'message_type', 'text'))
        text = attrs.get('text', getattr(self.instance, 'text', ''))
        if message_type == 'text' and (not text or not text.strip()):
            raise serializers.ValidationError({'text': 'Message text cannot be empty.'})
        return attrs


class MediaSerializer(serializers.ModelSerializer):
    message = MessageSerializer(read_only=True)
    message_id = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all(), source="message", write_only=True)

    class Meta:
        model = Media
        fields = ["id", "message", "message_id", "media_type", "file", "created_at"]

    def validate_message_id(self, value):
        request = self.context.get("request")
        if request and value.sender != request.user:
            raise serializers.ValidationError("You can only attach media to your own messages.")
        return value


class GroupSerializer(serializers.ModelSerializer):
    chat = ChatSerializer(read_only=True)
    chat_id = serializers.PrimaryKeyRelatedField(queryset=Chat.objects.all(), source="chat", write_only=True)

    class Meta:
        model = Group
        fields = ["id", "chat", "chat_id", "name", "description", "photo", "created_at", "updated_at"]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Group name cannot be blank.")
        return value.strip()


class ChannelSerializer(serializers.ModelSerializer):
    chat = ChatSerializer(read_only=True)
    chat_id = serializers.PrimaryKeyRelatedField(queryset=Chat.objects.all(), source="chat", write_only=True)

    class Meta:
        model = Channel
        fields = ["id", "chat", "chat_id", "name", "username", "description", "photo", "created_at", "updated_at"]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Channel name cannot be blank.")
        return value.strip()

    def validate_username(self, value):
        if value and not re.fullmatch(r'[A-Za-z0-9_]{5,32}', value):
            raise serializers.ValidationError(
                "Username must be 5-32 characters long and contain only letters, digits and underscores."
            )
        return value

class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="user", write_only=True)
    message = MessageSerializer(read_only=True)
    message_id = serializers.PrimaryKeyRelatedField(
        queryset=Message.objects.all(), source="message", write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Notification
        fields = ["id", "user", "user_id", "message", "message_id", "notification_type", "text", "is_read", "created_at"]


class ContactSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", write_only=True, required=False
    )
    contact_user = UserSerializer(read_only=True)
    contact_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="contact_user", write_only=True
    )

    class Meta:
        model = Contact
        fields = ["id", "user", "user_id", "contact_user", "contact_user_id", "nickname", "created_at"]

    def validate(self, attrs):
        user = attrs.get("user") or getattr(self.instance, "user", None) or getattr(self.context.get("request"), "user", None)
        contact_user = attrs.get("contact_user") or getattr(self.instance, "contact_user", None)
        if user and contact_user and user == contact_user:
            raise serializers.ValidationError({"contact_user_id": "You cannot add yourself as a contact."})
        return attrs

class BlockSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", write_only=True, required=False
    )
    blocked_user = UserSerializer(read_only=True)
    blocked_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="blocked_user", write_only=True
    )

    class Meta:
        model = Block
        fields = ["id", "user", "user_id", "blocked_user", "blocked_user_id", "created_at"]

    def validate(self, attrs):
        user = attrs.get("user") or getattr(self.instance, "user", None) or getattr(self.context.get("request"), "user", None)
        blocked_user = attrs.get("blocked_user") or getattr(self.instance, "blocked_user", None)
        if user and blocked_user and user == blocked_user:
            raise serializers.ValidationError({"blocked_user_id": "You cannot block yourself."})
        return attrs

class StorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", write_only=True, required=False
    )
    expires_at = serializers.DateTimeField(required=False)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Story
        fields = ["id", "user", "user_id", "media", "caption", "created_at", "expires_at", "is_active"]

    def validate_expires_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Expiration time must be in the future.")
        return value

class StoryViewSerializer(serializers.ModelSerializer):
    story = StorySerializer(read_only=True)
    story_id = serializers.PrimaryKeyRelatedField(queryset=Story.objects.all(), source="story", write_only=True)
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="user", write_only=True)

    class Meta:
        model = StoryView
        fields = ["id", "story", "story_id", "user", "user_id", "viewed_at"]