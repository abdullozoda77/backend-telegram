from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Product
from .serializers import ProductSerializer

CACHE_TTL = 60  # seconds

class ProductViewSet(ModelViewSet):
    """Custom (manual) Redis caching: we choose the keys and clear the cache on every change."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def list(self, request, *args, **kwargs):
        cache_key = "products_list"
        data = cache.get(cache_key)

        if data is None:
            serializer = self.get_serializer(self.get_queryset(), many=True)
            data = serializer.data
            cache.set(cache_key, data, CACHE_TTL)

        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        cache_key = f"product_{pk}"
        data = cache.get(cache_key)

        if data is None:
            product = self.get_object()
            data = self.get_serializer(product).data
            cache.set(cache_key, data, CACHE_TTL)

        return Response(data)

    def perform_create(self, serializer):
        serializer.save()
        cache.clear()

    def perform_update(self, serializer):
        serializer.save()
        cache.clear()

    def perform_destroy(self, instance):
        instance.delete()
        cache.clear()

@method_decorator(cache_page(CACHE_TTL), name="list")
@method_decorator(cache_page(CACHE_TTL), name="retrieve")
class ProductCachePageViewSet(ModelViewSet):
    """Built-in Django caching: the whole response is cached, but it is NOT cleared on changes."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
