from django.contrib import admin
from .models import Category, Product, Order, Cart, CartItem, Review

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'user_id', 'total_price', 'shipping_cost', 'grand_total', 'status')
    list_filter = ('status',) 
    search_fields = ('id', 'user__username')
    actions = ['mark_as_shipped']

    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
        self.message_user(request, "Selected orders have been marked as shipped.")
    mark_as_shipped.short_description = "Mark selected orders as shipped"

    def user_id(self, obj):
        return obj.user.id
    user_id.short_description = 'User ID'

@admin.action(description="Set as shipped")
def setShipped(modeladmin, request, queryset):
    queryset.update(status='shipped')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_price', 'status', 'user',)
    actions = [setShipped]

admin.site.register(Review)
