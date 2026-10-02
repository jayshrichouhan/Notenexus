from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from .models import ContactMessage, FeedbackMessage, NoteComment, NoteRating, UploadedNote



admin.site.register(ContactMessage)
admin.site.register(FeedbackMessage)


@admin.register(UploadedNote)
class UploadedNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploader', 'uploader_role', 'status', 'view_count', 'download_count', 'original_filename', 'created_at')
    list_filter = ('uploader_role', 'status', 'created_at')
    search_fields = ('title', 'description', 'uploader__username', 'uploader_name', 'original_filename')
    readonly_fields = ('document_url', 'cloudinary_public_id', 'cloudinary_resource_type', 'file_size', 'view_count', 'download_count', 'created_at')


@admin.register(NoteRating)
class NoteRatingAdmin(admin.ModelAdmin):
    list_display = ('note', 'user', 'stars', 'updated_at')
    list_filter = ('stars', 'updated_at')
    search_fields = ('note__title', 'user__username')


@admin.register(NoteComment)
class NoteCommentAdmin(admin.ModelAdmin):
    list_display = ('note', 'user', 'created_at')
    search_fields = ('note__title', 'user__username', 'comment')

class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
        'is_staff',
        'is_active',
        'date_joined',
    )
    list_filter = ('groups', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    actions = ['make_instructor', 'make_student', 'remove_instructor', 'remove_student']

    def role(self, obj):
        if obj.groups.filter(name='Instructors').exists():
            return 'Instructor'
        if obj.groups.filter(name='Students').exists():
            return 'Student'
        return 'Member'
    role.short_description = 'Role'

    def make_instructor(self, request, queryset):
        instructor_group, _ = Group.objects.get_or_create(name='Instructors')
        student_group, _ = Group.objects.get_or_create(name='Students')
        for user in queryset:
            user.groups.add(instructor_group)
            user.groups.remove(student_group)
        self.message_user(request, 'Selected users have been assigned Instructor role.')
    make_instructor.short_description = 'Make selected users instructors'

    def make_student(self, request, queryset):
        student_group, _ = Group.objects.get_or_create(name='Students')
        instructor_group, _ = Group.objects.get_or_create(name='Instructors')
        for user in queryset:
            user.groups.add(student_group)
            user.groups.remove(instructor_group)
        self.message_user(request, 'Selected users have been assigned Student role.')
    make_student.short_description = 'Make selected users students'

    def remove_instructor(self, request, queryset):
        instructor_group, _ = Group.objects.get_or_create(name='Instructors')
        for user in queryset:
            user.groups.remove(instructor_group)
        self.message_user(request, 'Instructor role removed from selected users.')
    remove_instructor.short_description = 'Remove instructor role from selected users'

    def remove_student(self, request, queryset):
        student_group, _ = Group.objects.get_or_create(name='Students')
        for user in queryset:
            user.groups.remove(student_group)
        self.message_user(request, 'Student role removed from selected users.')
    remove_student.short_description = 'Remove student role from selected users'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


