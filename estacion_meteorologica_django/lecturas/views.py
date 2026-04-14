from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Avg, Max
from django.utils.timezone import now, localtime
from datetime import timedelta, datetime

from .models import Lectura, Alarma

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

@login_required
def lista_lecturas(request):
    lecturas = Lectura.objects.all().order_by('-fecha')
    alertas_display = [] 
    ultima_temp = lecturas.filter(sensor="temperatura").first()
    ultima_humedad = lecturas.filter(sensor="humedad").first()
    ultima_presion = lecturas.filter(sensor="presion").first()

    def procesar_alarma(lectura, condicion, mensaje):
        if lectura and lectura.valor is not None and condicion:
            if not Alarma.objects.filter(fecha=lectura.fecha, sensor=lectura.sensor, valor=lectura.valor).exists():
                Alarma.objects.create(
                    estacion=lectura.estacion,
                    sensor=lectura.sensor,
                    valor=lectura.valor,
                    fecha=lectura.fecha
                )
            return mensaje
        return None

    if ultima_temp:
        msg = None
        if ultima_temp.valor < 15:
            msg = procesar_alarma(ultima_temp, True, f"Temperatura baja detectada: {ultima_temp.valor} °C !!!")
        elif ultima_temp.valor > 35:
            msg = procesar_alarma(ultima_temp, True, f"Temperatura alta detectada: {ultima_temp.valor} °C !!!")
        if msg: alertas_display.append(msg)

    if ultima_humedad:
        msg = None
        if ultima_humedad.valor < 40:
            msg = procesar_alarma(ultima_humedad, True, f"Humedad baja detectada: {ultima_humedad.valor}% !!!")
        elif ultima_humedad.valor > 85:
            msg = procesar_alarma(ultima_humedad, True, f"Humedad alta detectada: {ultima_humedad.valor}% !!!")
        if msg: alertas_display.append(msg)

    if ultima_presion:
        msg = None
        if ultima_presion.valor < 980:
            msg = procesar_alarma(ultima_presion, True, f"Presión baja detectada: {ultima_presion.valor} hPa !!!")
        elif ultima_presion.valor > 1030:
            msg = procesar_alarma(ultima_presion, True, f"Presión alta detectada: {ultima_presion.valor} hPa !!!")
        if msg: alertas_display.append(msg)

    paginator = Paginator(lecturas, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "lecturas/lista.html", {
        "page_obj": page_obj,
        "alertas": alertas_display
    })


    
@login_required
def historial(request):

    lecturas = Lectura.objects.all().order_by('-fecha')

    sensor = request.GET.get("sensor")
    estacion = request.GET.get("estacion")
    fecha_inicio = request.GET.get("inicio")
    fecha_fin = request.GET.get("fin")

    if sensor:
        lecturas = lecturas.filter(sensor__icontains=sensor)

    if estacion:
        lecturas = lecturas.filter(estacion__icontains=estacion)

    if fecha_inicio:
        lecturas = lecturas.filter(fecha__gte=fecha_inicio)

    if fecha_fin:
        lecturas = lecturas.filter(fecha__lte=fecha_fin)

    paginator = Paginator(lecturas, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "historial.html", {
        "page_obj": page_obj,
        "sensor": sensor or "",
        "estacion": estacion or "",
        "inicio": fecha_inicio or "",
        "fin": fecha_fin or ""
    })


    

@login_required
def estaciones(request):
    estaciones_dict = {}
    alertas_estaciones = []
    
    ultimos_ids = (
        Lectura.objects.values('estacion')
        .annotate(max_id=Max('id'))
        .values_list('max_id', flat=True)
    )

    ultimas_lecturas = Lectura.objects.filter(id__in=ultimos_ids)

    for lectura in ultimas_lecturas:
        nombre = lectura.estacion
        if not lectura.fecha:
            continue

        ahora_sistema = datetime.now() 
        fecha_db_plana = lectura.fecha.replace(tzinfo=None)
        diferencia = ahora_sistema - fecha_db_plana

        if diferencia <= timedelta(minutes=5):
            estado = "Activa"
        elif diferencia <= timedelta(minutes=30):
            estado = "Inactiva"
        else:
            estado = "Sin comunicacion"
            alertas_estaciones.append(f"estacion {nombre} sin comunicacion")

        estaciones_dict[nombre] = {
            "ultima_lectura": lectura.fecha, # Puedes usar la original para el template
            "estado": estado,
            "sensor": lectura.sensor,
            "valor": lectura.valor
        }

    return render(request, "estaciones.html", {
        "estaciones": estaciones_dict,
        "alertas_estaciones": list(set(alertas_estaciones))
    })


