from rest_framework.decorators import detail_route
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status

from .models import Source
from .parsers import NestedMultipartJSONParser
from .permissions import SourcePermission
from .serializers import SourceSerializer


class SourceModelViewset(ModelViewSet):
    model = Source
    parser_classes = (JSONParser, NestedMultipartJSONParser)
    serializer_class = SourceSerializer
    permission_classes = (SourcePermission, )

    def get_queryset(self):
        return self.model.objects.all()

    @detail_route(methods=['get', ])
    def refresh(self, request, pk):
        source = self.get_object()

        refresh_job = source.run_async_method('refresh_data')
        if refresh_job:
            source.status = refresh_job.task_id
            source.save()

            return Response(
                        data=self.serializer_class().get_status(source),
                        status=status.HTTP_202_ACCEPTED
                    )

        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
