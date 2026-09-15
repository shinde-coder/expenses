from django.contrib import admin

from families.models import Family, FamilyInvitation, FamilyMember


class FamilyMemberInline(admin.TabularInline):
    model = FamilyMember
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ("name", "currency", "created_by", "created_at")
    search_fields = ("name",)
    list_filter = ("currency",)
    autocomplete_fields = ("created_by",)
    inlines = (FamilyMemberInline,)


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ("display_name", "family", "relationship", "role", "user", "is_active")
    list_filter = ("relationship", "is_active")
    search_fields = ("display_name", "family__name", "user__email")
    autocomplete_fields = ("family", "user")


@admin.register(FamilyInvitation)
class FamilyInvitationAdmin(admin.ModelAdmin):
    list_display = ("code", "family", "expires_at", "accepted_at")
    search_fields = ("code", "family__name")
