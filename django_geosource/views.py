from rest_framework.viewsets import ModelViewSet

from .models import SourceModel
from .serializers import SourceModelSerializer

class SourceModelViewset(ModelViewSet):
    model = SourceModel
    serializer_class = SourceModelSerializer
    authentication_classes = ()

    def get_queryset(self):
        return self.model.objects.all()