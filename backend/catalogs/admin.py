from django.contrib import admin

from catalogs.models import Category, MasterValue, PaymentMethod, SubCategory


class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "family", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("name",)
    inlines = (SubCategoryInline,)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "family", "is_active")
    list_filter = ("is_active", "category__type")
    search_fields = ("name", "category__name")


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "family", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(MasterValue)
class MasterValueAdmin(admin.ModelAdmin):
    list_display = ("group", "code", "label", "sort_order", "is_active")
    list_filter = ("group", "is_active")
    search_fields = ("group", "code", "label")
    ordering = ("group", "sort_order", "label")
