from rest_framework import routers

from .views import SourceModelViewset

app_name = 'geosource'

router = routers.SimpleRouter()

router.register(r'geosource', SourceModelViewset, base_name='geosource')

urlpatterns = router.urls
