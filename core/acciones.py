def ejecutar(accion, datos):

    if accion == "ACTIVAR":

        print("\n CultuBot:")
        print("Hola, ¿en qué puedo ayudarte?")

    elif accion == "DIBUJAR":

        print("\n Dibujando:")
        print(datos["nombre"])

    elif accion == "SALIR":

        print("\n Hasta luego.")

    elif accion == "NO_ENTIENDO":

        print("\n Lo siento.")
        print("No entendí lo que dijiste.")

    elif accion == "DORMIDO":

        pass