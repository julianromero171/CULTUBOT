from core.normalizador import normalizar


def test_cultura_bot_se_normaliza_a_cultubot():
    assert normalizar("cultura bot") == "cultubot"


def test_cultura_sola_no_deja_residuo_de_bot_duplicado():
    # Caso documentado en core/normalizador.py: si "cultura" se reemplazara
    # antes que "cultura bot", "cultura bot" quedaría roto ("cultubot bot").
    assert normalizar("cultura bot") == "cultubot"
    assert "bot bot" not in normalizar("cultura bot")


def test_male_con_se_normaliza_a_malecon():
    assert normalizar("male con de cucuta") == "malecon de cucuta"


def test_malecon_con_tilde_se_normaliza():
    assert normalizar("dibuja el malecón") == "dibuja el malecon"


def test_texto_sin_reglas_no_cambia():
    assert normalizar("biblioteca publica") == "biblioteca publica"
