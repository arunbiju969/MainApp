from django.shortcuts import render
from django.conf import settings
from .models import GeoServerLayer, GeoServerWorkspace


def default_map(request):
    """View for the main map page"""
    layers = GeoServerLayer.objects.filter(is_visible=True)
    workspaces = GeoServerWorkspace.objects.all()

    context = {
        "geoserver_url": settings.GEOSERVER_URL,
        "layers": layers,
        "workspaces": workspaces,
    }

    return render(request, "geoapp/map.html", context)
