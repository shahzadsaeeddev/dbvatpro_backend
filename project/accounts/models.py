import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models

from utility.modelMixins import TimeStampMixins


class RoleGroup(TimeStampMixins):
    group_name = models.CharField(max_length=50, blank=False, null=False)
    group_code = models.CharField(max_length=150, default="",blank=False, null=False)
    visible = models.BooleanField(default=False)
    company=models.ForeignKey("api.Company",blank=True, null=True, on_delete=models.CASCADE)


    def __str__(self):
        return self.group_name


class Users(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    keycloak_uuid = models.CharField(max_length=136, blank=False, null=False)
    is_owner = models.BooleanField(default=False)
    user_roles = models.ForeignKey(RoleGroup, blank=True, null=True, on_delete=models.SET_NULL)
    company=  models.OneToOneField("api.Company", blank=True, null=True, on_delete=models.SET_NULL)
    application_roles = ArrayField(models.CharField(
        blank=True,
        null=True, max_length=50
    ),
        size=100, default=list
    )
    is_delete = models.BooleanField(default=False)

    @property
    def is_manager(self):
        return "PERMISSIONS_CAN_LOGIN" in self.application_roles

    @property
    def is_admin(self):
        return "IS_ADMIN" in self.application_roles

    @property
    def is_developer(self):
        return "IS_TECHNICIAN" in self.application_roles




