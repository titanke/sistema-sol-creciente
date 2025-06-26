from pickle import FALSE
from django.shortcuts import redirect, render
from django.http import HttpResponse
import calendar
from posApp.models import Category, Products, Sales, salesItems, PaymentType, Size, Color,ProductFeature
from django.db.models import Q, Prefetch, F, Sum # Import F and Sum
from django.db.models.deletion import ProtectedError
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.core.paginator import Paginator
from django.db.models import Q
import json, sys
from datetime import date, datetime
from django.db import transaction
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import portrait
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from django.utils.timezone import localtime

from barcode import Code128
from barcode.writer import ImageWriter

from django.core.files.storage import FileSystemStorage
from django.conf import settings

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import os
# Login
def login_user(request):
    logout(request)
    resp = {"status":'failed','msg':''}
    username = ''
    password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status']='success'
            else:
                resp['msg'] = "Usuario o contraseña incorrecto"
        else:
            resp['msg'] = "Usuario o contraseña incorrecto"
    return HttpResponse(json.dumps(resp),content_type='application/json')

#Logout
def logoutuser(request):
    logout(request)
    return redirect('/')

# Create your views here.
@login_required
def home(request):
    now = datetime.now() # Use datetime.datetime for .year, .month
    
    # --- Determine the Year for Dashboard Filters ---
    # Get year from request.GET, default to current year
    dashboard_year_param = request.GET.get('year', '')
    if dashboard_year_param:
        try:
            dashboard_year = int(dashboard_year_param)
        except ValueError:
            dashboard_year = now.year # Default to current year if invalid
    else:
        dashboard_year = now.year # Default to current year if no param
    # -----------------------------------------------

    current_month = now.month
    current_day = now.day

    categories = Category.objects.count() # Use .count() directly
    products = Products.objects.count() # Use .count() directly

    # Transactions for today
    transaction = Sales.objects.filter(
        date_added__year=now.year,
        date_added__month=current_month,
        date_added__day=current_day
    ).count()

    # Total sales for today
    today_sales = Sales.objects.filter(
        date_added__year=now.year,
        date_added__month=current_month,
        date_added__day=current_day
    ).aggregate(total=Sum('grand_total'))['total'] or 0.0 # Use aggregate for sum directly

    # --- Data for Most Sold Products (affected by dashboard_year) ---
    # We want to sum the quantity of each product sold within the selected year
    most_sold_products = salesItems.objects.filter(
        sale_id__date_added__year=dashboard_year # Filter by the selected year
    ).values('product_id__name').annotate(
        total_qty_sold=Sum('qty')
    ).order_by('-total_qty_sold')

    # --- Data for Monthly Sales Evolution Chart (affected by dashboard_year) ---
    # Get monthly sales totals for the selected year
    monthly_sales = Sales.objects.filter(
        date_added__year=dashboard_year
    ).annotate(
        month=F('date_added__month') # Extract month number
    ).values('month').annotate(
        total_monthly_sales=Sum('grand_total')
    ).order_by('month')

    # Prepare data for Chart.js
    sales_data_for_chart = [0] * 12 # Initialize with 0s for 12 months
    
    # Use a list of month names for labels
    month_names = [
        'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
    ]

    for entry in monthly_sales:
        # Month numbers are 1-indexed, so convert to 0-indexed for list
        month_index = entry['month'] - 1
        if 0 <= month_index < 12: # Ensure index is valid
            sales_data_for_chart[month_index] = float(entry['total_monthly_sales'])

    context = {
        'page_title': 'Inicio',
        'categories': categories,
        'products': products,
        'transaction': transaction,
        'total_sales': format(float(today_sales), '.2f'), # Format sales for display
        'dashboard_year': dashboard_year, # Pass the selected year to the template
        'current_year_for_filter': now.year, # For max attribute in year input
        'most_sold_products': most_sold_products,
        'monthly_sales_labels': month_names, # Month names for chart X-axis
        'monthly_sales_data': sales_data_for_chart, # Sales values for chart Y-axis
    }
    return render(request, 'posApp/home.html', context)

def about(request):
    context = {
        'page_title':'About',
    }
    return render(request, 'posApp/about.html',context)

#Categories
@login_required
def category(request):
    category_list = Category.objects.all()
    # category_list = {}
    context = {
        'page_title':'Lista de Categorias',
        'category':category_list,
    }
    return render(request, 'posApp/category.html',context)


