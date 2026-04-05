from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Lectura
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required


def lista_lecturas(request):

    lecturas = Lectura.objects.all().order_by('-fecha')

    alertas = []
    temperatura_alta = False
    humedad_baja = False
    

    for lectura in lecturas:
        if lectura.sensor == "temperatura" and lectura.valor > 35:
            temperatura_alta = True

        if lectura.sensor == "humedad" and lectura.valor < 20:
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
