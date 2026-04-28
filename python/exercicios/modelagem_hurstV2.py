import numpy as np
import random
import matplotlib.pyplot as plt
import math

lista_aleatoria = [random.randint(1, 1000) for _ in range(100)]

# Lista base (100 valores)
lista_100 = [342, 891, 154, 723, 45, 998, 210, 567, 882, 319, 12, 445, 678, 901, 234, 556, 789, 112, 434, 667, 890, 123, 345, 567, 789, 901, 23, 145, 367, 589, 811, 33, 255, 477, 699, 921, 143, 365, 587, 809, 31, 253, 475, 697, 919, 141, 363, 585, 807, 29, 251, 473, 695, 917, 139, 361, 583, 805, 27, 249, 471, 693, 915, 137, 359, 581, 803, 25, 247, 469, 691, 913, 135, 357, 579, 801, 23, 245, 467, 689, 911, 133, 355, 577, 799, 21, 243, 465, 687, 909, 131, 353, 575, 797, 19, 241, 463, 685, 907, 129]


# =========================
# (1) FUNÇÕES (as suas)
# =========================

# desvios acumulados (chamei de y)
def calcular_Y(lista):
    media = sum(lista) / len(lista)
    y = []
    soma_aux = 0
    for x in lista:
        soma_aux += (x - media)
        y.append(soma_aux)
    return y

# (Range)
def calcular_R(y):
    amplitude = max(y) - min(y)
    return amplitude

# desvio padrão
def calcular_S(lista):
    n = len(lista)
    media = sum(lista) / n
    
    soma_quadrados = sum([(x - media)**2 for x in lista])
    variancia = soma_quadrados / n
    desvio_padrao = variancia**0.5
    
    return desvio_padrao

def calcular_RS(lista_original, lista_y):
    R = max(lista_y) - min(lista_y)
    
    n = len(lista_original)
    media = sum(lista_original) / n
    soma_quadrados = sum((x - media)**2 for x in lista_original)
    S = (soma_quadrados / n)**0.5
    
    return R / S 


# =========================
# (2) AQUI FOI A ALTERAÇÃO QUE VOCÊ PEDIU:
#     pegar prefixos com n = 2,4,8,16,32,64... até caber na lista
#     (somente potências de 2)
# =========================

# gere os n em potências de 2 até o tamanho da lista_100
n_valores = []
n = 2
while n <= len(lista_100):
    n_valores.append(n)
    n *= 2

# OBS: "até o final da lista" e "somente potências de 2" entram em conflito
# porque 100 não é potência de 2. Então aqui eu sigo só potências de 2.
# Se você quiser também incluir o ponto final n=100, descomente:
# if n_valores[-1] != len(lista_100):
#     n_valores.append(len(lista_100))

# agora, em vez de lista_10, lista_20, etc, eu crio dinamicamente:
lista_final_RS = []

for n in n_valores:
    lista_n = lista_100[:n]     # slicing do jeito que você pediu
    
    y_n = calcular_Y(lista_n)
    rs_n = calcular_RS(lista_n, y_n)
    
    lista_final_RS.append(rs_n)


# =========================
# (3) SEUS PLOTS (iguais)
# =========================

# usei o gpt, nao sei usar o matplotlib ainda
def plotar_rs(n_valores, rs_valores):
    # Cria o gráfico
    plt.figure(figsize=(10, 6))
    
    # Plota os pontos (n no eixo X, R/S no eixo Y)
    plt.scatter(n_valores, rs_valores, color='blue', label='Dados R/S')
    
    # Adiciona uma linha conectando os pontos para facilitar a visualização da tendência
    plt.plot(n_valores, rs_valores, color='red', linestyle='--', alpha=0.5)
    
    # Configurações de títulos e eixos
    plt.title('Análise R/S - Escala Linear')
    plt.xlabel('Tamanho da Amostra (n)')
    plt.ylabel('Razão R/S')
    plt.grid(True, which="both", ls="-", alpha=0.3)
    plt.legend()
    
    # Exibe o gráfico
    plt.show()

# Chamando a função com seus dados
# lista_final_RS agora foi construída com n em potências de 2
plotar_rs(n_valores, lista_final_RS)


# usei o gpt pq ja tava putasso de nao ter entendido algumas coisas, so queria que essa porra me desse o resultado
def plotar_rs_loglog(n_valores, rs_valores, base="e"):
    n = np.array(n_valores, dtype=float)
    rs = np.array(rs_valores, dtype=float)

    mask = rs > 0
    n = n[mask]
    rs = rs[mask]

    if base == "10":
        x = np.log10(n)
        y = np.log10(rs)
        xlabel = "log10(n)"
        ylabel = "log10(R/S)"
    else:
        x = np.log(n)
        y = np.log(rs)
        xlabel = "ln(n)"
        ylabel = "ln(R/S)"

    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, color="blue", label="Dados em log-log")
    plt.title("Análise R/S - Escala Log-Log")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, which="both", ls="-", alpha=0.3)
    plt.legend()
    plt.show()

def ajustar_reta_loglog_e_plotar(n_valores, rs_valores, base="e"):
    n = np.array(n_valores, dtype=float)
    rs = np.array(rs_valores, dtype=float)

    mask = rs > 0
    n = n[mask]
    rs = rs[mask]

    if base == "10":
        x = np.log10(n)
        y = np.log10(rs)
        xlabel = "log10(n)"
        ylabel = "log10(R/S)"
    else:
        x = np.log(n)
        y = np.log(rs)
        xlabel = "ln(n)"
        ylabel = "ln(R/S)"

    # Ajuste linear: y ≈ a + b*x
    b, a = np.polyfit(x, y, 1)  # slope=b, intercept=a

    # Predição na mesma escala (log)
    y_hat = a + b * x

    # Plot
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, color="blue", label="Dados em log-log")
    plt.plot(x, y_hat, color="red", linestyle="--", label="Reta ajustada")
    plt.title("Ajuste Linear em Log-Log (R/S vs n)")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, which="both", ls="-", alpha=0.3)
    plt.legend()
    plt.show()

    # Retorna parâmetros para você usar depois
    return a, b


plotar_rs_loglog(n_valores, lista_final_RS, base="e")   # base="10" se você preferir

# Agora: reta ajustada em log-log + impressão dos parâmetros
a, b = ajustar_reta_loglog_e_plotar(n_valores, lista_final_RS, base="e")
print("Parâmetros do ajuste em log-log:")
print("Intercepto a =", a)
print("Inclinação  b =", b)

print("Expoente (H) =", b)