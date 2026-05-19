import numpy as np
import matplotlib.pyplot as plt
import cv2
from itertools import pairwise
from sympy import symbols


def construir_versiera(l=401, h=801, qtd_pontos=10, plotar=True):
    """
    Constrói a versiera (parábola) como envoltória de uma família de retas
    a partir de dois lados de um triângulo isósceles.

    A construção segue os passos:
      1. Define um triângulo com vértices p11=(0,0), p21=(l-1,0) e p_base no meio da base inferior.
      2. Discretiza cada lado oblíquo em qtd_pontos pontos.
      3. Liga cada par (ponto_1, ponto_2) — um de cada lado — formando uma família de retas.
      4. As interseções consecutivas dessa família formam a envoltória — uma parábola.
      5. Ajusta um polinômio de grau 2 sobre esses pontos para obter a equação simbólica.

    Parâmetros
    ----------
    l : int
        Largura da tela (colunas). Default = 401.
    h : int
        Altura da tela (linhas). Default = 801.
    qtd_pontos : int
        Quantidade de divisões em cada lado oblíquo. Default = 10.
    plotar : bool
        Se True, exibe a tela final com a construção desenhada.

    Retorna
    -------
    dict com:
        "tela"        : np.ndarray — imagem RGB da construção
        "pontos"      : list[tuple] — pontos (x, y) sobre a parábola
        "coeficientes": np.ndarray — [a, b, c] da parábola y = ax² + bx + c
        "expressao"   : sympy.Expr — expressão simbólica arredondada
    """

    # 1. Inicializa a tela branca
    tela = np.zeros(shape=(h, l, 3), dtype=np.uint8) + 255

    # 2. Vértices do triângulo
    p11    = (0, 0)
    p21    = (l - 1, 0)
    p_base = ((l - 1) // 2, h - 1)

    cv2.circle(tela, p11,    15, (0, 255, 0), -1)
    cv2.circle(tela, p21,    15, (0, 255, 0), -1)
    cv2.circle(tela, p_base, 15, (0, 255, 0), -1)

    cv2.line(tela, p11, p_base, (0, 0, 0), 3)
    cv2.line(tela, p21, p_base, (0, 0, 0), 3)

    # 3. Equações analíticas das retas dos lados oblíquos
    a1, b1 = 2 * (h - 1) / (l - 1), 0          # lado esquerdo
    a2, b2 = 2 * (h - 1) / (1 - l), 2 * h      # lado direito

    f1 = lambda x: a1 * x + b1
    f2 = lambda x: a2 * x + b2

    # 4. Discretização: pontos igualmente espaçados em cada lado (extremos descartados)
    np.set_printoptions(legacy="1.13")
    x_pontos_1 = np.linspace(0,            (l - 1) // 2, qtd_pontos + 3).astype(int)[1:-1]
    x_pontos_2 = np.linspace((l - 1) // 2, l - 1,        qtd_pontos + 3).astype(int)[1:-1]

    y_pontos_1 = np.array(list(map(f1, x_pontos_1))).round(0).astype(int)
    y_pontos_2 = np.array(list(map(f2, x_pontos_2))).round(0).astype(int)

    pontos_1 = list(zip(x_pontos_1, y_pontos_1))
    pontos_2 = list(zip(x_pontos_2, y_pontos_2))

    # 5. Para cada par (ponto_1, ponto_2): desenha a reta e armazena seus coeficientes
    retas = []
    for ponto_1, ponto_2 in zip(pontos_1, pontos_2):
        cv2.circle(tela, ponto_1, 10, (0, 255, 0), -1)
        cv2.circle(tela, ponto_2, 10, (0, 255, 0), -1)
        cv2.line(tela, ponto_1, ponto_2, (0, 255, 0), 3)

        a, b = np.polyfit(
            np.array([ponto_1[0], ponto_2[0]]),
            np.array([ponto_1[1], ponto_2[1]]),
            deg=1
        )
        retas.append({"a": a, "b": b})

    # 6. Pareia retas consecutivas e encontra suas interseções (pontos da parábola)
    retas_pareadas = list(pairwise(retas))

    x_pontos_parabola = []
    y_pontos_parabola = []

    for reta_1, reta_2 in retas_pareadas:
        x_int = (reta_2["b"] - reta_1["b"]) / (reta_1["a"] - reta_2["a"])
        y_int = reta_1["a"] * x_int + reta_1["b"]
        x_int = int(round(x_int))
        y_int = int(round(y_int))

        cv2.circle(tela, (x_int, y_int), 10, (255, 0, 0), -1)
        x_pontos_parabola.append(x_int)
        y_pontos_parabola.append(y_int)

    # 7. Ajuste polinomial grau 2 → equação da parábola
    coefs = np.polyfit(x_pontos_parabola, y_pontos_parabola, deg=2)

    x = symbols("x")
    expressao = (round(coefs[0], 3) * x**2
                 + round(coefs[1], 3) * x
                 + round(coefs[2], 3))

    if plotar:
        plt.imshow(tela)
        plt.title(f"Versiera — y = {expressao}")
        plt.show()

    return {
        "tela":         tela,
        "pontos":       list(zip(x_pontos_parabola, y_pontos_parabola)),
        "coeficientes": coefs,
        "expressao":    expressao,
    }


if __name__ == "__main__":
    resultado = construir_versiera(l=401, h=801, qtd_pontos=10)
    print(f"Pontos da parábola: {resultado['pontos']}")
    print(f"Equação: y = {resultado['expressao']}")