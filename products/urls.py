from rest_framework.routers import DefaultRouter
from .views import ProductCachePageViewSet, ProductViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="products")
router.register("products-cached", ProductCachePageViewSet, basename="products-cached")

urlpatterns = router.urls
