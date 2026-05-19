import cv2
import numpy as np
from matplotlib import pyplot as plt

l = 1001
h = 201
qtd_pontos_versiera = 75
if qtd_pontos_versiera % 2 != 0:
    qtd_pontos_versiera += 1

tela = np.zeros(
    shape=(h, l, 3), dtype=np.uint8
)

cores = {
    "preto": (0, 0, 0),
    "branco": (255, 255, 255),
    "vermelho": (255, 0, 0),
    "verde": (0, 255, 0),
    "azul": (0, 0, 255),
    "amarelo": (255, 255, 0),
    "laranja": (255, 165, 0),
    "roxo": (128, 0, 128)
}

cor_fundo = cores["branco"]
cor_circunferencia = cores["preto"]
cor_trave = cores["verde"]
cor_ps = cores["laranja"]
cor_versiera = cores["vermelho"]

tela[:, :] = cor_fundo

xc = (l - 1) // 2
yc = (h - 1) // 2
r = (h - 1) // 2

cv2.circle(tela, (xc, yc), r, cor_circunferencia, 2)

p1 = (
    (l - 1) // 2,
    h
)
cv2.circle(tela, p1, 10, cores["preto"], -1)


xp2 = np.linspace(start=0, stop=l - 1, num=qtd_pontos_versiera). \
        round(0). \
        astype(int)
pontos_dois = list(zip(xp2,[0] * qtd_pontos_versiera))
for p2 in pontos_dois:
    # print(p2)
    cv2.line(tela, p1, p2, cor_trave, 1)

    a, b = np.polyfit(
        x=[p1[0], p2[0]],
        y=[p1[1], p2[1]],
        deg=1
    )

    coef_a = a**2 + 1
    coef_b = 2*a*b - 2*a*yc - 2*xc
    coef_c = b**2 + yc**2 - 2*b*yc - r**2 + xc**2

    delta = coef_b**2 - 4*coef_a*coef_c
    x1 = (-coef_b + np.sqrt(delta)) / (2 * coef_a)
    x2 = (-coef_b - np.sqrt(delta)) / (2 * coef_a)

    xs = max([x1, x2], key=lambda x: abs(x - p1[0]))
    ys = a * xs + b

    ponto_versiera = (p2[0], int(round(ys, 0)))
    cv2.circle(tela, ponto_versiera, 5, cor_versiera, -1)

plt.imshow(tela)
plt.show()


 




