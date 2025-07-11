from . import views
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic.base import RedirectView

urlpatterns = [
    path('redirect-admin', RedirectView.as_view(url="/admin"),name="redirect-admin"),
    path('', views.home, name="home-page"),
    path('login', auth_views.LoginView.as_view(template_name = 'posApp/login.html',redirect_authenticated_user=True), name="login"),
    path('userlogin', views.login_user, name="login-user"),
    path('logout', views.logoutuser, name="logout"),
    path('category', views.category, name="category-page"),
    path('manage_category', views.manage_category, name="manage_category-page"),
    path('save_category', views.save_category, name="save-category-page"),
    path('delete_category', views.delete_category, name="delete-category"),
    path('color', views.color, name="color-page"),
    path('manage_color', views.manage_color, name="manage_color-page"),
    path('save_color', views.save_color, name="save-color-page"),
    path('delete_color', views.delete_color, name="delete-color"),
    
    path('payment', views.payment, name="payment-page"),
    path('manage_payment', views.manage_payment, name="manage_payment-page"),
    path('save_payment', views.save_payment, name="save-payment-page"),
    path('delete_payment', views.delete_payment, name="delete-payment"),
    
    path('size', views.size, name="size-page"),
    path('manage_size', views.manage_size, name="manage_size-page"),
    path('save_size', views.save_size, name="save-size-page"),
    path('delete_size', views.delete_size, name="delete-size"),

    path('product', views.products, name="product-page"),
    path('manage_products', views.manage_products, name="manage_products-page"),
    path('test', views.test, name="test-page"),
    path('save_product', views.save_product, name="save-product-page"),
    path('delete_product', views.delete_product, name="delete-product"),
    path('generate_qr', views.generate_qr, name="generate-qr"),
    path('upload-file', views.upload_file, name='upload_file'),
    path('pos', views.pos, name="pos-page"),
    path('checkout-modal', views.checkout_modal, name="checkout-modal"),
    path('save-pos', views.save_pos, name="save-pos"),
    path('sales', views.salesList, name="sales-page"),
    path('receipt', views.receipt, name="receipt-modal"),
    path('receipt/pdf/', views.receipt_pdf, name='receipt_pdf'),
    path('delete_sale', views.delete_sale, name="delete-sale"),
    # path('employees', views.employees, name="employee-page"),
    # path('manage_employees', views.manage_employees, name="manage_employees-page"),
    # path('save_employee', views.save_employee, name="save-employee-page"),
    # path('delete_employee', views.delete_employee, name="delete-employee"),
    # path('view_employee', views.view_employee, name="view-employee-page"),
]