@login_required
def alarmas(request):
    alarmas = Alarma.objects.all().order_by('-fecha')

    paginator = Paginator(alarmas, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "alarmas.html", {
        "page_obj": page_obj
    })

@login_required
def cerrar_sesion(request):
    logout(request)
    return redirect('/login/')


@login_required
def lecturas_json(request):
    lecturas = Lectura.objects.all().order_by('-fecha')[:10]

    data = []

    for lectura in lecturas:
        data.append({
            "id": lectura.id,
            "estacion": lectura.estacion,
            "sensor": lectura.sensor,
            "valor": lectura.valor,
            "fecha": lectura.fecha.strftime("%d/%m/%Y %H:%M:%S")
        })

    return JsonResponse({"lecturas": data})


@login_required
def estaciones_json(request):
    lecturas = Lectura.objects.order_by('-fecha')

    estaciones = {}

    for lectura in lecturas:
        nombre = lectura.estacion

        if nombre not in estaciones:

            diferencia = now() - lectura.fecha

            if diferencia <= timedelta(minutes=2):
                estado = "Activa"
            elif diferencia <= timedelta(minutes=10):
                estado = "Inactiva"
            else:
                estado = "Sin comunicacion"

            estaciones[nombre] = {
                "estado": estado,
                "ultima_lectura": lectura.fecha.strftime("%d/%m/%Y %H:%M:%S")
            }

    return JsonResponse(estaciones)


@login_required
def obtener_lecturas_filtradas(request):
    """Función maestra de filtrado para Web y PDF"""
    lecturas = Lectura.objects.all().order_by('-fecha')
    
    sensor = request.GET.get("sensor", "")
    estacion = request.GET.get("estacion", "")
    inicio = request.GET.get("inicio", "")
    fin = request.GET.get("fin", "")

    if sensor:
        lecturas = lecturas.filter(sensor__icontains=sensor)
    if estacion:
        lecturas = lecturas.filter(estacion__icontains=estacion)
    
    if inicio:
        inicio_limpio = inicio.replace('T', ' ')
        lecturas = lecturas.filter(fecha__gte=inicio_limpio)
            
    if fin:
        fin_limpio = fin.replace('T', ' ')
        lecturas = lecturas.filter(fecha__lte=fin_limpio)

    return lecturas, sensor, estacion, inicio, fin

@login_required
def reportes(request):

    lecturas_filtradas, sensor, estacion, inicio, fin = obtener_lecturas_filtradas(request)
    
    total = lecturas_filtradas.count()
    promedio = lecturas_filtradas.aggregate(Avg('valor'))['valor__avg'] or 0
    ultima = lecturas_filtradas.first()

    paginator = Paginator(lecturas_filtradas, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, "reportes.html", {
        "page_obj": page_obj,
        "sensor": sensor,
        "estacion": estacion,
        "inicio": inicio,
        "fin": fin,
        "total": total,
        "promedio": round(promedio, 2),
        "ultima": ultima,
    })

@login_required
def generar_reporte_pdf(request):

    lecturas, sensor, estacion, inicio, fin = obtener_lecturas_filtradas(request)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_{now().strftime("%Y%m%d_%H%M")}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    titulo = f"Reporte: {estacion if estacion else 'Todas las estaciones'}"
    elements.append(Paragraph(titulo, styles['Title']))
    
    rango_fechas = f"Periodo: {inicio if inicio else 'Desde el inicio'} hasta {fin if fin else 'Actualidad'}"
    elements.append(Paragraph(rango_fechas, styles['Normal']))
    elements.append(Paragraph(f"Sensor: {sensor if sensor else 'Todos'}", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    data = [['estacion', 'sensor', 'valor', 'fecha']]
    for l in lecturas:
        fecha_local = localtime(l.fecha) 
        fecha_formateada = fecha_local.strftime('%d/%m/%Y %H:%M:%S')
        
        data.append([l.estacion, l.sensor, l.valor, fecha_formateada])
        
    tabla = Table(data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    
    elements.append(tabla)
    doc.build(elements)
    return response


@login_required
def eliminar_data_view(request):
    if request.method == "POST":
        inicio = request.POST.get("inicio_borrar")
        fin = request.POST.get("fin_borrar")

        if inicio and fin:
            inicio_limpio = inicio.replace('T', ' ')
            fin_limpio = fin.replace('T', ' ')
            
            queryset = Lectura.objects.filter(fecha__gte=inicio_limpio, fecha__lte=fin_limpio)
            cantidad = queryset.count()
            queryset.delete()
            
            messages.success(request, f"Éxito: Se han eliminado {cantidad} registros.")
        else:
            messages.error(request, "Error: Debes indicar ambos rangos de tiempo.")
            
    return render(request, 'eliminar.html')
