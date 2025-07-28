from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    def get_progress(self, obj):
        return obj.progress
    get_progress.short_description = 'Progress'

    list_display = ('title', 'project', 'user', 'is_done', 'is_archived', 'remind_at', 'due_at')
    list_filter = ('user', 'project', 'is_done', 'is_archived', 'created_at', 'remind_at', 'due_at')
    readonly_fields = ('created_at', 'updated_at', 'get_progress')
    search_fields = ('title', 'user__name', 'project')
    ordering = ('user', '-completed_at')

    fieldsets = (
        ('General', {'fields': ('user', 'title', 'project', 'notes')}),
        ('Status', {'fields': ('get_progress', 'is_done', 'is_archived')}),
        ('Dates', {'fields': ('remind_at', 'due_at', 'created_at', 'updated_at', 'completed_at')}),
    )
