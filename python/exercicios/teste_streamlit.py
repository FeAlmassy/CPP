import streamlit as st


st.title("Isso e um titulo badomnwmodiawn")
st.text("isso e um texto")

numero = st.number_input("Digite o divisor", value=2, step=1)
lista_input = st.text_input("Digite os números separados por vírgula", "1,2,3,4,5,6,7,8,9,10")

if st.button("Calcular"):
    def divisores(lista: list, numero: int) -> tuple[list, list]:
        
        lista_divisores = []
        lista_nao_divisores = []

        if not isinstance(numero, int):
            raise TypeError("o numero tem que ser inteiro")
        if numero == 0:
            raise ValueError("o num nao pode ser zero")
        if len(lista) == 0:
            raise ValueError("a lista nao pode estar vazia")
            
        i = 0
        while i <= len(lista) - 1:
            if not isinstance(lista[i], int):
                raise ValueError("a lista tem que conter somente numeros")
            if lista[i] % numero == 0:
                lista_divisores.append(lista[i])
            else:
                lista_nao_divisores.append(lista[i])
            i = i + 1

        return lista_divisores, lista_nao_divisores

