from pickle import FALSE
from django.shortcuts import redirect, render
from django.http import HttpResponse
from posApp.models import Category, Products, Sales, salesItems, ProductImage, Size, Color,ProductFeature
from django.db.models import Count, Sum
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.core.paginator import Paginator
from django.db.models import Q
import json, sys
from datetime import date, datetime
from django.db import transaction


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
    now = datetime.now()
    current_year = now.strftime("%Y")
    current_month = now.strftime("%m")
    current_day = now.strftime("%d")
    categories = len(Category.objects.all())
    products = len(Products.objects.all())
    transaction = len(Sales.objects.filter(
        date_added__year=current_year,
        date_added__month = current_month,
        date_added__day = current_day
    ))
    today_sales = Sales.objects.filter(
        date_added__year=current_year,
        date_added__month = current_month,
        date_added__day = current_day
    ).all()
    total_sales = sum(today_sales.values_list('grand_total',flat=True))
    context = {
        'page_title':'Inicio',
        'categories' : categories,
        'products' : products,
        'transaction' : transaction,
        'total_sales' : total_sales,
    }
    return render(request, 'posApp/home.html',context)


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
    data =  request.POST
    resp = {'status':''}
    try:
        Color.objects.filter(id = data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Color eliminado.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


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
    data =  request.POST
    resp = {'status':''}
    try:
        Size.objects.filter(id = data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Talla eliminada.')
    except:
        resp['status'] = 'failed'
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
    data =  request.POST
    resp = {'status':''}
    try:
        Category.objects.filter(id = data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Categoria eliminada.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")

# Products



def products(request):
    # Obtener el filtro de búsqueda y categoría
    search = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')

    # Filtrar productos basados en búsqueda y categoría
    if search:
        product_list = Products.objects.filter(name__icontains=search)
    else:
        product_list = Products.objects.all()

    if category_filter:
        product_list = product_list.filter(category_id=category_filter)

    # Calcular el total de productos
    total_products = product_list.count()

    # Para paginación
    page = request.GET.get('page', 1)
    paginator = Paginator(product_list, 10)  # 10 productos por página
    products_page = paginator.get_page(page)

    context = {
        'page_title': 'Lista de Productos',
        'products': products_page,
        'total_products': total_products,  # Añadir el total
        'category_filter': category_filter,  # Pasar el filtro de categoría
        'categories': Category.objects.all(),  # Si necesitas las categorías para el select
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

    try:
        # Manejo del ID
        id = data.get('id', '')
        id = int(id) if id.isnumeric() else None

        # Validar datos necesarios
        if not data.get('code') or not data.get('name') or not data.get('price'):
            resp['msg'] = "Código, nombre y precio son campos obligatorios."
            return HttpResponse(json.dumps(resp), content_type="application/json")

        # Validar precios
        try:
            price = float(data['price'].replace(',', '.'))
            p_mayor = float(data['p_mayor'].replace(',', '.'))
        except ValueError:
            resp['msg'] = "Formato de precio no válido. Usa números y puntos."
            return HttpResponse(json.dumps(resp), content_type="application/json")

        # Validar categoría
        category_id = data.get('category_id')
        category = Category.objects.filter(id=category_id).first() if category_id else None
        if not category:
            resp['msg'] = "Categoría seleccionada no es válida."
            return HttpResponse(json.dumps(resp), content_type="application/json")

        # Verificar duplicados
        if id:
            duplicate_check = Products.objects.exclude(id=id).filter(code=data['code']).exists()
        else:
            duplicate_check = Products.objects.filter(code=data['code']).exists()

        if duplicate_check:
            resp['msg'] = "El código del producto ya existe en la base de datos."
            return HttpResponse(json.dumps(resp), content_type="application/json")

        # Guardar o actualizar producto
        if id:
            # Actualización de producto existente
            product = Products.objects.get(id=id)
            product.code = data['code']
            product.category_id = category
            product.name = data['name']
            product.description = data['description']
            product.price = price
            product.p_mayor = p_mayor
            product.stock = int(data['stock'])
            product.status = int(data['status'])
            product.save()
        else:
            # Crear nuevo producto
            product = Products.objects.create(
                code=data['code'],
                category_id=category,
                name=data['name'],
                description=data['description'],
                price=price,
                p_mayor=p_mayor,
                stock=int(data['stock']),
                status=int(data['status']),
            )

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

        resp['status'] = 'success'
        resp['msg'] = "Producto guardado correctamente."
    except Exception as e:
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
        # Construye la ruta completa del archivo de la imagen
        image_path = os.path.join(settings.MEDIA_ROOT, 'products', f'{data["id"]}.jpg')
        # Verifica si el archivo existe y lo elimina
        if os.path.isfile(image_path):
            os.remove(image_path)
        product.delete()
        resp['status'] = 'success'
        messages.success(request, 'Producto eliminado.')
    except Exception as e:
        print(f"Error deleting product: {e}")
        resp['status'] = 'failed'
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
    if 'grand_total' in request.GET:
        grand_total = request.GET['grand_total']
    context = {
        'grand_total' : grand_total,
    }
    return render(request, 'posApp/checkout.html',context)



@login_required
def save_pos(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    pref = datetime.now().year + datetime.now().year
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += 1
        check = Sales.objects.filter(code=str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)

    try:
        sales = Sales(code=code, sub_total=data['sub_total'], descuento=data['descuento'], tax=data['tax'],
                      tax_amount=data['tax_amount'], grand_total=data['grand_total'], tendered_amount=data['tendered_amount'],
                      amount_change=data['amount_change']).save()
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
    except:
        resp['msg'] = "Ocurrio un error"
        print("Unexpected error:", sys.exc_info()[0])
    return HttpResponse(json.dumps(resp), content_type="application/json")


@csrf_exempt
def generate_qr(request):
    if request.method == 'POST':
        product_id = request.POST.get('id')
        product = Products.objects.get(pk=product_id)

        # Convertir el objeto del producto a string
        idp = str(product.pk)
        pro = str(product.price)

        # Generar el QR
        img = qrcode.make(idp+"- S/. "+pro)

        # Guardar el QR en un archivo temporal
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        image_png = buffer.getvalue()
        buffer.close()
        for file in os.listdir('media/static/qr_codes/'):
                    os.remove(os.path.join('media/static/qr_codes/', file))

        # Crear un archivo Django con el QR
        qr_image = ContentFile(image_png)
        file_path = default_storage.save('static/qr_codes/' + product_id + '.png', qr_image)
        
        qr_url = default_storage.url(file_path)
        return JsonResponse({'status': 'success', 'qr_url': qr_url})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def save_qr(request):
    qr_code = request.GET.get('qr_code')
    product = Products.objects.get(code=qr_code)
    return JsonResponse({'product_id': product.id})

@login_required
def salesList(request):
    sales = Sales.objects.all()
    sale_data = []
    for sale in sales:
        data = {}
        for field in sale._meta.get_fields(include_parents=False):
            if field.related_model is None:
                data[field.name] = getattr(sale,field.name)
        data['items'] = salesItems.objects.filter(sale_id = sale).all()
        data['item_count'] = len(data['items'])
        if 'tax_amount' in data:
            data['tax_amount'] = format(float(data['tax_amount']),'.2f')
        # print(data)
        sale_data.append(data)
    # print(sale_data)
    context = {
        'page_title':'Transacsiones',
        'sale_data':sale_data,
    }
    # return HttpResponse('')
    return render(request, 'posApp/sales.html',context)

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
