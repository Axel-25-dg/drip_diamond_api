from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from tienda.models import Carrito, ItemCarrito, VarianteProducto
from tienda.serializers.pedido_serializers import CarritoSerializer


class CarritoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _obtener_carrito(self, usuario):
        carrito, _ = Carrito.objects.get_or_create(usuario=usuario)
        return carrito

    def get(self, request):
        return Response(CarritoSerializer(self._obtener_carrito(request.user)).data)

    def post(self, request):
        carrito = self._obtener_carrito(request.user)
        variante_id = request.data.get('variante_producto_id')
        cantidad = int(request.data.get('cantidad', 1))

        variante = VarianteProducto.objects.filter(pk=variante_id).first()
        if not variante:
            return Response({'detail': 'Variante no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        if variante.stock < cantidad:
            return Response({'detail': 'Stock insuficiente.'}, status=status.HTTP_400_BAD_REQUEST)

        item, creado = ItemCarrito.objects.get_or_create(
            carrito=carrito, variante_producto=variante, defaults={'cantidad': cantidad}
        )
        if not creado:
            item.cantidad += cantidad
            item.save(update_fields=['cantidad'])

        return Response(CarritoSerializer(carrito).data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        carrito = self._obtener_carrito(request.user)
        ItemCarrito.objects.filter(carrito=carrito, pk=request.data.get('item_id')).delete()
        return Response(CarritoSerializer(carrito).data)
