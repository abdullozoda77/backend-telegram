def filter_chats(queryset, params):
    chat_type = params.get('chat_type')
    title = params.get('title')

    if chat_type:
        queryset = queryset.filter(chat_type=chat_type)
    if title:
        queryset = queryset.filter(title__icontains=title)
    return queryset

def search_chats(queryset, params):
    query = params.get('search')

    if query:
        queryset = queryset.filter(title__icontains=query)
    return queryset

def filter_messages(queryset, params):
    chat = params.get('chat')
    sender = params.get('sender')
    text = params.get('text')
    is_edited = params.get('is_edited')
    message_type = params.get('message_type')

    if chat:
        queryset = queryset.filter(chat_id=chat)
    if sender:
        queryset = queryset.filter(sender_id=sender)
    if text:
        queryset = queryset.filter(text__icontains=text)
    if is_edited:
        queryset = queryset.filter(is_edited=is_edited)
    if message_type:
        queryset = queryset.filter(message_type=message_type)
    return queryset

def search_messages(queryset, params):
    query = params.get('search')

    if query:
        queryset = queryset.filter(text__icontains=query)
    return queryset

def filter_media(queryset, params):
    message = params.get('message')
    media_type = params.get('media_type')

    if message:
        queryset = queryset.filter(message_id=message)
    if media_type:
        queryset = queryset.filter(media_type=media_type)
    return queryset

def filter_groups(queryset, params):
    name = params.get('name')

    if name:
        queryset = queryset.filter(name__icontains=name)
    return queryset

def search_groups(queryset, params):
    query = params.get('search')

    if query:
        queryset = queryset.filter(name__icontains=query) | queryset.filter(description__icontains=query)
    return queryset

def filter_channels(queryset, params):
    name = params.get('name')
    username = params.get('username')

    if name:
        queryset = queryset.filter(name__icontains=name)
    if username:
        queryset = queryset.filter(username__icontains=username)
    return queryset

def search_channels(queryset, params):
    query = params.get('search')

    if query:
        queryset = (
            queryset.filter(name__icontains=query)
            | queryset.filter(username__icontains=query)
            | queryset.filter(description__icontains=query)
        )
    return queryset

def filter_notifications(queryset, params):
    notification_type = params.get('notification_type')
    is_read = params.get('is_read')

    if notification_type:
        queryset = queryset.filter(notification_type=notification_type)
    if is_read:
        queryset = queryset.filter(is_read=is_read)
    return queryset

def search_notifications(queryset, params):
    query = params.get('search')

    if query:
        queryset = queryset.filter(text__icontains=query)
    return queryset

def filter_contacts(queryset, params):
    nickname = params.get('nickname')

    if nickname:
        queryset = queryset.filter(nickname__icontains=nickname)
    return queryset

def search_contacts(queryset, params):
    query = params.get('search')

    if query:
        queryset = queryset.filter(nickname__icontains=query)
    return queryset

def filter_stories(queryset, params):
    user = params.get('user')
    is_active = params.get('is_active')

    if user:
        queryset = queryset.filter(user_id=user)
    if is_active:
        queryset = queryset.filter(is_active=is_active)
    return queryset

def search_stories(queryset, params):
    query = params.get('search')

    if query:
        queryset = queryset.filter(caption__icontains=query)
    return queryset

def filter_story_views(queryset, params):
    story = params.get('story')
    user = params.get('user')

    if story:
        queryset = queryset.filter(story_id=story)
    if user:
        queryset = queryset.filter(user_id=user)
    return queryset