from django.shortcuts import render, get_object_or_404, redirect
from .models import Cadastro
from .forms import CadastroForm

# Exibir lista de cadastros
def cadastro_list(request):
    cadastros = Cadastro.objects.all()
    return render(request, 'cadastro_list.html', {'cadastros': cadastros})

# Criar um novo cadastro
def cadastro_create(request):
    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cadastro_list')
    else:
        form = CadastroForm()
    return render(request, 'cadastro_form.html', {'form': form})

# Editar um cadastro existente
def cadastro_update(request, pk):
    cadastro = get_object_or_404(Cadastro, pk=pk)
    if request.method == 'POST':
        form = CadastroForm(request.POST, instance=cadastro)
        if form.is_valid():
            form.save()
            return redirect('cadastro_list')
    else:
        form = CadastroForm(instance=cadastro)
    return render(request, 'cadastro_form.html', {'form': form})

# Excluir um cadastro
def cadastro_delete(request, pk):
    cadastro = get_object_or_404(Cadastro, pk=pk)
    if request.method == 'POST':
        cadastro.delete()
        return redirect('cadastro_list')
    return render(request, 'cadastro_confirm_delete.html', {'cadastro': cadastro})
