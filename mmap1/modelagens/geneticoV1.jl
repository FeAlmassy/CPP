using XLSX
using DataFrames
using LinearAlgebra
using Printf

# ── carregamento da base ──────────────────────────────────
df = DataFrame(XLSX.readtable("basedados.xlsx", 1))   # 1 = primeira planilha (pode trocar pelo nome, ex.: "Plan1")

dataframe_dados_clientes = df[:, 2:end-1]   # ignora primeira coluna (índice) e última (gabarito)
dataframe_gabarito       = df[:, end]       # sempre a última coluna

array_dados_clientes = Matrix{Float64}(dataframe_dados_clientes)
array_gabarito       = Vector{Int}(dataframe_gabarito)     # gabarito 0/1

qtd_features = size(array_dados_clientes, 2)
qtd_genes    = qtd_features + 1   # features + bias

println("Base carregada: $(size(array_dados_clientes, 1)) clientes, $qtd_features features")


function criar_cromossomos(qtd_cromossomos::Int=6, qtd_genes::Int=19)::Matrix{Float64}
    return -1 .+ 2 .* rand(qtd_cromossomos, qtd_genes)
end


"""
Pega cada linha de `cromossomos` (menos o primeiro termo, que é o bias) e itera sobre
cada linha de `array_dados_clientes`. Cada iteração é um produto escalar que gera um
vetor hipótese de 0 e 1. Compara com o gabarito e calcula o fitness:

    percentual_adimplente   = acertos de 1 / total de 1 no gabarito
    percentual_inadimplente = acertos de 0 / total de 0 no gabarito
    fitness                 = percentual_adimplente * percentual_inadimplente

Cada cromossomo recebe um fitness; o vetor de fitness tem o mesmo número de linhas
da matriz de cromossomos.
"""
function calcular_fitness(cromossomos::AbstractMatrix,
                          array_dados_clientes::AbstractMatrix,
                          array_gabarito::AbstractVector)::Vector{Float64}

    total_adimplentes   = sum(array_gabarito .== 1)
    total_inadimplentes = sum(array_gabarito .== 0)

    lista_fitness = Float64[]

    # em Julia, iterar a matriz direto percorre elemento a elemento (em ordem de coluna),
    # então usamos eachrow para ir de linha em linha como no for do numpy
    for linha in eachrow(cromossomos)

        bias  = linha[1]
        genes = linha[2:end]

        q = array_dados_clientes * genes .+ bias

        # onde cada elemento de q for >= 0 vira 1, senão vira 0
        vetor_hipotese = ifelse.(q .>= 0, 1, 0)

        acertos_adimplentes   = sum((vetor_hipotese .== 1) .& (array_gabarito .== 1))  # hipótese 1 e gabarito 1
        acertos_inadimplentes = sum((vetor_hipotese .== 0) .& (array_gabarito .== 0))  # hipótese 0 e gabarito 0

        percentual_adimplente   = acertos_adimplentes / total_adimplentes
        percentual_inadimplente = acertos_inadimplentes / total_inadimplentes

        fitness = percentual_adimplente * percentual_inadimplente
        push!(lista_fitness, fitness)
    end

    return lista_fitness   # cada cromossomo tem um fitness
end


function fitness_percentual(vetor_fitnesses::AbstractVector)::Vector{Float64}
    soma = sum(vetor_fitnesses)
    if soma == 0
        return ones(length(vetor_fitnesses)) ./ length(vetor_fitnesses)
    end
    return vetor_fitnesses ./ soma
end


function selecionar_pais_roleta(cromossomos::AbstractMatrix,
                                percentual_fitnesses::AbstractVector)
    roleta_acumulada = cumsum(percentual_fitnesses)

    n = size(cromossomos, 1)
    indice_pai = min(searchsortedfirst(roleta_acumulada, rand()), n)
    indice_mae = min(searchsortedfirst(roleta_acumulada, rand()), n)

    return cromossomos[indice_pai, :], cromossomos[indice_mae, :]
end


function cruzar_pais(pai::AbstractVector, mae::AbstractVector)
    c1 = rand(1:length(pai)-1)
    c2 = rand(1:length(pai)-1)
    c3 = rand(1:length(pai)-1)

    filho1 = vcat(pai[1:c1], mae[c1+1:end])
    filho2 = vcat(pai[1:c2], mae[c2+1:end])
    filho3 = vcat(pai[1:c3], mae[c3+1:end])

    return filho1, filho2, filho3
