from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

from .models import User
from api.permissions import AdminPermission
from .serializers import (UserSerializer,
                          FullUserSerializer,
                          TokenSerializer,
                          PatchUserSerializer)


class PageNumberPaginationWithEmpty(PageNumberPagination):
    page_size = 1


def assert_required_fields_in_response(response_data, required_fields):

    for field in required_fields:
        assert field in response_data,\
            f'{field} is missing from the response data.'


@method_decorator(csrf_protect, name='dispatch')
class SignupView(generics.GenericAPIView):

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        if username == 'me':
            return Response({'field_name': ['username']},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(username=username, email=email)
            serializer = UserSerializer(user, data=request.data, partial=True)
        except User.DoesNotExist:
            user = None
            serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            confirmation_code = User.objects.make_random_password(length=6)
            serializer.save(confirmation_code=confirmation_code)

            send_mail(
                'Confirm your account',
                f'Your confirmation code is: {confirmation_code}',
                settings.EMAIL_HOST_USER,
                [serializer.data['email']],
                fail_silently=False,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_protect, name='dispatch')
class TokenView(generics.GenericAPIView):

    def post(self, request):
        username = request.data.get('username')
        confirmation_code = request.data.get('confirmation_code')

        serializer = TokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        # Authenticate user using confirmation code
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response('No user', status=status.HTTP_404_NOT_FOUND)
        if not user.check_confirmation_code(confirmation_code):
            return Response({'error': 'Invalid confirmation code.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        return Response({'token': access})


@method_decorator(csrf_protect, name='dispatch')
class ProfileManage(GenericAPIView):
    permission_classes = [AdminPermission]
    pagination_class = PageNumberPaginationWithEmpty

    def get(self, request):
        username = request.query_params.get('search', None)
        if username is None:
            users = User.objects.all()
        else:
            users = User.objects.filter(username=username)
        page = self.paginate_queryset(users)
        serializer = FullUserSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = FullUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_protect, name='dispatch')
class ProfileActions(APIView):
    def get_permissions(self):
        if self.kwargs.get('username', '') == 'me':
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AdminPermission]

        return super().get_permissions()

    def get(self, request, username):
        try:
            if username == 'me':
                user = request.user
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response('User not found', status=status.HTTP_404_NOT_FOUND)

        serializer = FullUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, username):
        if username == 'me':
            user = request.user
            serializer = PatchUserSerializer(user,
                                             data=request.data,
                                             partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            user = User.objects.get(username=username)
            serializer = FullUserSerializer(user,
                                            data=request.data,
                                            partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, username):
        if username == 'me':
            return Response('Method not allowed',
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        user = get_object_or_404(User, username=username)

        user.delete()
        return Response('User deleted', status=status.HTTP_204_NO_CONTENT)
