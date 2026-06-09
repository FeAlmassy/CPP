
using LinearAlgebra
using XLSX
using DataFrames


# ────────────────────────────────────────────────────────────
#  structs — configuração e estado separados dos algoritmos
# ────────────────────────────────────────────────────────────

struct ConfigGA
    qtd_cromossomos::Int64
    qtd_genes::Int64
    geracoes::Int64
    fitness_alvo::Float64
end

# construtor com defaults — equivalente aos keyword args do Python
ConfigGA(; qtd_cromossomos=200, qtd_genes=19, geracoes=9999, fitness_alvo=0.90) =
    ConfigGA(qtd_cromossomos, qtd_genes, geracoes, fitness_alvo)


struct DadosBase
    clientes::Matrix{Float64}
    gabarito::Vector{Float64}
    qtd_features::Int64
    qtd_amostras::Int64
end


# ────────────────────────────────────────────────────────────
#  carregar base de dados
# ────────────────────────────────────────────────────────────

function carregar_base(caminho::String)::DadosBase
    xf  = XLSX.readxlsx(caminho)
    sh  = xf[XLSX.sheetnames(xf)[1]]
    df  = DataFrame(XLSX.eachtablerow(sh))

    mat = Matrix{Float64}(df)

    clientes = mat[:, 2:end-1]   # ignora primeira coluna (índice) e última (gabarito)
    gabarito = mat[:, end]

    println("Base carregada: $(size(clientes, 1)) clientes, $(size(clientes, 2)) features")

    return DadosBase(clientes, gabarito, size(clientes, 2), size(clientes, 1))
end


# ────────────────────────────────────────────────────────────
#  população inicial
#  f : ℤ × ℤ → Matrix{Float64}
# ────────────────────────────────────────────────────────────

function criar_cromossomos(config::ConfigGA)::Matrix{Float64}
    return -1.0 .+ 2.0 .* rand(config.qtd_cromossomos, config.qtd_genes)
end


# ────────────────────────────────────────────────────────────
#  fitness
#  f : Matrix{Float64} × DadosBase → Vector{Float64}
#
#  VANTAGEM JULIA: loop interno compila para Assembly nativo
#  sem precisar vetorizar com NumPy. Mais rápido e mais legível.
# ────────────────────────────────────────────────────────────

function calcular_fitness(
    cromossomos::Matrix{Float64},
    dados::DadosBase
)::Vector{Float64}

    total_adimplentes   = sum(dados.gabarito .== 1.0)
    total_inadimplentes = sum(dados.gabarito .== 0.0)

    n = size(cromossomos, 1)
    fitnesses = zeros(Float64, n)

    # loop explícito — em Julia é tão rápido quanto NumPy vetorizado
    for i in 1:n
        bias  = cromossomos[i, 1]
        genes = @view cromossomos[i, 2:end]   # @view evita cópia de memória

        q = dados.clientes * genes .+ bias     # produto interno + bias

        hipotese = q .>= 0.0                   # vetor Bool — sem alocar Int

        acertos_adim   = sum(hipotese .& (dados.gabarito .== 1.0))
        acertos_inadim = sum(.!hipotese .& (dados.gabarito .== 0.0))

        p_adim   = acertos_adim   / total_adimplentes
        p_inadim = acertos_inadim / total_inadimplentes

        fitnesses[i] = p_adim * p_inadim
    end

    return fitnesses
end


# ────────────────────────────────────────────────────────────
#  fitness percentual
#  f : Vector{Float64} → Vector{Float64}
# ────────────────────────────────────────────────────────────

function fitness_percentual(fitnesses::Vector{Float64})::Vector{Float64}
    soma = sum(fitnesses)
    soma == 0.0 && return fill(1.0 / length(fitnesses), length(fitnesses))
    return fitnesses ./ soma
end


# ────────────────────────────────────────────────────────────
#  seleção por roleta
#  f : Matrix{Float64} × Vector{Float64} → (Vector, Vector)
# ────────────────────────────────────────────────────────────

function selecionar_pais_roleta(
    cromossomos::Matrix{Float64},
    percentuais::Vector{Float64}
)::Tuple{Vector{Float64}, Vector{Float64}}

    roleta = cumsum(percentuais)
    n      = size(cromossomos, 1)

    # searchsorted retorna o índice onde o valor se encaixaria
    idx_pai = min(searchsortedfirst(roleta, rand()), n)
    idx_mae = min(searchsortedfirst(roleta, rand()), n)

    return cromossomos[idx_pai, :], cromossomos[idx_mae, :]
end


# ────────────────────────────────────────────────────────────
#  cruzamento — 3 filhos por corte aleatório
#  f : Vector × Vector → (Vector, Vector, Vector)
# ────────────────────────────────────────────────────────────

