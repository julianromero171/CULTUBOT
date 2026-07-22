def normalizar(texto):

    texto = texto.lower()

    texto = texto.replace("cultura", "cultubot")
    texto = texto.replace("cultura bot", "cultubot")
    texto = texto.replace("culto bot", "cultubot")
    texto = texto.replace("culto", "cultubot")

    texto = texto.replace("male con", "malecon")
    texto = texto.replace("malecón", "malecon")

    return texto