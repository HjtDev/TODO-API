from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import UserCreationForm, UserChangeFormNew
from django.contrib.auth.models import Group

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(UserAdmin):
    ordering = ['phone']

    add_form = UserCreationForm
    form = UserChangeFormNew
    model = User

    search_fields = [
        'phone',
        'name',
        'email'
    ]

    list_display = [
        'id',
        'phone',
        'name',
        'email',
        'is_active',
        'is_staff',
    ]

    fieldsets = (
        ('General', {'fields': ('phone', 'password')}),
        ('Personal', {'fields': ('name', 'email', 'profile')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        ('General', {'fields': ('phone', 'password1', 'password2')}),
        ('Personal', {'fields': ('name', 'email', 'profile', 'compare_list')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
