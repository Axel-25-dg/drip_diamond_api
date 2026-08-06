from rest_framework import permissions, status
from rest_framework.views import APIView

from core.responses import error_response, success_response
from tienda.models import Carrito, ItemCarrito, VarianteProducto
from tienda.serializers.pedido_serializers import CarritoSerializer


class CarritoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _obtener_carrito(self, usuario):
        carrito, _ = Carrito.objects.get_or_create(usuario=usuario)
        return carrito

    def get(self, request):
        carrito = self._obtener_carrito(request.user)
        return success_response(
            data=CarritoSerializer(carrito).data,
            message='Carrito obtenido exitosamente.',
        )

    def post(self, request):
        carrito = self._obtener_carrito(request.user)
        variante_id = request.data.get('variante_producto_id')
        try:
            cantidad = int(request.data.get('cantidad', 1))
        except (ValueError, TypeError):
            cantidad = 1

        variante = VarianteProducto.objects.filter(pk=variante_id).first()
        if not variante:
            return error_response(message='Variante de producto no encontrada.', status=status.HTTP_404_NOT_FOUND)
        if variante.stock < cantidad:
            return error_response(message='Stock insuficiente para esta talla/variante.', status=status.HTTP_400_BAD_REQUEST)

        item, creado = ItemCarrito.objects.get_or_create(
            carrito=carrito, variante_producto=variante, defaults={'cantidad': cantidad}
        )
        if not creado:
            item.cantidad += cantidad
            item.save(update_fields=['cantidad'])

        return success_response(
            data=CarritoSerializer(carrito).data,
            message='Producto agregado al carrito.',
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request):
        carrito = self._obtener_carrito(request.user)
        item_id = request.data.get('item_id')
        ItemCarrito.objects.filter(carrito=carrito, pk=item_id).delete()
        return success_response(
            data=CarritoSerializer(carrito).data,
            message='Item eliminado del carrito.',
        )
