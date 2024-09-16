from django.contrib import admin
from .models import Product

# Registre o modelo no admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description')
