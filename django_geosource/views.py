from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Source
from .parsers import NestedMultipartJSONParser
from .permissions import SourcePermission
from .serializers import SourceSerializer


class SourceModelViewset(ModelViewSet):
    model = Source
    parser_classes = (JSONParser, NestedMultipartJSONParser)
    serializer_class = SourceSerializer
    permission_classes = (SourcePermission,)
    ordering_fields = (
        "name",
        "polymorphic_ctype__model",
        "geom_type",
        "id",
        "slug",
    )
    filter_fields = (
        "polymorphic_ctype",
        "geom_type",
    )
    search_fields = ["name"]

    def get_queryset(self):
        return self.model.objects.all()

    @action(detail=True, methods=["get"])
    def refresh(self, request, pk):
        """Schedule a refresh now"""

        source = self.get_object()

        refresh_job = source.run_async_method("refresh_data")
        if refresh_job:
            return Response(data=source.get_status(), status=status.HTTP_202_ACCEPTED)

        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
