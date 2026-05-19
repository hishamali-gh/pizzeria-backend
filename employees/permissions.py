from rest_framework import permissions


class IsTenantAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            return request.user.employee_profile.role in ['admin', 'superadmin']

        except AttributeError:
            return False


class IsWorker(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.employee_profile.role in ['worker', 'admin', 'superadmin']
