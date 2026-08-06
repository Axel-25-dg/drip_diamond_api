# Zapatillas EC — Enterprise Backend API

> **Stack:** Django 5 · Django REST Framework · PostgreSQL · JWT · Resend · Argon2id · drf-spectacular

---

## Arquitectura

Sigue **Clean Architecture** con separación total de responsabilidades:

```
zapatillas_api/
├── config/              # Configuración central (settings, urls, wsgi, asgi)
├── core/                # Módulo transversal: respuestas estandarizadas + manejador de excepciones
├── seguridad_acceso/    # Autenticación, intentos de login, IPs bloqueadas, OTP, auditoría
├── tienda/
│   ├── models/          # Modelos de dominio separados por entidad
│   ├── serializers/     # Serializers de entrada y salida
│   ├── views/           # Vistas delgadas (sin lógica de negocio)
│   ├── services/        # Capa de servicios (lógica de negocio aquí)
│   ├── permissions/     # Permisos reutilizables por rol (RBAC)
│   ├── tests/           # Suite de pruebas (auth, imágenes, flujo de compra completo)
│   └── signals.py       # Automatizaciones via Django signals
├── templates/emails/    # Templates HTML de correos (Resend)
└── media/               # Almacenamiento local organizado por módulo
```

**Principios aplicados:** SOLID · DRY · KISS · Clean Code · Repository Pattern · Service Layer · Type Hints

---

## Módulos del Sistema

### 🔐 Autenticación y Seguridad
| Característica | Detalle |
|---|---|
| Contraseñas | **Argon2id** (nunca texto plano, salt aleatorio automático) |
| Tokens | JWT con Refresh Token + Rotación + Blacklist (SimpleJWT) |
| Sesiones | Invalidación automática de todas las sesiones al cambiar contraseña |
| Rate Limiting | `5/min` login · `30/min` anónimos · `120/min` usuarios autenticados |
| Brute Force | Bloqueo de IP tras 5 intentos fallidos (15 min) |
| Headers | XSS Filter · Content-Type Nosniff · X-Frame DENY · HSTS en producción |
| Auditoría | Log de cada acción (modelo, objeto, IP, usuario, timestamp) |
| SQL Injection | 100% ORM de Django, cero queries en crudo |

### 👤 Usuarios y RBAC
| Rol | Capacidades |
|---|---|
| **Administrador** | Acceso total al sistema |
| **Contador** | Ver comprobantes, aprobar/rechazar pagos, marcar liquidaciones pagadas |
| **Vendedor** | Ver sus ventas asignadas, historial, comisiones |
| **Cliente** | Gestión de carrito, pedidos, comprobantes y perfil |

**Registro público solo requiere:** nombre · apellido · correo · teléfono · contraseña _(sin cédula, RUC ni pasaporte)_

### 🔑 Recuperación de Contraseña (OTP)
Flujo de 3 pasos completamente seguro:

1. `POST /api/auth/recuperar-password/` → envía **código OTP de 6 dígitos** por correo (Resend)
2. `POST /api/auth/verificar-otp/` → verifica código (máx. 5 intentos · expira en 10 minutos)
3. `POST /api/auth/confirmar-password/` → establece nueva contraseña · invalida todas las sesiones anteriores

### 📦 Catálogo de Zapatillas
Cada producto tiene: nombre · marca · modelo · categoría · subcategoría · calidad · descripción · precio base · precio oferta · stock · estado · etiquetas · imagen principal · galería de imágenes · fecha creación/actualización

**Variantes por producto:** cada zapatilla soporta múltiples combinaciones de `talla + color`, cada variante controla su propio stock de manera independiente.

### 🖼️ Gestión de Imágenes (Almacenamiento Local)
Sin Cloudinary · Sin S3 · Sin Azure — almacenamiento local configurado en `MEDIA_ROOT` con rutas organizadas por módulo:

```
media/
    usuarios/perfiles/       ← fotos de perfil
    productos/zapatillas/    ← imágenes de productos
    categorias/              ← imágenes de categorías
    marcas/                  ← logos de marcas
    banners/                 ← banners
    promociones/             ← imágenes promocionales
    comprobantes/            ← vouchers de pago
    otros/                   ← archivos genéricos
```

