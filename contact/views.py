from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Contact
from accounts.models import Register
from .serializers import ContactSerializer
from rest_framework.permissions import IsAuthenticated


class ContactCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        user_id = Register.objects.filter(user=user.id).first()
        request.data['user'] = user_id.id
        serializer = ContactSerializer(data=request.data)
        print(serializer, '=========')
        if serializer.is_valid():
            serializer.save()  # Save the contact information to the database
            return Response({ "status":status.HTTP_201_CREATED,"message": "Contact information submitted successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserContactsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user.id
        user_id = Register.objects.filter(user=user).first()
        if not user_id:
            return Response({"error": "User ID not provided"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Filter contacts based on the provided user ID
            contacts = Contact.objects.filter(user=user_id.id)
            if contacts.exists():
                serializer = ContactSerializer(contacts, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "No contacts found for this user"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)