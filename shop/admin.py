from django.contrib import admin
from .models import Address
from .models import Product, ProductImage,ProductFeature,Order, OrderItem
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline, ProductFeatureInline]
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'payment_method', 'payment_status', 'status')
    list_filter = ('payment_method', 'payment_status', 'status')
    search_fields = ('user__username', 'upi_transaction_id')
admin.site.register(Product, ProductAdmin)
admin.site.register(OrderItem)
admin.site.register(Address)