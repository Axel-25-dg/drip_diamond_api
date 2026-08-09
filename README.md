# Zapatillas EC — Enterprise Backend API

> **Stack:** Django 5 · Django REST Framework · PostgreSQL · JWT · Resend · Argon2id · drf-spectacular

---

## Resumen del Backend

Backend Django REST para tienda de zapatillas con:
- roles: cliente, vendedor, contador, administrador
- autenticación JWT + recuperación de contraseña por OTP
- carrito y checkout con selección de vendedor
- comprobantes de pago y verificación
- pedido por estados con control de transiciones
- comisión fija por par y liquidaciones mensuales
- gestión de imágenes y envío local de archivos

Prefijo API base: `/api/`

---

## Endpoints clave

### Autenticación
| Método | Ruta | Descripción |
|---|---|
| POST | `/api/auth/login/` | Login con `username` o `correo` + `password` |
| POST | `/api/auth/logout/` | Cerrar sesión invalidando refresh token |
| POST | `/api/auth/refresh/` | Renovar access token |
| POST | `/api/auth/recuperar-password/` | Solicitar OTP por correo |
| POST | `/api/auth/verificar-otp/` | Verificar código OTP |
| POST | `/api/auth/confirmar-password/` | Restablecer contraseña |

### Usuarios
| Método | Ruta | Descripción |
|---|---|
| POST | `/api/usuarios/registro/` | Registrar cliente |
| GET | `/api/usuarios/me/` | Obtener perfil propio |
| PATCH | `/api/usuarios/me/` | Actualizar perfil propio (incluye `foto_perfil`) |
| GET | `/api/usuarios/vendedores/activos/` | Listar vendedores activos para checkout |
| POST | `/api/usuarios/vendedores/crear/` | Crear vendedor (Admin) |
| POST | `/api/usuarios/contadores/crear/` | Crear contador (Admin) |
| GET | `/api/usuarios/verificar-username/` | Verificar disponibilidad de username |

### Catálogo
| Método | Ruta | Descripción |
|---|---|
| GET | `/api/productos/` | Listar productos activos |
| GET | `/api/productos/{id}/` | Detalle de producto |
| GET | `/api/marcas/` | Listar marcas |
| GET | `/api/categorias/` | Listar categorías |
| GET | `/api/tallas/` | Listar tallas |
| GET | `/api/variantes/` | Listar variantes |
| GET | `/api/promociones/` | Listar promociones |

### Carrito
| Método | Ruta | Descripción |
|---|---|
| GET | `/api/pedidos/carrito/` | Ver carrito actual |
| POST | `/api/pedidos/carrito/` | Agregar ítem al carrito |
| DELETE | `/api/pedidos/carrito/` | Eliminar ítem del carrito |

### Pedidos y Checkout
| Método | Ruta | Descripción |
|---|---|
| POST | `/api/pedidos/` | Crear pedido desde carrito |
| GET | `/api/pedidos/` | Listar pedidos según rol |
| GET | `/api/pedidos/{id}/` | Ver detalle de pedido |
| POST | `/api/pedidos/{id}/subir-comprobante/` | Subir comprobante de pago |
| PATCH | `/api/pedidos/{id}/definir-costo-envio/` | Definir costo de envío (Admin) |
| POST | `/api/pedidos/{id}/marcar-enviado/` | Marcar pedido como enviado (Admin/Contador) |
| POST | `/api/pedidos/{id}/marcar-contactado/` | Marcar pago en revisión (Admin/Contador) |
| POST | `/api/pedidos/{id}/marcar-entregado/` | Confirmar entrega y generar comisión (Admin/Contador) |
| GET | `/api/pedidos/historial/` | Historial de compras del cliente |

### Comprobantes y pagos
| Método | Ruta | Descripción |
|---|---|
| PATCH | `/api/pedidos/comprobantes/{id}/verificar/` | Aprobar o rechazar comprobante (Contador/Admin) |

### Costos de envío
| Método | Ruta | Descripción |
|---|---|
| GET | `/api/costos-envio/` | Listar zonas y costos |
| POST | `/api/costos-envio/` | Crear zona de envío (Admin) |
| PATCH | `/api/costos-envio/{id}/` | Actualizar zona de envío (Admin) |

### Comisiones y liquidaciones
| Método | Ruta | Descripción |
|---|---|
| GET | `/api/comisiones/` | Ver comisiones |
| GET | `/api/comisiones/resumen-vendedor/` | Resumen de ventas y comisiones |
| GET | `/api/liquidaciones/` | Ver liquidaciones |
| POST | `/api/liquidaciones/generar/` | Generar liquidación mensual |
| POST | `/api/liquidaciones/{id}/marcar-pagada/` | Marcar liquidación como pagada (Contador) |
| GET | `/api/liquidaciones/pdf/?anio=&mes=` | Descargar PDF de liquidaciones |

