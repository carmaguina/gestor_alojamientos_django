from django.contrib import messages
from django.shortcuts import redirect, render

from alojamientos.models import Unidad

from .forms import ContactoForm
from .models import MensajeContacto


def inicio(request):
    # Los departamentos activos se muestran en la seccion "Departamentos" de la portada
    unidades = Unidad.objects.filter(activa=True).order_by('nombre')
    return render(request, 'paginas/inicio.html', {'unidades': unidades})


def acerca(request):
    return render(request, 'paginas/acerca.html')


def contacto(request):
    if request.method == 'POST':
        form = ContactoForm(request.POST)

        if form.is_valid():
            MensajeContacto.objects.create(
                nombre=form.cleaned_data['nombre'],
                email=form.cleaned_data['email'],
                mensaje=form.cleaned_data['mensaje']
            )
            messages.success(
                request,
                'Tu mensaje fue enviado correctamente.'
            )
            return redirect('paginas:contacto')
    else:
        form = ContactoForm()

    return render(request, 'paginas/contacto.html', {'form': form})
