from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout
from .models import Cadastro
from .forms import CadastroForm
from django.contrib import messages

def user_profile_view(request):
    # Verifica se o usuário está logado
    if 'usuario_id' not in request.session:
        messages.error(request, 'Você precisa estar logado para acessar essa página.')
        return redirect('login')

    # Obtém os detalhes do usuário logado
    usuario_id = request.session['usuario_id']
    try:
        usuario = Cadastro.objects.get(id=usuario_id)
    except Cadastro.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        return redirect('login')

    # Renderiza a página do perfil do usuário
    return render(request, 'user_profile.html', {'usuario': usuario})

def login_view(request):
    if request.method == 'POST':
        # Obtendo os dados do formulário
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        # Autenticar o usuário
        try:
            usuario = Cadastro.objects.get(email=email)
            if usuario.senha == senha:  # Verifique a senha (use hashing para produção)
                # Salve o nome do usuário e o ID na sessão
                request.session['usuario_id'] = usuario.id
                request.session['usuario_nome'] = usuario.nome
                return redirect('user_profile')
            else:
                messages.error(request, 'Email ou senha inválidos.')
        except Cadastro.DoesNotExist:
            messages.error(request, 'Email ou senha inválidos.')

    return render(request, 'login.html')

def logout_view(request):
    # Realiza o logout do usuário
    logout(request)
    # Redireciona para a página de login ou outra página de sua escolha
    return redirect('login')

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
            return redirect('user_profile')
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
