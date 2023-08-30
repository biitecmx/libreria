from django.contrib import admin

from .models import Book, Category, OrderBook, Order, Address, ExtraImage


class ExtraImageAdmin(admin.StackedInline):
    model = ExtraImage
 
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    inlines = [ExtraImageAdmin]
 
    class Meta:
       model = Book
 
@admin.register(ExtraImage)
class ExtraImageAdmin(admin.ModelAdmin):
    pass

admin.site.register(OrderBook)
admin.site.register(Order)
admin.site.register(Address)
admin.site.register(Category)