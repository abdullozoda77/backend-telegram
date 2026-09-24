from rest_framework.permissions import BasePermission

from .models import ChatMember


class IsChatAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'members'):
            chat = obj
        else:
            chat = obj.chat
        return ChatMember.objects.filter(chat=chat, user=request.user, is_admin=True).exists()

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsSender(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.sender == request.user

class IsMediaSender(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.message.sender == request.user