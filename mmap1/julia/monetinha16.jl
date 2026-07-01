using YFinance
using DataFrames
using Statistics
using LinearAlgebra
using Base.Threads

# 1. O Motor Matemático (Rei da Colina)
# Função recursiva que avalia carteiras sem alocar memória (HPC)
function busca_forca_bruta!(nivel::Int, soma_atual::Int, passo::Int, pesos_buffer::Vector{Float64},
                            medias::Vector{Float64}, covariancias::Matrix{Float64},
                            thread_id::Int, max_fos::Vector{Float64},
                            best_pesos::Vector{Vector{Float64}}, best_rets::Vector{Float64},
                            best_riscos::Vector{Float64}, n_acoes::Int)

    if nivel == 1
        pesos_buffer[1] = soma_atual / 100.0
        retorno = dot(pesos_buffer, medias)
        risco = dot(pesos_buffer, covariancias, pesos_buffer)

        # Evita divisão por zero
        if risco > 1e-12
            fo = retorno / risco
            if fo > max_fos[thread_id]
                max_fos[thread_id] = fo
                best_rets[thread_id] = retorno
                best_riscos[thread_id] = risco
                best_pesos[thread_id] .= pesos_buffer
            end
        end
        return
    end

    for v in 0:passo:soma_atual
        pesos_buffer[nivel] = v / 100.0
        busca_forca_bruta!(nivel - 1, soma_atual - v, passo, pesos_buffer, medias, covariancias,
                           thread_id, max_fos, best_pesos, best_rets, best_riscos, n_acoes)
    end
end

# 2. A Função Principal de Extração e Execução
function gerar_carteiras_hpc(acoes::Vector{String}, passo::Int;
                             investimento::Union{Float64, Nothing}=nothing,
                             start_dt::String="2023-01-01",
                             end_dt::String="2026-06-30")

    n_acoes = length(acoes)
    if n_acoes < 2
        error("São necessárias pelo menos 2 ações para a otimização.")
    end

    println("Extração de Dados do YFinance para $n_acoes ações...")
    precos_fechamento = DataFrame()

    for ticker in acoes
        try
            df_ticker = get_prices(ticker, startdt=start_dt, enddt=end_dt)
            # Proteção: tenta adjclose, se falhar, tenta close
            preco_col = haskey(df_ticker, "adjclose") ? df_ticker["adjclose"] : df_ticker["close"]

            if isempty(precos_fechamento)
                precos_fechamento.Date = df_ticker["timestamp"]
            end
            precos_fechamento[!, ticker] = preco_col
            println("Sucesso: $ticker")
        catch
            println("Aviso: Falha ao baixar $ticker. Pulando...")
        end
    end

    # Garante que só seguimos com os tickers que realmente baixaram
    acoes_validas = [t for t in acoes if t in names(precos_fechamento)]
    if length(acoes_validas) < n_acoes
        println("Aviso: usando apenas $(length(acoes_validas))/$(n_acoes) ações (falhas foram descartadas).")
    end
    acoes = acoes_validas
    n_acoes = length(acoes)
    if n_acoes < 2
        error("Menos de 2 ações sobreviveram ao download. Abortando.")
    end

    # Cálculos Matemáticos Vetoriais
    matriz_precos = Matrix(precos_fechamento[!, acoes])
    retornos_diarios = (matriz_precos[2:end, :] ./ matriz_precos[1:end-1, :]) .- 1
    medias = vec(mean(retornos_diarios, dims=1))
    covariancias = cov(retornos_diarios)

    # --- Configuração HPC (FIX) ---------------------------------------
    # threadid() é um id GLOBAL que cobre o pool :default + :interactive.
    # nthreads() sozinho só conta o pool :default, então dimensionar os
    # buffers só com nthreads() causa BoundsError quando a thread que
    # executa o loop pertence ao pool :interactive (thread 1, por padrão).
    # maxthreadid() cobre o espaço inteiro de ids possíveis.
    n_threads = Threads.maxthreadid()
    println("\n[Arquitetura] Threads default: $(Threads.nthreads(:default)) | " *
            "interactive: $(Threads.nthreads(:interactive)) | total ids: $n_threads")
    if Threads.nthreads(:default) == 1
        println("[Aviso] Rodando com apenas 1 thread :default — sem paralelismo real.")
        println("        Reinicie com: julia -t auto monetinha.jl")
    end

    max_fos = fill(-Inf, n_threads)
    best_pesos = [zeros(Float64, n_acoes) for _ in 1:n_threads]
    best_rets = zeros(Float64, n_threads)
    best_riscos = zeros(Float64, n_threads)
    # --------------------------------------------------------------------

    println("[Timer] Iniciando avaliação exata (força bruta) de todas as combinações...")
    tempo_calculo = @elapsed begin
        Threads.@threads for v_topo in 0:passo:100
            tid = Threads.threadid()
            buffer_pesos = zeros(Float64, n_acoes)
            buffer_pesos[n_acoes] = v_topo / 100.0

            busca_forca_bruta!(n_acoes - 1, 100 - v_topo, passo, buffer_pesos,
                               medias, covariancias, tid, max_fos, best_pesos, best_rets, best_riscos, n_acoes)
        end
    end

    println("[Timer] Processamento concluído em $(round(tempo_calculo, digits=4)) segundos.")

    # Acha o campeão (ignora slots de threads que nunca rodaram, ainda em -Inf)
    if all(isinf, max_fos)
        error("Nenhuma combinação de pesos válida foi encontrada (risco sempre ~0?).")
    end
    campeao_geral_id = argmax(max_fos)
    pesos_otimos = best_pesos[campeao_geral_id]

    # Montagem do DataFrame de Alocação
    alocacao = DataFrame()
    if investimento !== nothing
        preco_atual = matriz_precos[end, :]
        valor_por_acao = pesos_otimos .* investimento
        qtd_por_acao = floor.(valor_por_acao ./ preco_atual)
        alocacao = DataFrame(
            "Acao" => acoes,
            "Peso_pct" => round.(pesos_otimos .* 100, digits=2),
            "Preco_Atual_R\$" => round.(preco_atual, digits=2),
            "Valor_Alocado_R\$" => round.(valor_por_acao, digits=2),
            "Quantidade" => Int.(qtd_por_acao),
            "Valor_Real_R\$" => round.(qtd_por_acao .* preco_atual, digits=2)
        )
        push!(alocacao, ("TOTAL", 100.0, missing, round(sum(valor_por_acao), digits=2), missing, round(sum(qtd_por_acao .* preco_atual), digits=2)), promote=true)
    end

    return alocacao
end

# ---------------------------------------------------------
# Execução Principal
# ---------------------------------------------------------
# Lista com 16 ações
dezesseis_acoes = ["PETR3.SA", "VALE3.SA", "EMBJ3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "ITSA4.SA", "WEGE3.SA", "RENT3.SA", "SUZB3.SA", "ABEV3.SA", "B3SA3.SA", "GGBR4.SA", "LREN3.SA", "PRIO3.SA", "CSAN3.SA"]

alocacao = gerar_carteiras_hpc(dezesseis_acoes, 5, investimento=10_000.0)
display(alocacao)