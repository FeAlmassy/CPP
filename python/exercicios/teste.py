# resolução do exercício 13

alunos = [
    {"nome": "João", "notas": [8.0, 7.5, 9.0]},
    {"nome": "Maria", "notas": [5.5, 6.0, 5.0]},
    {"nome": "Pedro", "notas": [3.0, 4.0, 4.5]}
]

relatorio = []
for aluno in alunos:
    nome = aluno["nome"]
    notas = aluno["notas"]
    soma_notas = 0
    for nota in notas:
        soma_notas += nota
    media = round(soma_notas / len(notas), 2)

    if media >= 7:
        situacao = "Aprovado"
    elif media >= 5:
        situacao = "Recuperação"
    else:
        situacao = "Reprovado"

    relatorio.append({"nome": nome, "media": media, "situacao": situacao})

print(relatorio) # Saída esperada


round()