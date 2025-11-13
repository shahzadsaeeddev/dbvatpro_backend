
from rest_framework.permissions import BasePermission
from .models import Users


class HasRolesManager(BasePermission):
    """
    Check if the user has any of the required AMP Roles
    """

    message = (
        "You do not have any Assets Management Roles, "
        "Please contact Keycloak Administrator to add roles into your Keycloak Account"
    )

    def has_permission(self, request, view):
        return request.user.is_manager

# class HasUserRols(BasePermission):
#     """
#     Check if the user has any of the required AMP Roles
#     """
#
#     message = (
#         "You do not have any Assets Management Roles, "
#         "Please contact Keycloak Administrator to add roles into your Keycloak Account"
#     )
#
#     def has_permission(self, request, view):
#         if request.method == 'POST':
#             return request.user.is_create
#         elif request.method in ['PUT', 'PATCH', 'DELETE']:
#             return request.user.is_manage
#         elif request.method == 'GET':
#             return request.user.is_view
#         return False


class HasDashboardRole(BasePermission):
    """
    Check if the user has any of the required AMP Roles
    """

    message = (
        "You do not have any Assets Management Roles, "
        "Please contact Keycloak Administrator to add roles into your Keycloak Account"
    )

    def has_permission(self, request, view):
        if request.method == 'GET':
            return request.user.is_dashboard

        return False


class HasTechnicianRole(BasePermission):
    """
       Check if the user has any of the required AMP Roles
       """

    message = (
        "You do not have any Assets Management Roles, "
        "Please contact Keycloak Administrator to add roles into your Keycloak Account"
    )

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.is_can_create_technician
        elif request.method in ['PUT', 'PATCH']:
            return request.user.is_can_manage_technician
        elif request.method == 'DELETE':
            return request.user.is_can_manage_technician
        elif request.method == 'GET':
            return request.user.is_can_view_technician

        return False

class HasServicesRole(BasePermission):
    """
       Check if the user has any of the required AMP Roles
       """

    message = (
        "You do not have any Assets Management Roles, "
        "Please contact Keycloak Administrator to add roles into your Keycloak Account"
    )

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.can_create_service
        elif request.method in ['PUT', 'PATCH']:
            return request.user.can_manage_service
        elif request.method == 'DELETE':
            return request.user.can_manage_service
        elif request.method == 'GET':
            return request.user.can_view_service

        return False

class HasClientRole(BasePermission):
    """
       Check if the user has any of the required AMP Roles
       """

    message = (
        "You do not have any Assets Management Roles, "
        "Please contact Keycloak Administrator to add roles into your Keycloak Account"
    )

    def has_permission(self, request, view):
        if request.method == 'GET':
            return request.user.is_client_view

        return False

class HasJobRequestRole(BasePermission):
    """
       Check if the user has any of the required AMP Roles
       """

    message = (
        "You do not have any Assets Management Roles, "
        "Please contact Keycloak Administrator to add roles into your Keycloak Account"
    )

    def has_permission(self, request, view):
        if request.method == 'GET':
            return request.user.can_view_job_requests

        return False



class HasPaymentRole(BasePermission):
    """
       Check if the user has any of the required AMP Roles
       """

    message = (
        "You do not have any Assets Management Roles, "
        "Please contact Keycloak Administrator to add roles into your Keycloak Account"
    )

    def has_permission(self, request, view):
        if request.method == 'GET':
            return request.user.can_view_payments

        return False




