import json
import os

import requests
from django.db.models import Q

from django.conf import settings
from rest_framework import permissions, generics, filters

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .keycloak import update_user, reset_password_user
from .models import RoleGroup, Users
from .serializer import KeycloakTokenSerializer, UserRoleSerializer, UsersSerializer, KeycloakRefreshTokenSerializer, \
    UsersDetailSerializer, UserListSerializer, TechnicianListSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class GetKeycloakToken(ObtainAuthToken):
    permission_classes = ()
    serializer_class = KeycloakTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        base = settings.OIDC_HOST
        realm = settings.OIDC_REALM

        url = f"{base}/realms/{realm}/protocol/openid-connect/token"
        data = {
            "grant_type": "password",
            "client_id": settings.OIDC_RP_CLIENT_ID,
            "username": username,
            "password": password,
            "client_secret": settings.OIDC_RP_CLIENT_SECRET
        }

        response = requests.request("post", url, data=data)
        data = response.content.decode("utf-8")
        data = json.loads(data)

        token = data.get("access_token", None)
        refresh_token = data.get("refresh_token", None)
        if not token:
            return Response(data)
        return Response({
            "token": f"Bearer {token}",
            "refresh_token": refresh_token
        })


class GetKeycloakRefresh(ObtainAuthToken):
    permission_classes = ()
    serializer_class = KeycloakRefreshTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # Use refresh token instead of username and password
        refresh_token = serializer.validated_data["refresh_token"]

        base = settings.OIDC_HOST
        realm = settings.OIDC_REALM

        url = f"{base}/realms/{realm}/protocol/openid-connect/token"
        data = {
            "grant_type": "refresh_token",  # Changed grant_type to refresh_token
            "client_id": settings.OIDC_RP_CLIENT_ID,
            "refresh_token": refresh_token,
            "client_secret": settings.OIDC_RP_CLIENT_SECRET
        }
        response = requests.post(url, data=data)  # Changed to use requests.post for clarity
        data = response.json()  # Directly parsing JSON from response

        token = data.get("access_token", None)
        refresh_token = data.get("refresh_token", None)
        if not token:
            return Response(data)
        return Response({
            "token": f"Bearer {token}",
            "refresh_token": refresh_token
        })


class UserRolesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserRoleSerializer

    def get_queryset(self):
        query = RoleGroup.objects.filter(visible=True)
        return query


class UserRolesListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserRoleSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        query = RoleGroup.objects.filter(visible=True)
        return query


class UserView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UsersSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']

    # def get_queryset(self):
    #     return Users.objects.filter(company=self.request.user.company)
    #
    # def perform_create(self, serializer):
    #     user = self.request.user
    #     serializer.save(company=self.request.user.company)


class TechnicianListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TechnicianListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']

    def get_queryset(self):
        roles = RoleGroup.objects.filter(Q(group_name='technician') | Q(group_name='Technician'))
        return Users.objects.filter(user_roles__in=roles)



class UserListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserListSerializer
    queryset = Users.objects.all()
    # pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UsersDetailSerializer
    queryset = Users.objects.all()
    lookup_field = 'pk'

    # def get_queryset(self):
    #     return Users.objects.filter(company=self.request.user.company)




class UserProfileView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = Users.objects.filter(username=self.request.user.username).first()
        slz_data = UsersDetailSerializer(user)
        return Response(data=slz_data.data, status=200)

    def patch(self, request, *args, **kwargs):
        auth_header = self.request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

        scope = self.request.data.get('scope')
        if scope == 'update_profile':
            self.request.data.pop('scope', None)

            display_picture_id = self.request.data.pop('display_picture', None)

            Users.objects.filter(username=self.request.user.username).update(**self.request.data)

            # if display_picture_id:
            #     gallery_item = Gallery.objects.filter(id=display_picture_id).first()
            #     if gallery_item:
            #         file = gallery_item.pic.url if gallery_item.pic else None
            #         self.request.data["display_picture"] = os.path.join("https://api.diamondbox.me/", str(file))
            #
            # response = update_user(token, self.request.user.keycloak_uuid, **self.request.data)
            # if response.status_code != 204:
            #     raise ValidationError(json.loads(response.text))

        elif scope == 'update_password':
            if 'password' not in self.request.data:
                raise ValidationError("Password field is required for updating password")

            response = reset_password_user(token, self.request.user.keycloak_uuid, **self.request.data)
            if response.status_code != 204:
                raise ValidationError(json.loads(response.text))

        else:
            return Response(data={"message": "Invalid scope value", "status": 400}, status=400)

        return Response(data={"message": "Success", "status": 200}, status=200)
