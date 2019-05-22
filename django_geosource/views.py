from rest_framework.decorators import detail_route
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status

from .models import Source
from .serializers import SourceSerializer



class SourceModelViewset(ModelViewSet):
    model = Source
    serializer_class = SourceSerializer
    authentication_classes = ()

    def get_queryset(self):
        return self.model.objects.all()

    @detail_route(methods=['get', ])
    def refresh(self, request, pk):
        source = self.get_object()

        if source.run_async_method('refresh_data'):
            return Response(status=status.HTTP_202_ACCEPTED)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