**Validaciones en `imagen_service.py`:**
- Validación de extensión (jpg · jpeg · png · webp)
- Validación MIME real con Pillow (previene ejecutables disfrazados)
- Máximo 5 MB por archivo
- Nombres únicos con UUID4 (evita colisiones)
- Arquitectura preparada para migrar a Cloudinary/S3 sin modificar lógica de negocio

### 📧 Sistema de Correos (Resend — sin SMTP)
Todos los correos se envían exclusivamente via **API HTTP de Resend** (no SMTP).

**Correos automáticos implementados:**
| Evento | Template |
|---|---|
| Registro de usuario | `bienvenida.html` |
| Código OTP | `codigo_otp.html` |
| Solicitud de compra | `solicitud_compra.html` |
| Comprobante recibido | `comprobante_recibido.html` |
| Pago verificado/aprobado | `pago_verificado.html` |
| Pago rechazado | `pago_rechazado.html` |
| Ticket de compra | `ticket_compra.html` |
| Pedido enviado | `pedido_enviado.html` |
| Pedido entregado | `pedido_entregado.html` |
| Comisión pagada | `comision_pagada.html` |
| Promoción | `promocion.html` |
| Alerta de seguridad | `alerta_seguridad.html` |
| Recuperación de contraseña (enlace) | `recuperar_password.html` |

**Campañas de correos masivos** (`CampanaEmail`): segmentado por rol, con historial, plantillas reutilizables y preparado para colas (Celery).

### 🛒 Flujo de Compra Completo

```
Cliente → Carrito → Pedido (Pendiente de pago)
       ↓
   Sube comprobante (Comprobante enviado)
       ↓
   Contador revisa → Aprueba o Rechaza
       ↓ (Aprobado → Pago aprobado)
   Notificación automática a cliente, vendedor y admin
       ↓
   Admin prepara y despacha (Enviado)
       ↓
   Contador confirma entrega (Entregado / Venta finalizada)
       ↓
   Se genera comisión automáticamente
```

**Selector de Vendedor (obligatorio en checkout):**
- Lista de vendedores activos para elegir
- Opción "Ningún vendedor" (sin comisión)
- Campo `vendedor` permite `null`

### 🏷️ Máquina de Estados de Pedidos
Solo permite transiciones válidas (previene estados inválidos):

```
CARRITO → PENDIENTE_DE_PAGO → COMPROBANTE_ENVIADO → PAGO_EN_REVISION
                                                   ↓                ↓
                                           PAGO_APROBADO    PAGO_RECHAZADO
                                                   ↓
                                         PREPARANDO_PEDIDO → ENVIADO → ENTREGADO
                                                                     ↓
                                                                  CANCELADO
```

### 💰 Comisiones de Vendedores
| Condición | Resultado |
|---|---|
| Vendedor asignado + Pago aprobado + Pedido entregado | **$4.00 USD fijos** |
| Ningún vendedor seleccionado | **$0.00** (sin registro de comisión) |

El cálculo es **automático** al confirmar la entrega. El contador puede cerrar liquidaciones mensuales y marcarlas como pagadas.

### 📊 Módulo de Vendedores (Dashboard)
`GET /api/comisiones/resumen-vendedor/` devuelve:
- Ventas asignadas totales
- Ventas pendientes, pagadas y entregadas
- Total vendido ($)
- Total de comisiones acumuladas
- Comisiones pendientes de pago
- Comisiones ya pagadas (liquidadas)

### 📋 Módulo de Contador
Acciones permitidas (solo estas):
1. Ver comprobantes de pago
2. Aprobar pago (`VERIFICADO`) — dispara: factura automática + correo al cliente
3. Rechazar pago (`RECHAZADO`) — dispara: correo al cliente
4. Marcar liquidación mensual como pagada
5. Confirmar entrega de pedido (dispara comisión al vendedor)

### 🚚 Costos de Envío
El sistema calcula el costo desde `CostoEnvioZona` (tabla editable por el admin) según provincia/ciudad/zona. Sin APIs externas de paquetería. El administrador puede definirlo manualmente por pedido.

