from django.shortcuts import render, get_object_or_404, redirect
from .models import Cadastro
from .forms import CadastroForm
from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Cadastro

def login_view(request):
    if request.method == 'POST':
        # Obtendo os dados do formulário
        email = request.POST.get('email')  # Agora estamos capturando o email
        senha = request.POST.get('senha')

        # Autenticar o usuário
        try:
            usuario = Cadastro.objects.get(email=email)  # Verifique o email em vez do nome
            if usuario.senha == senha:  # Verifique a senha (use hashing para produção)
                # Fazer login do usuário (aqui você pode usar sessões ou qualquer outro método)
                request.session['usuario_id'] = usuario.id  # Salve o ID do usuário na sessão
                return redirect('cadastro_list')  # Redirecionar para a página inicial ou outra página após o login
            else:
                messages.error(request, 'Email ou senha inválidos.')
        except Cadastro.DoesNotExist:
            messages.error(request, 'Email ou senha inválidos.')

    # Verificar se o parâmetro 'redirect_to_register' está presente na URL
    if 'redirect_to_register' in request.GET:
        return redirect('register')  # Redirecionar para a página de cadastro

    return render(request, 'login.html')  # Renderize o template de login


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
