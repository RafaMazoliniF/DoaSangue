from django.db import models

class Cadastro(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    idade = models.IntegerField()
    senha = models.CharField(max_length=128, null=True)

    def __str__(self):
        return self.nome
