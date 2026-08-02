from django.contrib import admin
from django.contrib.auth.models import Group
from .core_models import Equipment

# 注册模型
admin.site.register(Equipment)

from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .core_models import UserProfile

# ==================== 注册 User 和 UserProfile ====================
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = '用户扩展信息'
    fk_name = 'user'

class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'is_staff', 'is_superuser', 'get_role')
    list_filter = ('is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'email')

    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except:
            return '-'
    get_role.short_description = '角色'

    # 禁止删除关键账号
    def has_delete_permission(self, request, obj=None):
        if obj and obj.username in ['superadmin', 'admin001', 'perry_chen']:
            return False
        return True

# 取消默认注册，重新注册
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# 注册 Group（可选）
admin.site.register(Group)

# 单独注册 UserProfile（方便查看）
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('work_number', 'name', 'role', 'department')
    list_filter = ('role',)
    search_fields = ('work_number', 'name')

    def has_delete_permission(self, request, obj=None):
        # 保护关键用户
        if obj and obj.user.username in ['superadmin', 'admin001', 'perry_chen']:
            return False
        return True