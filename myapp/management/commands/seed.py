from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from myapp.models import (
    Block, Chat, ChatMember, Channel, Contact, Group, Media, Message,
    Notification, Story, StoryView,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with one of everything: users, chats, messages, groups, channels, stories, etc."

    @transaction.atomic
    def handle(self, *args, **options):
        user1, _ = User.objects.get_or_create(username="seed_alice", defaults={"email": "alice@seed.local"})
        user1.set_password("SeedPass123!")
        user1.save()

        user2, _ = User.objects.get_or_create(username="seed_bob", defaults={"email": "bob@seed.local"})
        user2.set_password("SeedPass123!")
        user2.save()

        chat, _ = Chat.objects.get_or_create(chat_type="private", title="Seed Private Chat")
        ChatMember.objects.get_or_create(chat=chat, user=user1, defaults={"is_admin": True})
        ChatMember.objects.get_or_create(chat=chat, user=user2)

        message, _ = Message.objects.get_or_create(chat=chat, sender=user1, text="Hello from seed data")

        media, _ = Media.objects.get_or_create(
            message=message,
            media_type="file",
            defaults={"file": ContentFile(b"seed file contents", name="seed.txt")},
        )

        group_chat, _ = Chat.objects.get_or_create(chat_type="group", title="Seed Group")
        ChatMember.objects.get_or_create(chat=group_chat, user=user1, defaults={"is_admin": True})
        group, _ = Group.objects.get_or_create(chat=group_chat, defaults={"name": "Seed Group", "description": "A seeded group"})

        channel_chat, _ = Chat.objects.get_or_create(chat_type="channel", title="Seed Channel")
        ChatMember.objects.get_or_create(chat=channel_chat, user=user1, defaults={"is_admin": True})
        channel, _ = Channel.objects.get_or_create(
            chat=channel_chat, defaults={"name": "Seed Channel", "username": "seed_channel", "description": "A seeded channel"}
        )

        notification, _ = Notification.objects.get_or_create(
            user=user2, message=message,
            defaults={"notification_type": "message", "text": "You have a new message"},
        )

        contact, _ = Contact.objects.get_or_create(user=user1, contact_user=user2, defaults={"nickname": "Bob"})

        block, _ = Block.objects.get_or_create(user=user2, blocked_user=user1)

        story, _ = Story.objects.get_or_create(
            user=user1,
            defaults={
                "media": ContentFile(b"seed story contents", name="seed_story.txt"),
                "caption": "Seed story",
                "expires_at": timezone.now() + timedelta(hours=24),
            },
        )

        story_view, _ = StoryView.objects.get_or_create(story=story, user=user2)

        self.stdout.write(self.style.SUCCESS("Seeded:"))
        self.stdout.write(f"  users: {user1.username}, {user2.username} (password: SeedPass123!)")
        self.stdout.write(f"  chat: {chat} (id={chat.id})")
        self.stdout.write(f"  message: {message} (id={message.id})")
        self.stdout.write(f"  media: {media} (id={media.id})")
        self.stdout.write(f"  group: {group} (id={group.id})")
        self.stdout.write(f"  channel: {channel} (id={channel.id})")
        self.stdout.write(f"  notification: {notification} (id={notification.id})")
        self.stdout.write(f"  contact: {contact} (id={contact.id})")
        self.stdout.write(f"  block: {block} (id={block.id})")
        self.stdout.write(f"  story: {story} (id={story.id})")
        self.stdout.write(f"  story_view: {story_view} (id={story_view.id})")
