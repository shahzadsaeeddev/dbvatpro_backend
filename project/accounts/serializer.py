import json

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .keycloak import create_user, update_user, update_role, deactivate_user, reset_password_user
from .models import RoleGroup, Users


class KeycloakTokenSerializer(serializers.Serializer):
    """
    KeycloakTokenSerializer
    Used to retrieve a token from keycloak using basic auth
    """

    username = serializers.CharField(max_length=200, required=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class KeycloakRefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(max_length=2500, required=True)


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleGroup
        fields = ['id', 'group_name']



class UsersSerializer(serializers.ModelSerializer):
    access_role = serializers.CharField(source='user_roles', read_only=True)
    uuid = serializers.CharField(source='id', read_only=True)

    class Meta:
        model = Users
        fields = ['first_name', 'last_name', 'email', 'password', 'access_role', 'user_roles', 'username',
                  'uuid', 'company']
        # extra_kwargs = {
        #     'user_roles': {'write_only': True},
        #     'password': {'write_only': True},
        # }

    def create(self, validated_data):
        request = self.context.get('request')
        auth_token = None

        if request and hasattr(request, 'META'):
            auth_token = request.META.get('HTTP_AUTHORIZATION')
        if auth_token and auth_token.startswith('Bearer '):
            auth_token = auth_token.split(' ')[1]
            response, code = create_user(auth_token, **validated_data)
            if response.status_code != 201:
                raise ValidationError(json.loads(response.text))
            else:
                user = Users.objects.create(**validated_data, keycloak_uuid=code)

                return user

        raise ValidationError("Authorization token is missing or invalid.")



class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id', 'email', 'username',]


class TechnicianListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id', 'username',]




class UsersDetailSerializer(serializers.ModelSerializer):
    access_role = serializers.CharField(source='user_roles', read_only=True)
    uuid = serializers.CharField(source='id', read_only=True)
    scope = serializers.CharField(write_only=True)
    filter = serializers.CharField(source='user_roles.id', read_only=True)


    class Meta:
        model = Users
        fields = ['scope', 'first_name', 'last_name', 'username', 'email', 'access_role', 'user_roles', 'password',
                  'uuid', 'filter']
        # extra_kwargs = {
        #     'user_roles': {'write_only': True},
        #     'password': {'write_only': True}
        # }




        def update(self, instance, validated_data):
            scope = validated_data.pop('scope', None)
            #print(validated_data)
            if scope is None:
                raise ValidationError({"errorMessage": "Missing 'scope' in request data"})

            allowed_branches = validated_data.pop('allowed_branches', None)

            request = self.context.get('request')
            if request and hasattr(request, 'META'):
                auth_token = request.META.get('HTTP_AUTHORIZATION')
            else:
                auth_token = None

            if auth_token and auth_token.startswith('Bearer '):
                auth_token = auth_token.split(' ')[1]

                if scope == 'update_profile':
                    response = update_user(auth_token, instance.keycloak_uuid, **validated_data)
                    if response.status_code != 204:
                        raise ValidationError(json.loads(response.text))
                elif scope == 'update_password':
                    response = reset_password_user(auth_token, instance.keycloak_uuid, **validated_data)
                    if response.status_code != 204:
                        raise ValidationError(json.loads(response.text))
                elif scope == 'update_role':
                    assigned = validated_data['user_roles'].group_code
                    default = instance.user_roles.group_code
                    update_role(auth_token, instance.keycloak_uuid, default, assigned)
                elif scope == 'update_status':
                    response = deactivate_user(auth_token, instance.keycloak_uuid, validated_data['status'])
                    if response.status_code != 204:
                        raise ValidationError(json.loads(response.text))
                else:
                    raise ValidationError({"errorMessage": "Invalid scope value"})

                for attr, value in validated_data.items():
                    setattr(instance, attr, value)

                instance.save()
                if allowed_branches is not None:
                    instance.allowed_branches.set(allowed_branches)

                return instance
            else:
                raise ValidationError({"errorMessage": "Invalid or missing authorization token"})

