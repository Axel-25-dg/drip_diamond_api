from rest_framework.permissions import BasePermission, SAFE_METHODS


class EsAdministrador(BasePermission):
    message = 'Solo el administrador puede realizar esta acción.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.es_administrador)


class EsContador(BasePermission):
    message = 'Solo el contador puede realizar esta acción.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.es_contador)


class EsVendedor(BasePermission):
    message = 'Solo un vendedor puede realizar esta acción.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.es_vendedor)


class EsCliente(BasePermission):
    message = 'Solo un usuario cliente puede realizar esta acción.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.es_cliente)


class EsAdministradorOContador(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.es_administrador or user.es_contador))


class SoloLecturaOAdministrador(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.es_administrador)



class EsDuenoOAdministrador(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.es_administrador or user.es_contador:
            return True
        propietario = getattr(obj, 'usuario', None) or getattr(obj, 'vendedor', None)
        return propietario == user
