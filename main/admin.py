from django.contrib import admin
from .models import Post, Subscribe, CustomUser, Subscribe_plan

@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'isAuthor',)
    list_filter = ('username', 'isAuthor',)
    search_fields = ('username',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'header','text',)
    list_filter = ('author',)
    search_fields = ('author', 'header,')

@admin.register(Subscribe_plan)
class Subscribe_planAdmin(admin.ModelAdmin):
    list_display = ('name', 'price',)
    list_filter = ('name', 'price',)
    search_fields = ('name', 'price',)

@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    search_fields = ('subscriber',)
