import numpy as np
import pandas as pd

df = pd.read_excel("basedados.xlsx")

dataframe_dados_clientes = df.iloc[:, 1:-1]  # ignora primeira coluna (índice) e última (gabarito)
dataframe_gabarito       = df.iloc[:, -1]    # sempre a última coluna

array_dados_clientes = dataframe_dados_clientes.values
array_gabarito       = dataframe_gabarito.values

qtd_features = array_dados_clientes.shape[1]
qtd_genes    = qtd_features + 1  # features + bias

print(f"Base carregada: {array_dados_clientes.shape[0]} clientes, {qtd_features} features")



def criar_cromossomos(qtd_cromossomos: int=6, qtd_genes: int=19) -> np.ndarray:
    return -1 + 2 * np.random.rand(qtd_cromossomos, qtd_genes)


def calcular_fitness(cromossomos: np.ndarray, array_dados_clientes: np.ndarray, array_gabarito: np.ndarray) -> np.ndarray:
    """
    Pega cada linha do array_cromossomos (menos o primeiro termo, que é o bias) e itera sobre cada linha da array de dados clientes
    cada linha (iteracao) e um produto escalar
    cada iteracao vai gerar um vetor coluna contendo 0 e 1 chamado de vetor hipotese

    depois comparar o vetor hipotese de cada cromossomo com o vetor gabarito e calcular a porcentagem de acerto

    depois calcular o fitness seguindo a formula 

    percentual_adimplente = quantidade de 1 no vetor hipotese/ total de 1 no gabarito
    percentual_inadimplente - quantidade de 0 no vetor hipotese/ total de 0 no gabarito

    fitness = percentual_adimplente * percentual_inadimplente

    cada cromossomo vai ter um fitness. Somar todos os fitness e calcular a porcentagem relativa de acerta de cada cromossomo
    com base nisso
    """

    total_adimplentes = np.sum(array_gabarito == 1)
    total_inadimplentes = np.sum(array_gabarito == 0)
    
    lista_hipotese = []

    #iteracao pra cada cromossomo
    for linha in cromossomos:  # o for num array vai de linha em linha automaticamente
        
        bias = linha[0]
        genes = linha[1:]

        q = np.dot(array_dados_clientes, genes) + bias

        #claudio ajudou, onde cada elemento de Q for maior igual a zero troque por 1, se nao troque por zero
        vetor_hipotese = np.where(q >= 0, 1, 0)

        acertos_adimplentes = np.sum((vetor_hipotese == 1) & (array_gabarito == 1)) #se a hipotese for 1 e o gabarito for 1 ele acertou, entao contabiliza
        acertos_inadimplentes = np.sum((vetor_hipotese == 0) & (array_gabarito == 0)) #se a hipotese for 0 e o gabarito for 0 ele acertou, entao contabiliza
        # se nao o & da false e ele nao soma 


        percentual_adimplente = acertos_adimplentes / total_adimplentes
        percentual_inadimplente = acertos_inadimplentes / total_inadimplentes

        fitness = percentual_adimplente * percentual_inadimplente
        
        lista_hipotese.append(fitness)
        vetor_fitness = np.array(lista_hipotese) 

    return vetor_fitness # cada cromossomo tem um fitness, entao o vetor de fitness tem o mesmo numero de linhas do array de cromossomos


def fitness_percentual(vetor_fitnesses: np.ndarray) -> np.ndarray:
    soma = np.sum(vetor_fitnesses)
    if soma == 0:
        return np.ones(len(vetor_fitnesses)) / len(vetor_fitnesses)
    return vetor_fitnesses / soma


def selecionar_pais_roleta(
    cromossomos: np.ndarray,
    percentual_fitnesses: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    roleta_acumulada = np.cumsum(percentual_fitnesses)

    indice_pai = min(int(np.searchsorted(roleta_acumulada, np.random.rand())), len(cromossomos) - 1)
    indice_mae = min(int(np.searchsorted(roleta_acumulada, np.random.rand())), len(cromossomos) - 1)

    return cromossomos[indice_pai], cromossomos[indice_mae]


def cruzar_pais(pai: np.ndarray, mae: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    c1 = np.random.randint(1, len(pai))
    c2 = np.random.randint(1, len(pai))
    c3 = np.random.randint(1, len(pai))

    filho1 = np.concatenate([pai[:c1], mae[c1:]])
    filho2 = np.concatenate([pai[:c2], mae[c2:]])
    filho3 = np.concatenate([pai[:c3], mae[c3:]])

    return filho1, filho2, filho3


def mutar(filho1: np.ndarray, filho2: np.ndarray, filho3: np.ndarray,) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    for filho in [filho1, filho2, filho3]:
        indice = np.random.randint(0, len(filho))
        filho[indice] = -1 + 2 * np.random.rand()

    return filho1, filho2, filho3


def atualizar_populacao(cromossomos: np.ndarray,vetor_fitnesses: np.ndarray,filho1: np.ndarray,filho2: np.ndarray,filho3: np.ndarray,array_dados_clientes: np.ndarray,array_gabarito: np.ndarray,) -> np.ndarray:
    filhos = np.array([filho1, filho2, filho3])
    fitnesses_filhos = calcular_fitness(filhos, array_dados_clientes, array_gabarito)

    indices_melhores_filhos = np.argsort(fitnesses_filhos)[-2:] # pega os indices dos 2 melhores filhos, ou seja, os 2 filhos com maior fitness
    indices_piores          = np.argsort(vetor_fitnesses)[:2] # pega os indices dos 2 piores cromossomos da populacao, ou seja, os 2 cromossomos com menor fitness

    nova_populacao = cromossomos.copy()
    for i in range(2):
        idx_pior  = int(indices_piores[i])
        idx_filho = int(indices_melhores_filhos[i])
        nova_populacao[idx_pior] = filhos[idx_filho]

    return nova_populacao

def algoritmo_genetico(array_dados_clientes: np.ndarray, array_gabarito: np.ndarray, qtd_cromossomos: int = 200, qtd_genes: int= 19, geracoes: int= 9999, fitness_alvo: float = 0.90,) -> tuple[np.ndarray, float]:

    populacao = criar_cromossomos(qtd_cromossomos, qtd_genes)

    melhor_cromossomo = None
    melhor_fitness    = 0.0



    for geracao in range(geracoes):

        fitnesses   = calcular_fitness(populacao, array_dados_clientes, array_gabarito)
        percentuais = fitness_percentual(fitnesses)

        idx_melhor    = int(np.argmax(fitnesses))
        fitness_atual = float(fitnesses[idx_melhor])

        if fitness_atual > melhor_fitness:
            melhor_fitness    = fitness_atual
            melhor_cromossomo = populacao[idx_melhor].copy()

        print(f"Geração {geracao+1:>3} | melhor fitness: {melhor_fitness:.4f}")

        if melhor_fitness >= fitness_alvo:
            print(f"\nFitness alvo {fitness_alvo} atingido na geração {geracao+1}.")
            break

        pai, mae = selecionar_pais_roleta(populacao, percentuais)
        filho1, filho2, filho3 = cruzar_pais(pai, mae)
        filho1, filho2, filho3 = mutar(filho1, filho2, filho3)
        populacao = atualizar_populacao(
            populacao, fitnesses,
            filho1, filho2, filho3,
            array_dados_clientes, array_gabarito,
        )

    return melhor_cromossomo, melhor_fitness
