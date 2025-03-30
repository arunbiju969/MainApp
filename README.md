# GeoServer Django Integration

A lightweight Django application for creating interactive geospatial web maps using GeoServer and Leaflet. This project provides a modern, responsive UI built with Tailwind CSS and Flowbite to visualize and interact with GeoServer layers.

## 🌍 Features

- Interactive map interface with Leaflet.js
- GeoServer layer integration via WMS
- Layer visibility controls
- Multiple basemap options
- Responsive design with Tailwind CSS & Flowbite
- Admin interface for managing GeoServer layer metadata
- Vercel-friendly deployment configuration

## 🏗️ Architecture

This application uses a lightweight approach to geospatial web development:

1. **GeoServer**: Handles spatial data storage and OGC services (WMS, WFS)
2. **Django**: Manages application flow and stores layer metadata
3. **Leaflet**: Provides client-side map rendering and interaction
4. **Tailwind/Flowbite**: Delivers responsive, modern UI components

## 📋 Prerequisites

- Python 3.8+
- Django 5.1+
- GeoServer instance (accessible via HTTPS)
- Basic understanding of Django and GeoServer concepts

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/geoserver-django-integration.git
cd geoserver-django-integration
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure GeoServer settings

In settings.py, update your GeoServer URL and default workspace:

```python
GEOSERVER_URL = "https://your-geoserver-url.com/geoserver"
GEOSERVER_WORKSPACE = "your_workspace_name"
```

### 5. Run migrations and create superuser

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

### 7. Add GeoServer layers

Access the admin interface at http://localhost:8000/admin/ and:
- Add GeoServer workspaces
- Add GeoServer layers with appropriate workspace references

## 📊 Data Models

### GeoServerWorkspace
Represents a workspace in GeoServer:
- `name`: Workspace name (must match GeoServer workspace name)

### GeoServerLayer
Represents a layer in GeoServer:
- `name`: Internal identifier
- `title`: Human-readable title
- `workspace`: ForeignKey to GeoServerWorkspace
- `layer_name`: Exact layer name in GeoServer
- `is_visible`: Whether layer is visible by default
- `layer_order`: Order for display in layer list

## 🖥️ User Interface

The application provides:
- Interactive map viewer with layer controls
- Layer visibility toggles
- Multiple basemap options
- Responsive design for desktop and mobile

## 🔧 Customization

### Adding New Basemaps

Edit the `map.html` template and add new entries to the `baseMaps` object:

```javascript
const baseMaps = {
    // Existing basemaps
    newBasemap: L.tileLayer('https://tile.url/{z}/{x}/{y}.png', {
        attribution: 'Attribution text'
    }),
}
```

### Changing Default Map View

Modify the map initialization in `map.html`:

```javascript
const map = L.map('map').setView([latitude, longitude], zoomLevel);
```

## 📦 Deployment to Vercel

This application is designed to be deployable to Vercel with minimal configuration:

1. Create a vercel.json file:
```json
{
  "builds": [
    {
      "src": "MainApp/wsgi.py",
      "use": "@vercel/python",
      "config": { "maxLambdaSize": "15mb" }
    },
    {
      "src": "build_files.sh",
      "use": "@vercel/static-build",
      "config": { "distDir": "staticfiles" }
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "MainApp/wsgi.py"
    }
  ]
}
```

2. Create `build_files.sh`:
```bash
#!/bin/bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
```

## 📝 Notes

- The application uses a SQLite database by default, which is read-only in Vercel's production environment
- For production, configure environment variables for sensitive information
- Ensure your GeoServer instance has CORS properly configured

## 📚 Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Leaflet Documentation](https://leafletjs.com/reference.html)
- [GeoServer Documentation](https://docs.geoserver.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Flowbite Documentation](https://flowbite.com/docs/getting-started/introduction/)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
