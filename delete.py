import os
import django

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos.settings')
django.setup()

from posApp.models import Sales, salesItems

# Borrar todos los items primero (porque dependen de Sales)
salesItems.objects.all().delete()

# Luego borrar las ventas
Sales.objects.all().delete()

print("✅ Registros eliminados.")
