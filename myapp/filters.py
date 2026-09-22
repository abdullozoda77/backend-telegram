def filter_transactions(queryset, params):
    type_ = params.get('type')
    status_ = params.get('status')
    date_from = params.get('date_from')
    date_to = params.get('date_to')

    if type_:
        queryset = queryset.filter(type=type_)
    if status_:
        queryset = queryset.filter(status=status_)
    if date_from:
        queryset = queryset.filter(created_at__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__lte=date_to)
    return queryset
