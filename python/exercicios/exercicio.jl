# INPUTS
try
    a = -2
    
    b = 2
    
    qnt_ret = 1000
    
    if qnt_ret <= 0
        error("A quantidade de retângulos deve ser maior que zero")
    end

    # MODELAGEM
    tamanho_eixo_x = b - a
    dx = tamanho_eixo_x / qnt_ret
    lista_areas = Float64[]
    f = x -> x^2

    i = 0
    while i < qnt_ret
        x_atual = a + i * dx
        area = dx * f(x_atual)
        push!(lista_areas, area)
        i += 1
    end

    println("Resultado da integral: $(sum(lista_areas))")

catch e
    if isa(e, ArgumentError)
        println("Erro: Por favor, digite apenas números.")
    else
        println("Erro: $(e.msg)")
    end
end