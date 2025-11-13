import uuid
from django.db import models


class TimeStampMixins(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CompanyMixins(TimeStampMixins):
    company = models.ForeignKey('api.Company', on_delete=models.SET_NULL, blank=True, null=True,
                                related_name="%(class)s_data")

    class Meta:
        abstract = True