function cruzar_pais(
    pai::Vector{Float64},
    mae::Vector{Float64}
)::Tuple{Vector{Float64}, Vector{Float64}, Vector{Float64}}

    n  = length(pai)
    c1 = rand(1:n-1)
    c2 = rand(1:n-1)
    c3 = rand(1:n-1)

    filho1 = vcat(pai[1:c1],  mae[c1+1:end])
    filho2 = vcat(pai[1:c2],  mae[c2+1:end])
    filho3 = vcat(pai[1:c3],  mae[c3+1:end])

    return filho1, filho2, filho3
end


# ────────────────────────────────────────────────────────────
#  mutação — altera um gene aleatório por filho
#  multiple dispatch — aceita número variável de filhos
# ────────────────────────────────────────────────────────────

function mutar!(filho::Vector{Float64})
    idx = rand(1:length(filho))
    filho[idx] = -1.0 + 2.0 * rand()
end

# versão para três filhos — mesmo nome, tipos diferentes
function mutar!(
    filho1::Vector{Float64},
    filho2::Vector{Float64},
    filho3::Vector{Float64}
)
    mutar!(filho1)
    mutar!(filho2)
    mutar!(filho3)
end

# NOTA: ! na convenção Julia = função que modifica o argumento (mutável)
# equivalente ao comportamento in-place do NumPy


# ────────────────────────────────────────────────────────────
#  atualizar população — substitui os 2 piores pelos 2 melhores filhos
# ────────────────────────────────────────────────────────────

function atualizar_populacao!(
    populacao::Matrix{Float64},
    fitnesses::Vector{Float64},
    filho1::Vector{Float64},
    filho2::Vector{Float64},
    filho3::Vector{Float64},
    dados::DadosBase
)
    filhos           = hcat(filho1, filho2, filho3)'   # matriz 3 × genes
    fitnesses_filhos = calcular_fitness(filhos, dados)

    # sortperm — retorna índices que ordenariam o vetor
    idx_melhores_filhos = sortperm(fitnesses_filhos)[end-1:end]   # 2 melhores filhos
    idx_piores          = sortperm(fitnesses)[1:2]                 # 2 piores da população

    for i in 1:2
        populacao[idx_piores[i], :] = filhos[idx_melhores_filhos[i], :]
    end
end


# ────────────────────────────────────────────────────────────
#  loop principal
# ────────────────────────────────────────────────────────────

function algoritmo_genetico(
    dados::DadosBase,
    config::ConfigGA = ConfigGA()
)::Tuple{Vector{Float64}, Float64}

    populacao = criar_cromossomos(config)

    melhor_cromossomo = zeros(Float64, config.qtd_genes)
    melhor_fitness    = 0.0

    for geracao in 1:config.geracoes

        fitnesses   = calcular_fitness(populacao, dados)
        percentuais = fitness_percentual(fitnesses)

        idx_melhor    = argmax(fitnesses)
        fitness_atual = fitnesses[idx_melhor]

        if fitness_atual > melhor_fitness
            melhor_fitness    = fitness_atual
            melhor_cromossomo = populacao[idx_melhor, :] |> copy
        end

        @printf "Geração %4d | melhor fitness: %.4f\n" geracao melhor_fitness

        melhor_fitness >= config.fitness_alvo && begin
            println("\nFitness alvo $(config.fitness_alvo) atingido na geração $geracao.")
            break
        end

        pai, mae                = selecionar_pais_roleta(populacao, percentuais)
        filho1, filho2, filho3  = cruzar_pais(pai, mae)
        mutar!(filho1, filho2, filho3)
        atualizar_populacao!(populacao, fitnesses, filho1, filho2, filho3, dados)
    end

    return melhor_cromossomo, melhor_fitness
end


# ────────────────────────────────────────────────────────────
#  predição com o cromossomo treinado
# ────────────────────────────────────────────────────────────

function predizer(
    cromossomo::Vector{Float64},
    clientes::Matrix{Float64}
)::Vector{Int64}

    bias  = cromossomo[1]
    genes = @view cromossomo[2:end]

    q = clientes * genes .+ bias
    return ifelse.(q .>= 0.0, 1, 0)
end


# ────────────────────────────────────────────────────────────
#  execução
# ────────────────────────────────────────────────────────────

using Printf

dados  = carregar_base("basedados.xlsx")
config = ConfigGA(qtd_cromossomos=200, qtd_genes=dados.qtd_features + 1, fitness_alvo=0.90)

cromossomo, fitness = algoritmo_genetico(dados, config)

println("\nMelhor fitness final: $(round(fitness, digits=4))")
println("Cromossomo: $cromossomo")