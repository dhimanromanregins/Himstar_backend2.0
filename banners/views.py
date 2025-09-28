from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import BannerOrVideo
from dashboard.models import Category
from .serializers import BannerOrVideoSerializer
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class BannersByCategoryAPIView(APIView):
    """
    Banners API
    
    Retrieves all banners and videos for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get all banners and videos",
        responses={
            200: openapi.Response(
                description="Banners retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'banners': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                description='Banner/Video object'
                            )
                        )
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
                        'details': openapi.Schema(type=openapi.TYPE_STRING, description='Error details'),
                    }
                )
            )
        },
        tags=['Banners']
    )
    def get(self, request):
        try:
            banners = BannerOrVideo.objects.all()

            # Serialize the data
            serializer = BannerOrVideoSerializer(banners, many=True)

            # Return a JSON response with serialized data
            return Response({
                'banners': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Generic exception handler for other unexpected errors
            return Response(
                {'error': 'An error occurred while retrieving banners.', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )