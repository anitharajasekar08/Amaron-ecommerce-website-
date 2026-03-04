from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('', views.index_view, name='index'),
    path('shop/', views.shop_view, name='shop'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('service/', views.service, name='service'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("get-cart/", views.get_cart, name="get_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("update-cart/", views.update_cart, name="update_cart"),
    path("remove-cart/", views.remove_cart, name="remove_cart"),
    path("order-success/<int:order_id>/", views.order_success, name="order_success"),
path("register/", views.register, name="register"),
path("my-orders/", views.my_orders, name="my_orders"),
path("login/", auth_views.LoginView.as_view(), name="login"),
path("logout/", auth_views.LogoutView.as_view(next_page="index"), name="logout"),
path("success/", views.success, name="success"),
path("cancel-order/<int:order_id>/", views.cancel_order, name="cancel_order"),
path("download-invoice/<int:order_id>/", views.download_invoice, name="download_invoice"),
path('wishlist/', views.wishlist, name='wishlist'),
path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
path('edit-address/<int:id>/', views.edit_address, name='edit_address'),
]