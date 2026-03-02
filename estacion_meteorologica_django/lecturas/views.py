from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Lectura

def lista_lecturas(request):
    lecturas = Lectura.objects.all()

    paginator = Paginator(lecturas, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "lecturas/lista.html", {"page_obj": page_obj})