---

## Documentación API (auto-generada)

| Endpoint | Descripción |
|---|---|
| `GET /api/docs/` | **Swagger UI** interactivo |
| `GET /api/redoc/` | **Redoc** (documentación limpia) |
| `GET /api/schema/` | Esquema OpenAPI 3 en JSON/YAML |

---

## Endpoints Principales

### Autenticación
```
POST   /api/auth/login/                  ← Iniciar sesión (JWT)
POST   /api/auth/logout/                 ← Cerrar sesión (blacklist token)
POST   /api/auth/refresh/                ← Renovar access token
POST   /api/auth/recuperar-password/     ← Solicitar OTP por correo
POST   /api/auth/verificar-otp/          ← Verificar código OTP (6 dígitos)
POST   /api/auth/confirmar-password/     ← Establecer nueva contraseña
```

### Usuarios
```
POST   /api/usuarios/registro/           ← Registro público de clientes
GET    /api/usuarios/me/                 ← Perfil propio (autenticado)
PATCH  /api/usuarios/me/                 ← Actualizar perfil
GET    /api/usuarios/vendedores/activos/ ← Lista vendedores (para checkout)
POST   /api/usuarios/vendedores/crear/   ← Crear vendedor (Admin)
POST   /api/usuarios/contadores/crear/   ← Crear contador (Admin)
GET    /api/usuarios/verificar-username/ ← Verificar disponibilidad username
```

### Catálogo
```
GET    /api/productos/                   ← Listar productos (filtro, búsqueda, orden)
GET    /api/productos/{id}/              ← Detalle de producto + galería + variantes
GET    /api/marcas/                      ← Listar marcas
GET    /api/categorias/                  ← Listar categorías
GET    /api/tallas/                      ← Listar tallas disponibles
GET    /api/variantes/                   ← Listar variantes con stock
GET    /api/promociones/                 ← Listar promociones activas
```

### Imágenes
```
POST   /api/imagenes/subir/              ← Subir imagen (devuelve {id, url})
GET    /api/imagenes/?content_type=&object_id=  ← Listar imágenes de un objeto
DELETE /api/imagenes/{id}/              ← Eliminar imagen
```

### Carrito
```
GET    /api/pedidos/carrito/             ← Ver carrito actual
POST   /api/pedidos/carrito/             ← Agregar item al carrito
DELETE /api/pedidos/carrito/             ← Eliminar item del carrito
```

### Pedidos
```
POST   /api/pedidos/                     ← Crear pedido desde carrito (checkout)
GET    /api/pedidos/                     ← Listar pedidos (filtrado por rol)
GET    /api/pedidos/{id}/                ← Detalle de pedido
POST   /api/pedidos/{id}/subir-comprobante/     ← Cliente sube voucher
PATCH  /api/pedidos/{id}/definir-costo-envio/   ← Admin define costo envío
POST   /api/pedidos/{id}/marcar-enviado/        ← Admin marca como enviado
POST   /api/pedidos/{id}/marcar-contactado/     ← Admin/Contador actualiza estado
GET    /api/pedidos/historial/           ← Historial de compras del cliente
```

### Pagos
```
PATCH  /api/pedidos/comprobantes/{id}/verificar/  ← Contador aprueba/rechaza pago
```

### Envíos
```
GET    /api/costos-envio/                ← Listar zonas y costos
POST   /api/costos-envio/               ← Crear zona (Admin)
PATCH  /api/costos-envio/{id}/          ← Editar costo (Admin)
```

### Comisiones y Liquidaciones
```
GET    /api/comisiones/                  ← Listar comisiones (filtrado por rol)
GET    /api/comisiones/resumen-vendedor/ ← Dashboard del vendedor
GET    /api/liquidaciones/               ← Listar liquidaciones mensuales
POST   /api/liquidaciones/generar/       ← Generar liquidación mensual
POST   /api/liquidaciones/{id}/marcar-pagada/  ← Contador marca como pagada
GET    /api/liquidaciones/pdf/?anio=&mes=      ← PDF de liquidaciones
```

