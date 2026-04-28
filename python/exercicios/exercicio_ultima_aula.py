from itertools import pairwise

numero = 5.142142
def float2frac(num:float) -> str:

    if not isinstance(num, float):
        raise TypeError("cu")
    numero_str = str(numero)
    pi, pf = numero_str.split('.')
    pi = int(pi)

    tamanho_pf = len(pf)
    if tamanho_pf % 2 != 0:
        raise Exception("O número de dígitos decimais deve ser par.")

    p = 1
    max_p = int(len(pf) / 2)
    periodicidades = []
    while p <= max_p:                                                 
        p1 = pf[0:p]
        p2 = pf[p:p+p]
        if p1 == p2:
            periodicidades.append(p1)
        p += 1

    periodicidades_pareados = pairwise(periodicidades)
    p_final = len(periodicidades[0])
    for p1, p2 in periodicidades_pareados:
        if p2.replace(p1, "") == "":
            p_final = len(p1)


    x = pf[0:p_final]
    x = int(x)

    num = (10 ** p_final - 1) * pi + x
    den = 10 ** p_final - 1

    return num/den

print(float2frac(3.1111))




