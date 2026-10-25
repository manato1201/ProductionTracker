from rest_framework.response import Response
from rest_framework.views import APIView

from . import ingest
from . import serializers as s
from .auth import IngestApiKeyAuthentication
from .permissions import IsIngestClient


class IngestBase(APIView):
    """X-API-Key 専用。セッション・トークンでは呼べず、CSRF の対象にもならない。"""

    authentication_classes = [IngestApiKeyAuthentication]
    permission_classes = [IsIngestClient]


class QualityIngestView(IngestBase):
    def post(self, request):
        body = s.QualityIngestSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        d = body.validated_data
        summary = ingest.ingest_quality(d["project"], d["scan_run_id"], d["scanned_at"], d["results"])
        return Response(summary, status=201 if summary["created"] else 200)


class VisualIngestView(IngestBase):
    def post(self, request):
        body = s.VisualIngestSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        d = body.validated_data
        result, created = ingest.ingest_visual(**d)
        return Response(s.VisualResultSerializer(result).data, status=201 if created else 200)
