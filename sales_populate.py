import os
import django
import random
from faker import Faker
from django.utils import timezone
from datetime import datetime, timedelta

# --- Configuración Django ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos.settings')
django.setup()

# --- Importar Modelos ---
from posApp.models import (
    Sales, salesItems, Products, PaymentType
)

fake = Faker()

# --- Obtener datos existentes ---
productos = list(Products.objects.all())
tipos_pago = list(PaymentType.objects.all())

if not productos:
    print("❌ Error: No hay productos en la base de datos. Por favor, crea algunos productos primero.")
    exit()
if not tipos_pago:
    print("❌ Error: No hay tipos de pago en la base de datos. Por favor, crea algunos tipos de pago primero.")
    exit()

print(f"📊 Generando 100 ventas de prueba usando solo los modelos base...")

# --- Preparar listas para bulk_create ---
sales_to_create = []
sales_items_to_create = []

# --- Generación de Ventas ---
# Iteramos para crear los objetos en memoria primero
for _ in range(1000):
    subtotal = round(random.uniform(50, 500), 2)
    descuento = round(random.uniform(0, subtotal * 0.15), 2)
    if descuento > subtotal:
        descuento = 0
    
    tax = 0.18
    tax_amount = round((subtotal - descuento) * tax, 2)
    grand_total = round(subtotal - descuento + tax_amount, 2)
    
    tendered = round(grand_total + random.uniform(0, 50), 2)
    change = round(tendered - grand_total, 2)
    if change < 0:
        change = 0

    fecha_venta = timezone.now() - timedelta(days=random.randint(0, 90))

    # Crear la instancia de Sale (sin guardarla en la BD aún)
    sale = Sales(
        code=f"VTA-{fecha_venta.strftime('%Y%m%d%H%M%S')}-{fake.unique.random_int(min=1000, max=9999)}",
        sub_total=subtotal,
        grand_total=grand_total,
        descuento=descuento,
        tax_amount=tax_amount,
        tax=tax,
        payment_type_id=random.choice(tipos_pago),
        tendered_amount=tendered,
        amount_change=change,
        date_added=fecha_venta,
        date_updated=fecha_venta
    )
    sales_to_create.append(sale)

# Ahora, guardar todas las ventas en una sola operación de base de datos
print("Guardando ventas en lote...")
# bulk_create devuelve las instancias de los objetos creados, incluyendo sus IDs.
# Esto es CRÍTICO para poder asignar los sale_id a los salesItems.
created_sales = Sales.objects.bulk_create(sales_to_create)
print(f"Se crearon {len(created_sales)} objetos de venta.")


# --- Crear Ítems de Venta (salesItems) ---
# Iteramos sobre las ventas que acabamos de crear (que ahora tienen IDs)
print("Preparando ítems de venta en lote...")
for sale in created_sales: # Usamos los objetos con IDs ya asignados
    num_items_per_sale = random.randint(1, 5)
    productos_para_venta = random.sample(productos, min(num_items_per_sale, len(productos)))

    for product in productos_para_venta:
        qty = random.randint(1, 5)
        price = product.price
        total_item = round(price * qty, 2)

        # Crear la instancia de SalesItem (sin guardarla en la BD aún)
        sales_item = salesItems(
            sale_id=sale, # Asignamos la instancia de Sale con su ID
            product_id=product,
            price=price,
            qty=qty,
            total=total_item
        )
        sales_items_to_create.append(sales_item)

# Ahora, guardar todos los ítems de venta en una sola operación de base de datos
print("Guardando ítems de venta en lote...")
salesItems.objects.bulk_create(sales_items_to_create)
print(f"Se crearon {len(sales_items_to_create)} objetos de ítems de venta.")

print("\n✅ ¡Datos de ventas de prueba generados exitosamente!")
print(f"Total de ventas creadas: {Sales.objects.count()}")
print(f"Total de ítems de venta creados: {salesItems.objects.count()}")