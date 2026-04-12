from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils.timezone import now
from datetime import timedelta
from .models import Lectura
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from django.db.models import Max
from datetime import datetime

@login_required
def lista_lecturas(request):
    lecturas = Lectura.objects.all().order_by('-fecha')

    alertas = []
    temperatura_alta = False
    humedad_baja = False

    for lectura in lecturas:
        if lectura.sensor == "temperatura" and lectura.valor is not None and lectura.valor > 35:
            temperatura_alta = True

        if lectura.sensor == "humedad" and lectura.valor is not None and lectura.valor < 20:
            humedad_baja = True

    if temperatura_alta:
        alertas.append("Temperatura alta!!!")

    if humedad_baja:
        alertas.append("Humedad baja!!!")

    paginator = Paginator(lecturas, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "lecturas/lista.html", {
        "page_obj": page_obj,
        "alertas": alertas
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
    
    # 1. Obtenemos los últimos IDs
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

        # Lógica de tiempo corregida para el desfase
        ahora_sistema = datetime.now() 
        fecha_db_plana = lectura.fecha.replace(tzinfo=None)
        diferencia = ahora_sistema - fecha_db_plana

        if diferencia <= timedelta(minutes=10):
            estado = "Activa"
        elif diferencia <= timedelta(minutes=30):
            estado = "Inactiva"
        else:
            estado = "Sin comunicación"
            alertas_estaciones.append(f"⚠ Estación {nombre} sin comunicación")

        # --- ESTO ES LO QUE FALTABA: Llenar el diccionario ---
        estaciones_dict[nombre] = {
            "ultima_lectura": lectura.fecha, # Puedes usar la original para el template
            "estado": estado,
            "sensor": lectura.sensor,
            "valor": lectura.valor
        }
        # -----------------------------------------------------

    return render(request, "estaciones.html", {
        "estaciones": estaciones_dict,
        "alertas_estaciones": list(set(alertas_estaciones))
    })


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
                estado = "Sin comunicación"

            estaciones[nombre] = {
                "estado": estado,
                "ultima_lectura": lectura.fecha.strftime("%d/%m/%Y %H:%M:%S")
            }

    return JsonResponse(estaciones)
