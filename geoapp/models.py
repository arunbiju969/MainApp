from django.db import models


class GeoServerWorkspace(models.Model):
    """Represents a workspace in GeoServer"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class GeoServerLayer(models.Model):
    """Represents a layer in GeoServer"""

    name = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    workspace = models.ForeignKey(GeoServerWorkspace, on_delete=models.CASCADE)
    layer_name = models.CharField(max_length=100)
    is_visible = models.BooleanField(default=True)
    layer_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.workspace.name}:{self.layer_name})"

    @property
    def wms_url(self):
        from django.conf import settings

        return f"{settings.GEOSERVER_URL}/{self.workspace.name}/wms"

    class Meta:
        ordering = ["layer_order"]
