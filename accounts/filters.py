def search_users(queryset, params):
    query = params.get('search')

    if query:
        queryset = queryset.filter(username__icontains=query) | queryset.filter(email__icontains=query)
    return queryset
