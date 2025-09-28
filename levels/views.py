from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Stage, Level
from .serializers import StageSerializer, LevelSerializer
from rest_framework.permissions import IsAuthenticated

class StageAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        stages = Stage.objects.all()
        serializer = StageSerializer(stages, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StageDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, pk):
        try:
            return Stage.objects.get(pk=pk)
        except Stage.DoesNotExist:
            return None

    def get(self, request, pk):
        stage = self.get_object(pk)
        if not stage:
            return Response({"error": "Stage not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = StageSerializer(stage)
        return Response(serializer.data)

    def put(self, request, pk):
        stage = self.get_object(pk)
        if not stage:
            return Response({"error": "Stage not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = StageSerializer(stage, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        stage = self.get_object(pk)
        if not stage:
            return Response({"error": "Stage not found"}, status=status.HTTP_404_NOT_FOUND)
        stage.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LevelAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        levels = Level.objects.all()
        serializer = LevelSerializer(levels, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = LevelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