### Documentación automática
| Método | Ruta | Descripción |
|---|---|
| GET | `/api/schema/` | OpenAPI schema |
| GET | `/api/docs/` | Swagger UI |
| GET | `/api/redoc/` | ReDoc |

---

## Ejemplos clave

### Login
```json
{
  "correo": "cliente@example.com",
  "password": "Password123!"
}
```

### Crear pedido en checkout
```json
{
  "vendedor_id": 42,
  "tipo_entrega": "DOMICILIO",
  "direccion_formateada": "Av. Principal 123",
  "referencia_adicional": "Puerta azul",
  "ciudad": "Quito"
}
```

### Actualizar perfil con foto
Encabezados:
- `Content-Type: multipart/form-data`
- `Authorization: Bearer <token>`

Campos:
- `correo`
- `nombre`
- `apellido`
- `telefono`
- `direccion_referencial`
- `foto_perfil`

### Verificar comprobante de pago
```json
{
  "estado": "VERIFICADO",
  "observacion": "Pago correcto"
}
```

### Generar liquidación mensual
```json
{
  "vendedor_id": 42,
  "anio": 2026,
  "mes": 8
}
```

---

## Flujo de vendedor y comisiones

1. El cliente abre checkout y obtiene los vendedores activos con `GET /api/usuarios/vendedores/activos/`.
2. Si elige vendedor, envía `vendedor_id` en `POST /api/pedidos/`.
3. El cliente sube comprobante con `POST /api/pedidos/{id}/subir-comprobante/`.
4. El contador verifica el comprobante con `PATCH /api/pedidos/comprobantes/{id}/verificar/`.
5. Si se aprueba, el pedido pasa a `PAGO_APROBADO`.
6. Admin/contador marca el pedido como enviado y luego como entregado.
7. Al confirmar entrega, se genera automáticamente `ComisionVenta` para el vendedor.

> Si no hay `vendedor_id`, no se crea comisión de vendedor.

---

## Campos importantes para el frontend

### En perfil
- `correo` → alias de `email`
- `nombre` → alias de `primer_nombre`
- `apellido` → alias de `primer_apellido`
- `foto_perfil` → imagen de perfil

### En pedido
- `vendedor` → ID del vendedor seleccionado
- `vendedor_codigo` → código del vendedor asignado
- `detalles` → lista de productos comprados
- `direccion_envio` → dirección utilizada
- `comprobante_pago` → comprobante subido

### En comisiones/liquidaciones
- `ComisionVenta.monto` → total de comisión por pedido
- `ComisionVenta.estado` → `PENDIENTE` / `LIQUIDADA`
- `LiquidacionMensual.pagada` → si la liquidación ya fue pagada

---

## Modelos principales

### Usuario
- `username`
- `email`
- `primer_nombre`
- `segundo_nombre`
- `primer_apellido`
- `segundo_apellido`
- `rol` (`ADMINISTRADOR`, `CONTADOR`, `VENDEDOR`, `CLIENTE`)
- `telefono`
- `direccion_referencial`
- `foto_perfil`

### PerfilVendedor
- `usuario`, `codigo_vendedor`, `activo`, `banco`, `tipo_cuenta`, `numero_cuenta`

### Producto
- `marca`, `categoria`, `nombre`, `modelo`, `codigo`, `calidad`, `descripcion`, `precio_base`, `imagen_principal`, `activo`

### VarianteProducto
- `producto`, `talla`, `stock`, `peso_kg`, `sku`

### Pedido
- `usuario`, `vendedor`, `tipo_entrega`, `costo_envio`, `subtotal`, `total`, `estado`, `numero_guia`, `direccion_envio`

### DetallePedido
- `variante_producto`, `cantidad`, `precio_unitario`, `subtotal`

### ComprobantePago
- `pedido`, `archivo`, `banco_origen`, `numero_referencia`, `monto_declarado`, `estado`, `verificado_por`, `fecha_verificacion`, `observacion`

### ComisionVenta
- `pedido`, `vendedor`, `cantidad_pares`, `monto_por_par`, `monto`, `estado`, `liquidacion`, `confirmada_por`

### LiquidacionMensual
- `vendedor`, `periodo_anio`, `periodo_mes`, `total_pares`, `total_comisiones`, `pagada`, `comprobante_pago`

---

## Observaciones finales

- El cliente puede ver vendedores activos en `/api/usuarios/vendedores/activos/`.
- El frontend debe enviar `vendedor_id` en el checkout si el cliente selecciona vendedor.
- `PATCH /api/usuarios/me/` acepta `multipart/form-data` para `foto_perfil` y alias de campos `correo`, `nombre`, `apellido`.
- Las imágenes de perfil devuelven URL absoluta cuando se incluye el request en el serializer.
- Las comisiones se crean solo cuando el pedido es marcado como entregado.
