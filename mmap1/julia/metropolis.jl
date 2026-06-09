using Random
using Printf
using Base.Threads
using ProgressMeter

const r          = 1500
const qtd_pontos = 100_000_000_000

function monte_carlo_chunk(n::Int, seed::Int, prog_counter::Atomic{Int}, atualiza_a_cada::Int)::Int
    rng    = Xoshiro(seed)
    i      = 0
    duas_r = 2.0 * r
    r2     = Float64(r^2)

    @fastmath @inbounds for k in 1:n
        x = rand(rng) * duas_r
        y = rand(rng) * duas_r
        if (x - r) * (x - r) + (y - r) * (y - r) ≤ r2
            i += 1
        end
        if k % atualiza_a_cada == 0
            atomic_add!(prog_counter, 1)   # incremento atômico — thread-safe
        end
    end
    return i
end

function monte_carlo(qtd_pontos::Int)::Int
    nt             = nthreads()
    chunk          = qtd_pontos ÷ nt
    atualiza_a_cada = 1_000_000
    resultados     = Vector{Int}(undef, nt)

    total_ticks    = qtd_pontos ÷ atualiza_a_cada
    prog_counter   = Atomic{Int}(0)
    prog           = Progress(total_ticks; dt=1.0, barlen=40, desc="Monte Carlo: ")

    # thread separada só pra atualizar a barra
    @async begin
        ultimo = 0
        while ultimo < total_ticks
            atual = prog_counter[]
            if atual > ultimo
                update!(prog, atual)
                ultimo = atual
            end
            sleep(0.5)
        end
    end

    @threads for t in 1:nt
        resultados[t] = monte_carlo_chunk(chunk, t * 1_234_567, prog_counter, atualiza_a_cada)
    end

    finish!(prog)
    return sum(resultados)
end

inicio = time()
i = monte_carlo(qtd_pontos)
fim = time()

e             = qtd_pontos - i
area_estimada = (i / qtd_pontos) * (2r)^2
area_real     = π * r^2

@printf "Threads:                     %d\n"     nthreads()
println("Pontos dentro do círculo: $i")
println("Pontos fora do círculo:   $e")
@printf "Estimativa de π ≈ %.8f\n"             4 * i / qtd_pontos
@printf "Tempo:                       %.3fs\n"  fim - inicio
@printf "Área estimada (Monte Carlo): %.4f\n"   area_estimada
@printf "Área real     (π × r²):      %.4f\n"   area_real
@printf "Erro relativo:               %.6f%%\n" abs(area_estimada - area_real) / area_real * 100