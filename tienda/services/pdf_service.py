import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet


def generar_pdf_liquidaciones(anio: int, mes: int):
    """
    Genera un PDF con todos los vendedores, sus datos de pago y el estado
    de su liquidación del periodo. Devuelve un BytesIO listo para servir
    como archivo descargable.
    """
    from tienda.models import LiquidacionMensual

    liquidaciones = (
        LiquidacionMensual.objects
        .filter(periodo_anio=anio, periodo_mes=mes)
        .select_related('vendedor', 'vendedor__perfil_vendedor')
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph(f'Liquidación de comisiones — {mes:02d}/{anio}', estilos['Title']),
        Spacer(1, 0.5 * cm),
    ]

    encabezado = ['Vendedor', 'Código', 'Cuenta', 'Pares', 'Total', 'Estado']
    filas = [encabezado]
    total_general = 0

    for liq in liquidaciones:
        vendedor = liq.vendedor
        perfil = getattr(vendedor, 'perfil_vendedor', None)
        cuenta = f'{perfil.banco} {perfil.numero_cuenta}' if perfil else '—'
        filas.append([
            vendedor.nombre_completo,
            perfil.codigo_vendedor if perfil else '—',
            cuenta,
            str(liq.total_pares),
            f'${liq.total_comisiones}',
            'Pagada' if liq.pagada else 'Pendiente',
        ])
        total_general += liq.total_comisiones

    filas.append(['', '', '', '', f'Total: ${total_general}', ''])

    tabla = Table(filas, colWidths=[4 * cm, 2.5 * cm, 4 * cm, 1.8 * cm, 2.5 * cm, 2.5 * cm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111111')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
    ]))
    elementos.append(tabla)

    doc.build(elementos)
    buffer.seek(0)
    return buffer