### Contabilidad
```
GET    /api/facturas/                    ← Ver facturas (Admin/Contador)
GET    /api/notas-credito/               ← Ver notas de crédito
GET    /api/retenciones/                 ← Ver retenciones
GET    /api/libro-ventas/                ← Libro de ventas
POST   /api/libro-ventas/cerrar/         ← Cerrar libro mensual
GET    /api/reportes-sri/                ← Reportes SRI
```

### Notificaciones
```
GET    /api/notificaciones/              ← Notificaciones del usuario autenticado
PATCH  /api/notificaciones/{id}/marcar_leida/  ← Marcar como leída
```

### Seguridad (Admin)
```
GET    /api/seguridad/intentos/          ← Intentos de login
GET    /api/seguridad/ips-bloqueadas/    ← IPs bloqueadas
GET    /api/seguridad/auditoria/         ← Log de auditoría
```

---

## Formato de Respuestas (Estándar Uniforme)

**Éxito:**
```json
{
    "success": true,
    "message": "Operación realizada correctamente.",
    "data": {}
}
```

**Error:**
```json
{
    "success": false,
    "message": "Error de validación.",
    "errors": {}
}
```

Todas las respuestas usan este formato gracias a `core/responses.py` y el manejador global en `core/exceptions.py`.

---

## Variables de Entorno (.env)

```env
SECRET_KEY=django-insecure-change-this-in-production

DEBUG=True

ALLOWED_HOSTS=127.0.0.1,localhost,178.105.61.61

CSRF_TRUSTED_ORIGINS=

DB_NAME=languageapi_db
DB_USER=postgres
DB_PASSWORD=admin
DB_HOST=localhost
DB_PORT=5432

CORS_ALLOW_ALL_ORIGINS=True

DEFAULT_FROM_EMAIL=no-responder@zapatillas.ec
RESEND_API_KEY=re_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

> ⚠️ El archivo `.env.example` es ignorado. El único archivo de configuración es `.env`.

---

## Instalación

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
.\venv\Scripts\Activate.ps1     # Windows PowerShell

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
# (editar .env con tus credenciales)

# 4. Aplicar migraciones
python manage.py migrate

# 5. Crear superusuario administrador
python manage.py createsuperuser

# 6. Ejecutar servidor de desarrollo
python manage.py runserver
```

---

## Tests

```bash
# Ejecutar todos los tests
python manage.py test

# Con detalle
python manage.py test --verbosity=2
```

**Tests incluidos:**
| Módulo | Tests |
|---|---|
| `test_auth.py` | Login exitoso · Registro sin cédula · Flujo OTP completo |
| `test_imagenes.py` | Subida de imagen válida con validación MIME |
| `test_compra_flujo.py` | Flujo completo con vendedor + comisión $4 USD · Flujo sin vendedor ($0 comisión) |

---

## Seguridad en Producción

Cuando `DEBUG=False`:
- `SECURE_SSL_REDIRECT = True`
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- `SECURE_HSTS_SECONDS = 31536000` (1 año)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- `SECURE_HSTS_PRELOAD = True`

---

## Decisiones Arquitectónicas

| Decisión | Razón |
|---|---|
| **Argon2id para passwords** | Algoritmo más resistente a ataques de fuerza bruta (ganador PHC 2015) |
| **Resend (HTTP) en lugar de SMTP** | Sin configuración de servidor de correo, confiable y con logs |
| **OTP de 6 dígitos** | Más usable que links de email (no requiere frontend URL) |
| **Vendedor null en pedido** | Permite ventas sin comisión sin afectar la integridad del modelo |
| **Máquina de estados** | Previene transiciones inválidas (ej: ENTREGADO → PENDIENTE) |
| **Comisión fija $4 USD por pedido** | No por par — simplifica el cálculo y es predecible |
| **GenericForeignKey para imágenes** | Un solo modelo de imagen reutilizable en todo el sistema |
| **Almacenamiento local organizado** | Carpetas por módulo, UUID para nombres, preparado para S3/Cloudinary |
| **core/ desacoplado** | `responses.py` y `exceptions.py` disponibles para cualquier app |
| **drf-spectacular** | Swagger/Redoc auto-generado desde el código, siempre actualizado |
