from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework import permissions

class IsAdminOrReadOnly(BasePermission):
    """GET/HEAD/OPTIONS sabke liye open, POST/PUT/PATCH/DELETE sirf staff/admin"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
        
        

class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """Read = everyone (auth). Write = sirf owner ya admin."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or obj.owner_id == request.user.id