@login_required
def manage_category(request):
    category = {}
    if request.method == 'GET':
        data =  request.GET
        id = ''
        if 'id' in data:
            id= data['id']
        if id.isnumeric() and int(id) > 0:
            category = Category.objects.filter(id=id).first()
    
    context = {
        'category' : category
    }
    return render(request, 'posApp/manage_category.html',context)

@login_required
def color(request):
    search = request.GET.get('search', '')
    if search:
        color_list = Color.objects.filter(name__icontains=search)
    else:
        color_list = Color.objects.all()
    # category_list = {}
    context = {
        'page_title':'Lista de Colores',
        'color':color_list,
    }
    return render(request, 'posApp/color.html',context)


def manage_color(request):
    color = {}
    if request.method == 'GET':
        data =  request.GET
        id = ''
        if 'id' in data:
            id= data['id']
        if id.isnumeric() and int(id) > 0:
            color = Color.objects.filter(id=id).first()
    
    context = {
        'color' : color
    }
    return render(request, 'posApp/manage_color.html',context)


@login_required
def save_color(request):
    data =  request.POST
    resp = {'status':'failed'}
    try:
        if (data['id']).isnumeric() and int(data['id']) > 0 :
            save_color = Color.objects.filter(id = data['id']).update(name=data['name'],status = data['status'])
        else:
            save_color = Color(name=data['name'],status = data['status'])
            save_color.save()
        resp['status'] = 'success'
        messages.success(request, 'Color agregado correctamente.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")



@login_required
def delete_color(request):
    data = request.POST
    resp = {'status': ''}
    try:
        # Intentar eliminar la categoría
        Color.objects.get(id=data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Color eliminado.')

    except Exception as e:
        if "restricted foreign keys" in str(e):
            resp['status'] = 'failed'
            resp['message'] = 'No se puede eliminar el color seleccionado porque está relacionado con uno o más productos.'
        else:
            resp['status'] = 'failed'
            resp['message'] = f'Ocurrió un error inesperado: {str(e)}'

    return HttpResponse(json.dumps(resp), content_type="application/json")



""
@login_required
def payment(request):
    search = request.GET.get('search', '')
    if search:
        color_list = PaymentType.objects.filter(name__icontains=search)
    else:
        color_list = PaymentType.objects.all()
    # category_list = {}
    context = {
        'page_title':'Lista de Tipos de pago',
        'payment':color_list,
    }
    return render(request, 'posApp/payment.html',context)

@login_required
def manage_payment(request):
    payment = {}
    if request.method == 'GET':
        data =  request.GET
        id = ''
        if 'id' in data:
            id= data['id']
        if id.isnumeric() and int(id) > 0:
            payment = PaymentType.objects.filter(id=id).first()
    
    context = {
        'payment' : payment
    }
    return render(request, 'posApp/manage_payment.html',context)


@login_required
def save_payment(request):
    data =  request.POST
    resp = {'status':'failed'}
    try:
        if (data['id']).isnumeric() and int(data['id']) > 0 :
            save_payment = PaymentType.objects.filter(id = data['id']).update(name=data['name'],status = data['status'])
        else:
            save_payment = PaymentType(name=data['name'],status = data['status'])
            save_payment.save()
        resp['status'] = 'success'
        messages.success(request, 'Tipo de pago agregado correctamente.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")



@login_required
def delete_payment(request):
    data = request.POST
    resp = {'status': ''}
    try:
        # Intentar eliminar la categoría
        PaymentType.objects.get(id=data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Tipo de pago eliminado.')

    except Exception as e:
        if "restricted foreign keys" in str(e):
            resp['status'] = 'failed'
            resp['message'] = 'No se puede eliminar el tipo de pago seleccionado porque está relacionado con uno o más ventas.'
        else:
            resp['status'] = 'failed'
            resp['message'] = f'Ocurrió un error inesperado: {str(e)}'

    return HttpResponse(json.dumps(resp), content_type="application/json")



""


@login_required
def size(request):
    search = request.GET.get('search', '')
    if search:
        size_list = Size.objects.filter(name__icontains=search)
    else:
        size_list = Size.objects.all()
    # category_list = {}
    context = {
        'page_title':'Lista de Tallas',
        'size':size_list,
    }
    return render(request, 'posApp/size.html',context)

@login_required

def manage_size(request):
    size = {}
    if request.method == 'GET':
        data =  request.GET
        id = ''
        if 'id' in data:
            id= data['id']
        if id.isnumeric() and int(id) > 0:
            size = Size.objects.filter(id=id).first()
    
    context = {
        'size' : size
    }
    return render(request, 'posApp/manage_size.html',context)


@login_required
def save_size(request):
    data =  request.POST
    resp = {'status':'failed'}
    try:
        if (data['id']).isnumeric() and int(data['id']) > 0 :
            save_size = Size.objects.filter(id = data['id']).update(name=data['name'],status = data['status'])
        else:
            save_size = Size(name=data['name'],status = data['status'])
            save_size.save()
        resp['status'] = 'success'
        messages.success(request, 'Talla agregado correctamente.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_size(request):
    data = request.POST
    resp = {'status': ''}
    try:
        # Intentar eliminar la categoría
        Size.objects.get(id=data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Talla eliminada.')

    except Exception as e:
        if "restricted foreign keys" in str(e):
            resp['status'] = 'failed'
            resp['message'] = 'No se puede eliminar la talla seleccionada porque está relacionado con uno o más productos.'
        else:
            resp['status'] = 'failed'
            resp['message'] = f'Ocurrió un error inesperado: {str(e)}'

    return HttpResponse(json.dumps(resp), content_type="application/json")



@login_required
def save_category(request):
    data =  request.POST
    resp = {'status':'failed'}
    try:
        if (data['id']).isnumeric() and int(data['id']) > 0 :
            save_category = Category.objects.filter(id = data['id']).update(name=data['name'], description = data['description'],status = data['status'])
        else:
            save_category = Category(name=data['name'], description = data['description'],status = data['status'])
            save_category.save()
        resp['status'] = 'success'
        messages.success(request, 'Categoria agregada correctamente.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def delete_category(request):
    data = request.POST
    resp = {'status': ''}
    try:
        # Intentar eliminar la categoría
        Category.objects.get(id=data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Categoría eliminada.')

    except Exception as e:
        if "restricted foreign keys" in str(e):
            resp['status'] = 'failed'
            resp['message'] = 'No se puede eliminar la categoría porque está relacionada con uno o más productos.'
        else:
            resp['status'] = 'failed'
            resp['message'] = f'Ocurrió un error inesperado: {str(e)}'

    return HttpResponse(json.dumps(resp), content_type="application/json")

# Products

def products(request):
    search = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    search_id = request.GET.get('search_id', '')
    
    
    # Filtrar productos basados en búsqueda y categoría
    if search:
        product_list = Products.objects.filter(name__icontains=search)
    else:
        product_list = Products.objects.all()

    if category_filter:
        product_list = product_list.filter(category_id=category_filter)
        
    if status_filter:
        product_list = product_list.filter(status=status_filter)

    if search_id:
        product_list = product_list.filter(id=int(search_id))

     
    #Ventas de hoy   
    now = datetime.now()
    current_year = now.strftime("%Y")
    current_month = now.strftime("%m")
    current_day = now.strftime("%d")
    products = len(Products.objects.all())

    today_sales = Sales.objects.filter(
        date_added__year=current_year,
        date_added__month = current_month,
        date_added__day = current_day
    ).all()
    total_sales = sum(today_sales.values_list('grand_total',flat=True))    
    

    # Calcular el total de productos
    total_products = product_list.count()

    # Para paginación
    page = request.GET.get('page', 1)
    paginator = Paginator(product_list, 10)  # 10 productos por página
    products_page = paginator.get_page(page)
    
    
    #Total inversion productos
    products = Products.objects.all()
    total_investment = sum(product.p_mayor_compra * product.stock for product in products)
    
    context = {
        'page_title': 'Lista de Productos',
        'products': products_page,
        'total_products': total_products,  # Añadir el total
        'category_filter': category_filter,  # Pasar el filtro de categoría
        'categories': Category.objects.all(),  # Si necesitas las categorías para el select
        'total_sales': total_sales,
        'total_investment': total_investment,
        'search_id': search_id,
        'search': search,
        'category_filter': category_filter,
        'status_filter': status_filter,
    }
    return render(request, 'posApp/products.html', context)

@login_required
def manage_products(request):
    product = {}
    features = []
    categories = Category.objects.filter(status=1).all()
    colors = Color.objects.all()
    sizes = Size.objects.all()

    if request.method == 'GET':
        data = request.GET
        id = ''
        if 'id' in data:
            id = data['id']
        if id.isnumeric() and int(id) > 0:
            product = Products.objects.filter(id=id).first()
            if product:
                features = product.features.all()

    context = {
        'product': product,
        'features': features,
        'categories': categories,
        'colors': colors,
        'sizes': sizes,
    }
    return render(request, 'posApp/manage_product.html', context)




def test(request):
    categories = Category.objects.all()
    context = {
        'categories' : categories
    }
    return render(request, 'posApp/test.html',context)

@transaction.atomic
@login_required
def save_product(request):
    data = request.POST
    resp = {'status': 'failed'}

    deleted_features = data.get('deleted_features', '').split(',')
    deleted_features = [int(feature_id) for feature_id in deleted_features if feature_id.isdigit()]

    # Eliminar las características marcadas como eliminadas
    ProductFeature.objects.filter(id__in=deleted_features).delete()

    try:
        # Manejo del ID
        id = data.get('id', '')
        id = int(id) if id.isnumeric() else None

        # Validar datos necesarios
        if not data.get('name') or not data.get('price'):
            resp['msg'] = "Nombre y precio son campos obligatorios."
            return HttpResponse(json.dumps(resp), content_type="application/json")

        # Validar precios
        try:
            price = float(data['price'].replace(',', '.'))
            p_mayor_compra = float(data['p_mayor_compra'].replace(',', '.'))
            if data['p_mayor_venta'] != '':
                p_mayor_venta = float(data['p_mayor_venta'].replace(',', '.'))
            else:
                p_mayor_venta = 0.0

        except ValueError:
            resp['msg'] = "Formato de precio no válido. Usa números y puntos."
            return HttpResponse(json.dumps(resp), content_type="application/json")

        # Validar categoría
        category_id = data.get('category_id')
        category = Category.objects.filter(id=category_id).first() if category_id else None
        if not category:
            resp['msg'] = "Categoría seleccionada no es válida."
            return HttpResponse(json.dumps(resp), content_type="application/json")

        # Guardar o actualizar producto
        if id:
            # Actualización de producto existente
            product = Products.objects.get(id=id)
            product.category_id = category
            product.name = data['name']
            product.description = data['description']
            product.price = price
            product.p_mayor_compra = p_mayor_compra
            product.p_mayor_venta = p_mayor_venta
            product.stock = int(data['stock'])
            product.status = int(data['status'])
        else:
            # Crear nuevo producto
            product = Products.objects.create(
                category_id=category,
                name=data['name'],
                description=data['description'],
                price=price,
                p_mayor_compra=p_mayor_compra,
                p_mayor_venta = p_mayor_venta,
                stock=int(data['stock']),
                status=int(data['status']),
            )

        if 'image' in request.FILES:
            new_image = request.FILES['image']
            fs = FileSystemStorage(location='media/products')
            filename = fs.save(new_image.name, new_image)
            image_url = 'media/products/' + filename
            # Si ya existe una imagen anterior, eliminarla
            if product.image:
                if os.path.isfile(product.image):
                    os.remove(product.image)
            # Asignar la nueva imagen al producto
            product.image = image_url

        # Manejo de características (ProductFeature)
        ProductFeature.objects.filter(product=product).delete()  # Elimina características previas
        feature_colors = data.getlist('feature_color[]')
        feature_sizes = data.getlist('feature_size[]')
        feature_stocks = data.getlist('feature_stock[]')

        total_feature_stock = 0
        for color_id, size_id, stock in zip(feature_colors, feature_sizes, feature_stocks):
            stock = int(stock)
            total_feature_stock += stock
            color = Color.objects.filter(id=color_id).first()
            size = Size.objects.filter(id=size_id).first()

            if color and size:
                ProductFeature.objects.create(product=product, color=color, size=size, stock=stock)

        if total_feature_stock > product.stock:
            raise ValueError("El stock total de las características no puede superar el stock general del producto.")

        product.save() 
        resp['status'] = 'success'
        resp['msg'] = "Producto guardado correctamente."
    except Exception as e:
        if "UNIQUE" in str(e):
            resp['msg'] = "No se puede guardar el mismo color y talla del producto"
        else:
            print(f"Error al guardar el producto: {e}")
            resp['msg'] = f"Error al guardar el producto: {str(e)}"

    return HttpResponse(json.dumps(resp), content_type="application/json")

def upload_file(request):
    media_path = os.path.join(settings.MEDIA_ROOT)
    selected_directory = request.POST.get('directory', '') 
    selected_directory_path = os.path.join(media_path,"products")
    print(selected_directory)
    # Crea la carpeta si no existe
    #os.makedirs(selected_directory_path, exist_ok=True)

    if request.method == 'POST':
        file = request.FILES.get('file')
        # Obtiene la extensión del archivo
        extension = os.path.splitext(file.name)[1]
        # Crea el nuevo nombre del archivo
        new_file_name = f"{selected_directory}{extension}"
        file_path = os.path.join(selected_directory_path, new_file_name)
        with open(file_path, 'wb') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def delete_product(request):
    data =  request.POST
    resp = {'status':''}
    try:
        product = Products.objects.get(id=data['id'])
        if product.image:
       
            if os.path.isfile(product.image):
                os.remove(product.image)
        product.delete()
        resp['status'] = 'success'
        messages.success(request, 'Producto eliminado.')
    except Exception as e:
        if "restricted foreign keys" in str(e):
            resp['status'] = 'failed'
            resp['message'] = 'No se puede eliminar el Producto por que esta relacionado a una o varias ventas'
        else:
            resp['status'] = 'failed'
            resp['message'] = f'Ocurrió un error inesperado: {str(e)}'
        
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def pos(request):
    products = Products.objects.filter(status=1)
    product_json = []
    for product in products:
        features = product.features.all()
        feature_data = [
            {
                'id': feature.id,
                'color': feature.color.name,
                'size': feature.size.name,
                'stock': feature.stock
            }
            for feature in features
        ]
        product_json.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'p_mayor_venta': float(product.p_mayor_venta),
            'stock': product.stock,
            'features': feature_data
        })

    context = {
        'page_title': "Punto de venta",
        'products': products,
        'product_json': json.dumps(product_json)
    }
    return render(request, 'posApp/pos.html', context)




@login_required
def checkout_modal(request):
    grand_total = 0
    payment = PaymentType.objects.filter(status=1).all()
    if 'grand_total' in request.GET:
        grand_total = request.GET['grand_total']
    context = {
        'grand_total' : grand_total,
        'payment': payment,
    }
    return render(request, 'posApp/checkout.html',context)



@login_required
def save_pos(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    pref = datetime.now().year + datetime.now().year
    payment_type = data.get('payment_type_id')
    payment = PaymentType.objects.filter(id=payment_type).first() if payment_type else None
    
    if data.get('pos_print_after_save') == 'true':
        resp['print'] = True
    
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += 1
        check = Sales.objects.filter(code=str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)
    grand_totalv = data.get('grand_total', '0')  # Obtén el valor o usa '0' como predeterminado
    try:
        grand_totalv = float(grand_totalv.replace(',', '').strip())  # Elimina comas y espacios
    except ValueError:
        grand_totalv = 0.0  # Maneja el caso de un valor no convertible


    try:
        sales = Sales(code=code, sub_total=data['sub_total'], payment_type_id=payment, descuento=data['descuento'], tax=data['tax'],
                      tax_amount=data['tax_amount'], grand_total=grand_totalv, tendered_amount=data['tendered_amount'],
                      amount_change=data['amount_change'], user_id=request.user).save()
        sale_id = Sales.objects.last().pk
        i = 0
        for prod in data.getlist('product_id[]'):
            product_id = prod
            sale = Sales.objects.filter(id=sale_id).first()
            product = Products.objects.filter(id=product_id).first()
            qty = data.getlist('qty[]')[i]
            price = data.getlist('price[]')[i]
            total = float(qty) * float(price)

            # Update product stock
             # Ensure qty is converted to integer for subtraction
            product.stock -= int(qty) 
            product.save()  # Save the updated stock
            
                # Verificar si hay un feature seleccionado para este producto
            feature_id = data.getlist('feature_id[]')[i] if 'feature_id[]' in data else None
            feature = None  # Inicializar el feature como None por defecto

            if feature_id:
                feature = ProductFeature.objects.filter(id=feature_id).first()
                if feature:
                    feature.stock -= int(qty) 
                    feature.save()  # Guardar el stock actualizado en el feature

            # Registrar el ítem en la venta
            print({'sale_id': sale, 'product_id': product, 'feature_id': feature, 'qty': qty, 'price': price, 'total': total})
                    
            salesItems(sale_id=sale, product_id=product, feature_id=feature, qty=qty, price=price, total=total).save()
            i += 1
        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        messages.success(request, "Registro de venta exitoso")
        
        Products.objects.filter(stock=0).update(status=0)  # Update all products with 0 stock
    except Exception as e:
        resp['msg'] = f"Ocurrió un error: {str(e)}"
        print("Unexpected error:", sys.exc_info()[0])
    return HttpResponse(json.dumps(resp), content_type="application/json")


@csrf_exempt
def generate_qr(request):
    if request.method == 'POST':
        product_id = request.POST.get('id')
        product = Products.objects.get(pk=product_id)

        current_year = datetime.now().year

        barcode_data = f"{product.pk}-{current_year}"
        buffer = BytesIO()
        barcode = Code128(barcode_data, writer=ImageWriter())
        
        # Escribir el código de barras con estilo personalizado
        barcode.write(buffer, options={
            "module_width": 0.3,   # Ancho de cada línea de barra
            "module_height": 10.0, # Altura de las barras
            "font_size": 6,       # Tamaño del texto debajo
            "text_distance": 3.0,  # Espacio entre barras y texto
            "quiet_zone": 2.0,     # Margen alrededor
            "write_text": True     # Mostrar el código debajo
        })

        image_png = buffer.getvalue()
        buffer.close()

        # Eliminar archivos anteriores
        for file in os.listdir('media/static/qr_codes/'):
            os.remove(os.path.join('media/static/qr_codes/', file))

        # Guardar la imagen del código de barras
        barcode_image = ContentFile(image_png)
        file_path = default_storage.save(f'static/qr_codes/{product_id}.png', barcode_image)

        barcode_url = default_storage.url(file_path)
        return JsonResponse({'status': 'success', 'qr_url': barcode_url})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def save_qr(request):
    qr_code = request.GET.get('qr_code')
    product = Products.objects.get(code=qr_code)
    return JsonResponse({'product_id': product.id})


def salesList(request):
    # Get search parameters
    search_query = request.GET.get('search', '')
    date_from_param = request.GET.get('date_from', '')
    payment_type_id = request.GET.get('payment_type_id', '')
    
    # Determine Year and Month for filters and defaults
    year_param = request.GET.get('year', '')
    month_param = request.GET.get('month', '')

    current_datetime = datetime.now()
    
    if year_param:
        try:
            year = int(year_param)
        except ValueError:
            year = current_datetime.year
    else:
        year = current_datetime.year

    if month_param:
        try:
            month = int(month_param)
        except ValueError:
            month = current_datetime.month
    else:
        month = current_datetime.month

    page = request.GET.get('page', 1)

    # --- 1. Build the BASE QuerySet with all common filters ---
    # This queryset will include search, date_from, and payment_type filters.
    # It will be the foundation for both current period and accumulated sums.
    base_queryset = Sales.objects.select_related('payment_type_id').order_by('-id')

    if not request.user.is_superuser: # Check if the logged-in user is NOT an admin
        base_queryset = base_queryset.filter(user_id=request.user)

    if search_query:
        base_queryset = base_queryset.filter(Q(code__icontains=search_query))

    if date_from_param:
        try:
            parsed_date_from = datetime.strptime(date_from_param, '%Y-%m-%d').date()
            base_queryset = base_queryset.filter(date_added__date__gte=parsed_date_from)
        except ValueError:
            pass

    if payment_type_id:
        base_queryset = base_queryset.filter(payment_type_id=payment_type_id)
    # ----------------------------------------------------------

    # --- 2. QuerySet for the CURRENT PERIOD (base_queryset + month/year) ---
    # This will be used for displaying sales on the page and for "current month/year" aggregates.
    current_period_queryset = base_queryset.filter(date_added__year=year, date_added__month=month).prefetch_related(
        Prefetch('salesitems_set', queryset=salesItems.objects.select_related('product_id'))
    )

    # --- Aggregations for the CURRENT month/year ---
    total_profit_current_month_result = current_period_queryset.aggregate(
        profit=Sum(
            (F('salesitems__price') - F('salesitems__product_id__p_mayor_compra')) * F('salesitems__qty')
        )
    )
    total_profit_current_month = total_profit_current_month_result.get('profit') or 0.0
    total_profit_current_month = format(float(total_profit_current_month), '.2f')

    total_sales_current_month_result = current_period_queryset.aggregate(revenue=Sum('grand_total'))
    total_sum_of_sales_current_month = total_sales_current_month_result.get('revenue') or 0.0
    total_sum_of_sales_current_month = format(float(total_sum_of_sales_current_month), '.2f')

    # --- 3. QuerySet for ACCUMULATED values (base_queryset + date_added__lte) ---
    # This will respect all filters from base_queryset, AND filter by date up to the selected month/year.
    last_day_of_month = calendar.monthrange(year, month)[1]
    end_date_for_accumulation = datetime(year, month, last_day_of_month, 23, 59, 59)

    accumulated_queryset = base_queryset.filter(date_added__lte=end_date_for_accumulation)

    # --- Aggregations for ACCUMULATED values (respecting all filters) ---
    total_profit_accumulated_result = accumulated_queryset.aggregate(
        profit=Sum(
            (F('salesitems__price') - F('salesitems__product_id__p_mayor_compra')) * F('salesitems__qty')
        )
    )
    total_accumulated_profit = total_profit_accumulated_result.get('profit') or 0.0
    total_accumulated_profit = format(float(total_accumulated_profit), '.2f')

    total_sales_accumulated_result = accumulated_queryset.aggregate(revenue=Sum('grand_total'))
    total_accumulated_sales = total_sales_accumulated_result.get('revenue') or 0.0
    total_accumulated_sales = format(float(total_accumulated_sales), '.2f')
    # ---------------------------------------------------------------------

    # --- Pagination for the current page display ---
    # Use the current_period_queryset for displaying sales on the page.
    paginator = Paginator(current_period_queryset, 10)
    sales_page = paginator.get_page(page)

    # --- Process data for template (for individual sale display) ---
    sale_data = []
    for sale in sales_page.object_list:
        total_profit_for_this_sale = 0.0
        items_list = list(sale.salesitems_set.all())

        for item in items_list:
            if item.product_id and item.product_id.p_mayor_compra is not None:
                profit_per_single_unit = item.price - item.product_id.p_mayor_compra
                total_profit_for_this_sale += (profit_per_single_unit * item.qty)
        
        data = {
            'id': sale.id,
            'code': sale.code,
            'sub_total': sale.sub_total,
            'grand_total': sale.grand_total,
            'descuento': sale.descuento,
            'tax_amount': format(float(sale.tax_amount), '.2f'),
            'tax': sale.tax,
            'tendered_amount': sale.tendered_amount,
            'amount_change': sale.amount_change,
            'date_added': sale.date_added,
            'date_updated': sale.date_updated,
            'payment_type': sale.payment_type_id.name if sale.payment_type_id else 'N/A',
            'item_count': len(items_list),
            'username': sale.user_id.username if sale.user_id else 'N/A',
            'profit_for_sale': format(total_profit_for_this_sale, '.2f'),
        }
        sale_data.append(data)

    payment_types = PaymentType.objects.all()

    # Count of total sales for the CURRENT PERIOD
    total_sales_count = accumulated_queryset.count()

    # --- Additional data for template context ---
    months_choices = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]

    context = {
        'page_title': 'Transacciones',
        'sale_pages': sales_page,
        'sale_data': sale_data,
        # Count for the CURRENT PERIOD
        'total_sales_count': total_sales_count, 
        
        # Profit and Sales values for the CURRENT PERIOD (selected Month & Year)
        'total_profit_current_month': total_profit_current_month,
        'total_sum_of_sales_current_month': total_sum_of_sales_current_month,

        # Profit and Sales values ACCUMULATED UP TO the selected Month & Year (respecting all filters)
        'total_accumulated_profit': total_accumulated_profit,
        'total_accumulated_sales': total_accumulated_sales,
        
        'search_query': search_query,
        'date_from': date_from_param,
        'payment_types': payment_types,
        'payment_type_id': payment_type_id,
        'year': year,
        'month': month,
        'current_year': current_datetime.year,
        'months_choices': months_choices,
    }
    return render(request, 'posApp/sales.html', context)

@login_required
def receipt(request):
    id = request.GET.get('id')
    sales = Sales.objects.filter(id = id).first()
    transaction = {}
    for field in Sales._meta.get_fields():
        if field.related_model is None:
            transaction[field.name] = getattr(sales,field.name)
    if 'tax_amount' in transaction:
        transaction['tax_amount'] = format(float(transaction['tax_amount']))
    ItemList = salesItems.objects.filter(sale_id = sales).all()
    context = {
        "transaction" : transaction,
        "salesItems" : ItemList
    }

    return render(request, 'posApp/receipt.html',context)
    # return HttpResponse('')




@login_required
def receipt_pdf(request):
    sale_id = request.GET.get('id')
    sale = Sales.objects.filter(id=sale_id).first()
    if not sale:
        return HttpResponse("Venta no encontrada", status=404)

    items = salesItems.objects.filter(sale_id=sale)
    #payments = SalesPayment.objects.filter(sale=sale)

    # Parámetros de diseño
    ticket_width = 80 * mm
    line_height = 4 * mm
    top_margin = -1 * mm
    bottom_margin = -4 * mm

    # Calcular líneas fijas y dinámicas
    fixed_lines = 24  # logo+titulos+separadores+datos+headers+total+pie etc.
    num_item_lines = items.count()
    #num_payment_lines = payments.count()
    total_lines = fixed_lines + num_item_lines  

    # Altura dinámica
    ticket_height = top_margin + bottom_margin + total_lines * line_height

    # Crear canvas en memoria
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=(ticket_width, ticket_height))
    y = ticket_height - top_margin

    # Helpers de dibujo
    def draw_center(text, size=9, move=1):
        nonlocal y
        p.setFont("Courier-Bold", size)
        p.drawCentredString(ticket_width / 2, y, text)
        y -= line_height * move

    def draw_left(text, size=9, move=1):
        nonlocal y
        p.setFont("Courier-Bold", size)
        p.drawString(5 * mm, y, text)
        y -= line_height * move
    
    def draw_left_(text, size=9, move=1):
        nonlocal y
        p.setFont("Courier", size)
        p.drawString(5 * mm, y, text)
        y -= line_height * move
        
    def draw_right(text, size=9, move=1):
        nonlocal y
        p.setFont("Courier-Bold", size)
        p.drawRightString(ticket_width - 5 * mm, y, text)
        y -= line_height * move
        
    def draw_right_m(text, size=9, move=1):
        nonlocal y
        p.setFont("Courier-Bold", size)
        p.drawRightString(ticket_width - 5 * mm, y, text)
        y -= line_height * move

    def draw_sep():
        draw_left("-" * 41, size=8, move=1)


    # Títulos
    draw_sep()

    draw_center("SOL CRECIENTE STORE", size=8)
    draw_center("BOLETA DE VENTA", size=8)
    draw_center(f"CÓDIGO DE VENTA: {sale.code}", size=8)
    draw_sep()

    # Datos fecha/hora y contacto
    local_date = localtime(sale.date_added)

    draw_left(f"Fecha:{local_date.strftime('%d/%m/%Y')}", size=8)
    draw_left(f"Hora: {local_date.strftime('%H:%M')}", size=8)
    draw_left("De:   Yessica Marisol Colquehuanca", size=8)
    draw_left("RUC:  1010101010", size=8)
    draw_left("Tel:  942352219", size=8)
    draw_sep()

    # Cabecera de items
    draw_left("Producto", size=9, move=0)
    draw_right_m("Importe", size=9, move=1)

    # Items
    for item in items:
        name = f"{item.product_id.name}"
        qty_price = f"{item.qty} x S/ {item.total/item.qty:.2f}"
        p.setFont("Courier-Bold", 8)
        p.drawString(5 * mm, y, name)
        p.drawRightString(ticket_width - 5 * mm, y, qty_price)
        y -= line_height

    draw_sep()

    # Total
    draw_left("Total:", size=8, move=0)
    draw_right(f"S/ {sale.grand_total:.2f}", size=8, move=1)
    draw_sep()

    # Métodos de Pago
    #draw_left("Métodos de Pago:", size=8)
    #for pmt in payments:
    #    draw_left_(f"{pmt.payment_type.name}", size=8, move=0)
    #    draw_right(f"S/ {pmt.amount:.2f}", size=8, move=1)

    #draw_sep()

    # Recibido / Vuelto
    draw_left("Recibido:", size=8, move=0)
    draw_right(f"S/ {sale.tendered_amount:.2f}", size=8, move=1)
    draw_left("Vuelto:", size=8, move=0)
    draw_right(f"S/ {sale.amount_change:.2f}", size=8, move=1)
    draw_sep()

    # Pie
    draw_center("¡Gracias por su visita!", size=8)

    p.showPage()
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')





@login_required
def delete_sale(request):
    resp = {'status': 'failed', 'msg': ''}
    id = request.POST.get('id')
    restore_stock = request.POST.get('restore_stock', 'false').lower() == 'true'  # Leer el parámetro de restauración
    try:
        if restore_stock:
            # Restaurar stock de los items antes de eliminar la venta
            sale_items = salesItems.objects.filter(sale_id=id)
            
            for item in sale_items:
                # Restaurar el stock del producto
                product = item.product_id
                product.stock += item.qty
                
                if product.status == 0 and product.stock > 0:
                    product.status = 1  
                product.save()
                
                # Restaurar el stock del feature si aplica
                if item.feature_id:
                    feature = item.feature_id
                    feature.stock += item.qty
                    feature.save()
        
        # Eliminar la venta y los items asociados
        Sales.objects.filter(id=id).delete()
        
        resp['status'] = 'success'
        if restore_stock:
            messages.success(request, 'Historial de venta eliminado y stock restaurado.')
        else:
            messages.success(request, 'Historial de venta eliminado sin restaurar el stock.')
    except Exception as e:
        resp['msg'] = f"Ocurrió un error: {str(e)}"
        print("Unexpected error:", e)
    
    return HttpResponse(json.dumps(resp), content_type='application/json')