end


function mutar(filho1::AbstractVector, filho2::AbstractVector, filho3::AbstractVector)
    for filho in (filho1, filho2, filho3)
        indice = rand(1:length(filho))
        filho[indice] = -1 + 2 * rand()
    end
    return filho1, filho2, filho3
end


function atualizar_populacao(cromossomos::AbstractMatrix,
                             vetor_fitnesses::AbstractVector,
                             filho1::AbstractVector,
                             filho2::AbstractVector,
                             filho3::AbstractVector,
                             array_dados_clientes::AbstractMatrix,
                             array_gabarito::AbstractVector)::Matrix{Float64}

    filhos = permutedims(hcat(filho1, filho2, filho3))   # 3 × qtd_genes (cada filho vira uma linha)
    fitnesses_filhos = calcular_fitness(filhos, array_dados_clientes, array_gabarito)

    indices_melhores_filhos = sortperm(fitnesses_filhos)[end-1:end]  # os 2 filhos com maior fitness
    indices_piores          = sortperm(vetor_fitnesses)[1:2]         # os 2 cromossomos com menor fitness

    nova_populacao = copy(cromossomos)
    for i in 1:2
        idx_pior  = indices_piores[i]
        idx_filho = indices_melhores_filhos[i]
        nova_populacao[idx_pior, :] = filhos[idx_filho, :]
    end

    return nova_populacao
end


function algoritmo_genetico(array_dados_clientes::AbstractMatrix,
                            array_gabarito::AbstractVector,
                            qtd_cromossomos::Int=6,
                            qtd_genes::Int=19,
                            geracoes::Int=100,
                            fitness_alvo::Float64=0.90)

    populacao = criar_cromossomos(qtd_cromossomos, qtd_genes)

    melhor_cromossomo = zeros(qtd_genes)   # placeholder (equivalente ao None do Python)
    melhor_fitness    = 0.0

    for geracao in 1:geracoes

        fitnesses   = calcular_fitness(populacao, array_dados_clientes, array_gabarito)
        percentuais = fitness_percentual(fitnesses)

        idx_melhor    = argmax(fitnesses)
        fitness_atual = fitnesses[idx_melhor]

        if fitness_atual > melhor_fitness
            melhor_fitness    = fitness_atual
            melhor_cromossomo = copy(populacao[idx_melhor, :])
        end

        @printf("Geração %3d | melhor fitness: %.4f\n", geracao, melhor_fitness)

        if melhor_fitness >= fitness_alvo
            @printf("\nFitness alvo %.2f atingido na geração %d.\n", fitness_alvo, geracao)
            break
        end

        pai, mae = selecionar_pais_roleta(populacao, percentuais)
        filho1, filho2, filho3 = cruzar_pais(pai, mae)
        filho1, filho2, filho3 = mutar(filho1, filho2, filho3)
        populacao = atualizar_populacao(populacao, fitnesses,
                                        filho1, filho2, filho3,
                                        array_dados_clientes, array_gabarito)
    end

    return melhor_cromossomo, melhor_fitness
end


"""
Usa o melhor cromossomo encontrado pelo algoritmo genético para prever se um novo
cliente será adimplente (1) ou inadimplente (0).

- melhor_cromossomo: vetor 1D retornado por `algoritmo_genetico`.
- dados_novo_cliente: vetor 1D com as features do cliente (sem o gabarito).
"""
function prever_novo_cliente(melhor_cromossomo::AbstractVector,
                             dados_novo_cliente::AbstractVector)::Int
    bias  = melhor_cromossomo[1]      # separa o bias dos pesos (genes)
    genes = melhor_cromossomo[2:end]

    q = dot(dados_novo_cliente, genes) + bias   # produto escalar (Q)

    previsao = q >= 0 ? 1 : 0          # regra de decisão
    return previsao
end


# ── execução ──────────────────────────────────────────────
melhor_cromossomo, melhor_fitness = algoritmo_genetico(
    array_dados_clientes, array_gabarito,
    6, qtd_genes, 100, 0.90,
)

println("\nMelhor fitness encontrado: $(round(melhor_fitness, digits=4))")