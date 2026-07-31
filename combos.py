"""
Apuestas combinadas con cuota JUSTA del modelo, sobre un catálogo amplio
de mercados (resultado, goles, córners, tarjetas, tiros, primera mitad).

La probabilidad conjunta de una combinada es la fracción de las 10.000
simulaciones en las que TODAS las selecciones se cumplen a la vez, calculada
directamente sobre los arrays crudos de la Monte Carlo (correlacionados
entre sí porque salen de la misma corrida). Esto respeta la correlación
real entre mercados —"gana el local" y "más de 8.5 córners" NO son
independientes— en vez de multiplicar probabilidades sueltas como hace un
creador de apuestas de casa, que infla la cuota resultante.

Alcance honesto: solo se ofrecen mercados que la simulación calcula de
verdad (resultado, goles, córners, tarjetas, tiros, primera mitad,
clasificación en eliminatoria). NO hay mercados de jugador (goleador,
asistencias, tiros de un jugador), de minuto exacto, ni de VAR: no existe
dato real para modelarlos, y esta app no inventa cifras.
"""

import numpy as np

# Semilla propia y fija para el desempate por penaltis en "clasifica":
# determinista y reproducible, independiente de la semilla de la Monte
# Carlo principal para no alterar el resto de la simulación.
_RNG_PENALTIS = np.random.RandomState(123456)


def _pick_mas_confiable(catalogo, claves_candidatas):
    """Entre varias claves del catálogo (p. ej. todas las líneas y lados de
    un mercado), la que tiene la probabilidad real más alta — decide LÍNEA
    y LADO (over/under) a la vez, calculado sobre los datos reales de la
    simulación. Antes se elegía la línea más cercana al valor esperado
    (la de MÁS incertidumbre); ahora se elige la de más confianza, que es
    lo que pide una combinada pensada para acertar."""
    mejor_clave, mejor_prob = None, -1.0
    for k in claves_candidatas:
        if k not in catalogo:
            continue
        p = float(np.mean(catalogo[k][2])) * 100.0
        if p > mejor_prob:
            mejor_prob, mejor_clave = p, k
    return mejor_clave, mejor_prob


# ── Umbrales de confianza, respaldados por backtest (no por intuición) ──
#
# Un backtest de 747 partidos con datos punto-en-el-tiempo (ver backtest.py)
# midió si un pick al X% de confianza del modelo acierta de verdad ~X% de
# las veces. El resultado NO fue uniforme entre mercados:
#
#   Resultado (1X2): mal calibrado por encima de 70%. La banda "80-100%"
#   acertó solo 57.8% real — MENOS que la banda "70-80%" (60.9%). El modelo
#   dice más de lo que sabe en el resultado directo. Único nivel respaldado
#   por el backtest: la banda 70-80%.
#
#   Goles (Over/Under) y Ambos Marcan: bien calibrados y crecientes. La
#   banda 70-80% de Over/Under 2.5 acertó 69.4% real (casi exacto), y BTTS
#   67.7% en su franja alta. Aquí sí se puede confiar en la probabilidad
#   del modelo como señal de acierto real.
#
# Por eso el umbral de "resultado" es más exigente que el de "mercado": no
# porque el resultado importe más, sino porque el propio backtest muestra
# que hay que pedirle más certeza antes de creerle.
UMBRAL_RESULTADO = 70.0
UMBRAL_MERCADO = 65.0

# Córners, tarjetas, tiros y primera mitad no se pudieron calibrar todavía
# (el backtest no los mide; ESPN no da históricos de esos datos por
# partido). Se les aplica el mismo umbral conservador que a goles/BTTS,
# como supuesto razonable, no como hecho verificado.


def _catalogo_legs(raw, home, away, sim):
    """Construye el catálogo de selecciones disponibles para este partido.

    Cada entrada es (mercado, selección, máscara booleana de 10.000 bits).
    La probabilidad de una combinada es el AND de las máscaras de sus
    selecciones, promediado — la fracción conjunta real, no el producto.
    """
    h, a = raw["home_goals"], raw["away_goals"]
    n = len(h)
    total_g = h + a

    hc, ac = raw.get("home_corners"), raw.get("away_corners")
    hcd, acd = raw.get("home_cards"), raw.get("away_cards")
    hs, as_ = raw.get("home_shots"), raw.get("away_shots")
    hts, ats = raw.get("home_total_shots"), raw.get("away_total_shots")
    fhh, fha = raw.get("fh_home_goals"), raw.get("fh_away_goals")

    C = {}  # catálogo: clave -> (mercado, selección, máscara)

    # ── Resultado ──
    C["1"] = ("Resultado", f"Gana {home}", h > a)
    C["X"] = ("Resultado", "Empate", h == a)
    C["2"] = ("Resultado", f"Gana {away}", h < a)
    C["1X"] = ("Doble oportunidad", f"{home} o empate", h >= a)
    C["X2"] = ("Doble oportunidad", f"{away} o empate", h <= a)
    C["12"] = ("Doble oportunidad", "Sin empate", h != a)
    C["dnb1"] = ("Empate no válido", f"{home} (reembolso si hay empate)", h > a)
    C["dnb2"] = ("Empate no válido", f"{away} (reembolso si hay empate)", h < a)
    C["margen_h1"] = ("Margen de victoria", f"{home} gana por 1", (h - a) == 1)
    C["margen_h2p"] = ("Margen de victoria", f"{home} gana por 2 o más", (h - a) >= 2)
    C["margen_a1"] = ("Margen de victoria", f"{away} gana por 1", (a - h) == 1)
    C["margen_a2p"] = ("Margen de victoria", f"{away} gana por 2 o más", (a - h) >= 2)
    C["cs_h"] = ("Portería a cero", f"{home} gana sin recibir gol", (h > a) & (a == 0))
    C["cs_a"] = ("Portería a cero", f"{away} gana sin recibir gol", (a > h) & (h == 0))
    C["marcador_00"] = ("Resultado exacto", "0-0", (h == 0) & (a == 0))

    # ── Goles ──
    for linea in (0.5, 1.5, 2.5, 3.5, 4.5):
        C[f"o{linea}"] = ("Goles totales", f"Más de {linea}", total_g > linea)
        C[f"u{linea}"] = ("Goles totales", f"Menos de {linea}", total_g < linea)
    for linea in (0.5, 1.5, 2.5):
        C[f"ho{linea}"] = ("Goles del local", f"{home}: más de {linea}", h > linea)
        C[f"ao{linea}"] = ("Goles del visitante", f"{away}: más de {linea}", a > linea)
    C["btts"] = ("Ambos marcan", "Sí", (h > 0) & (a > 0))
    C["btts_no"] = ("Ambos marcan", "No", (h == 0) | (a == 0))
    C["par"] = ("Total de goles", "Número par", (total_g % 2) == 0)
    C["impar"] = ("Total de goles", "Número impar", (total_g % 2) == 1)

    # ── Córners (si la simulación los trae) ──
    hay_corners = hc is not None
    if hay_corners:
        total_c = hc + ac
        for linea in (7.5, 8.5, 9.5, 10.5):
            C[f"co{linea}"] = ("Córners totales", f"Más de {linea}", total_c > linea)
            C[f"cu{linea}"] = ("Córners totales", f"Menos de {linea}", total_c < linea)
        C["cmas_h"] = ("Córners", f"{home}: más córners", hc > ac)
        C["cmas_a"] = ("Córners", f"{away}: más córners", ac > hc)
        C["cpar"] = ("Córners totales", "Número par", (total_c % 2) == 0)
        C["cimpar"] = ("Córners totales", "Número impar", (total_c % 2) == 1)

    # ── Tarjetas (si la simulación las trae) ──
    hay_tarjetas = hcd is not None
    if hay_tarjetas:
        total_cd = hcd + acd
        for linea in (1.5, 2.5, 3.5, 4.5, 5.5):
            C[f"to{linea}"] = ("Tarjetas totales", f"Más de {linea}", total_cd > linea)
            C[f"tu{linea}"] = ("Tarjetas totales", f"Menos de {linea}", total_cd < linea)
        C["tmas_h"] = ("Tarjetas", f"{home}: más tarjetas", hcd > acd)
        C["tmas_a"] = ("Tarjetas", f"{away}: más tarjetas", acd > hcd)

    # ── Tiros a puerta y tiros totales (si la simulación los trae) ──
    if hs is not None:
        total_sot = hs + as_
        for linea in (5.5, 6.5, 8.5):
            C[f"so{linea}"] = ("Tiros a puerta (total)", f"Más de {linea}", total_sot > linea)
    if hts is not None:
        total_ts = hts + ats
        for linea in (18.5, 22.5, 26.5):
            C[f"tso{linea}"] = ("Tiros totales", f"Más de {linea}", total_ts > linea)

    # ── Primera mitad (si la simulación la trae) ──
    if fhh is not None:
        fh_total = fhh + fha
        C["fh1"] = ("Primera mitad", f"Gana {home} al descanso", fhh > fha)
        C["fhx"] = ("Primera mitad", "Empate al descanso", fhh == fha)
        C["fh2"] = ("Primera mitad", f"Gana {away} al descanso", fhh < fha)
        C["fh_o05"] = ("Goles 1ª parte", "Más de 0.5 al descanso", fh_total > 0.5)
        C["fh_o15"] = ("Goles 1ª parte", "Más de 1.5 al descanso", fh_total > 1.5)
        C["fh_btts"] = ("Ambos marcan 1ª parte", "Sí", (fhh > 0) & (fha > 0))

    return C, n, hay_corners, hay_tarjetas


def _clasifica_masks(h, a):
    """'Clasifica' en eliminatoria: gana en 90' o penaltis si hay empate.
    Los penaltis se modelan como una moneda 50/50 con semilla propia y fija
    (determinista, no interfiere con la Monte Carlo del partido)."""
    empate = h == a
    moneda = _RNG_PENALTIS.random(len(h)) < 0.5
    clasifica_h = (h > a) | (empate & moneda)
    clasifica_a = (a > h) | (empate & ~moneda)
    return clasifica_h, clasifica_a


def _prob(mascaras):
    """Probabilidad conjunta real (%): fracción de simulaciones donde TODAS
    las condiciones se cumplen a la vez. Nunca se multiplica por separado."""
    conjunta = mascaras[0]
    for m in mascaras[1:]:
        conjunta = conjunta & m
    return float(np.mean(conjunta) * 100.0)


def _ficha(catalogo, claves, home, away):
    """Construye una combinada a partir de claves del catálogo."""
    mercados = []
    mascaras = []
    for k in claves:
        if k not in catalogo:
            return None
        mercado, seleccion, mascara = catalogo[k]
        mercados.append({"mercado": mercado, "seleccion": seleccion})
        mascaras.append(mascara)
    p = _prob(mascaras)
    if p < 1.0:  # combinada casi imposible: no se ofrece
        return None
    return {"selecciones": mercados, "probabilidad": round(p, 1), "cuota": round(100.0 / p, 2)}


def combinadas_de(sim, home, away, raw=None, es_eliminatoria=False, maximo=8):
    """Genera combinadas priorizando ACIERTO, no cuota.

    Filosofía: para cada mercado disponible (resultado, goles, BTTS,
    córners, tarjetas, primera mitad) se elige el pick MÁS CONFIABLE de ese
    mercado — la línea y el lado (over/under) con mayor probabilidad real,
    no el más cercano al promedio. Un mercado que no alcanza su umbral de
    confianza (ver UMBRAL_RESULTADO / UMBRAL_MERCADO arriba) simplemente NO
    se ofrece: es preferible una combinada de menos, o ninguna, a rellenar
    con un pick de moneda al aire.

    Las combinadas se arman apilando los picks más confiables primero (1
    selección, luego +la 2ª más confiable, y así hasta 5), así que el
    tamaño de cada una es consecuencia de cuánta certeza hay en este
    partido — nunca se fuerza una combinada grande de baja confianza solo
    para mostrar variedad de tamaños.

    `raw` (opcional): arrays crudos de simulate_match(..., return_raw=True).
    Sin ellos, solo se puede ofrecer el catálogo de goles (compatibilidad
    con quien no haya migrado a return_raw todavía).
    """
    if raw is None:
        return _combinadas_legado(sim, home, away, es_eliminatoria, maximo)

    catalogo, n, hay_corners, hay_tarjetas = _catalogo_legs(raw, home, away, sim)
    h, a = raw["home_goals"], raw["away_goals"]
    hay_fh = "fh1" in catalogo

    picks = []  # [(clave, probabilidad, familia)], la más confiable de cada mercado

    def agregar(candidatas, umbral, familia):
        clave, p = _pick_mas_confiable(catalogo, candidatas)
        if clave and p >= umbral:
            picks.append((clave, p, familia))

    lineas_goles = [f"o{l}" for l in (0.5, 1.5, 2.5, 3.5, 4.5)] + \
                   [f"u{l}" for l in (0.5, 1.5, 2.5, 3.5, 4.5)]
    agregar(["1", "X", "2", "1X", "X2", "12"], UMBRAL_RESULTADO, "resultado")
    agregar(lineas_goles, UMBRAL_MERCADO, "goles")
    agregar(["btts", "btts_no"], UMBRAL_MERCADO, "btts")

    if hay_corners:
        lineas_corners = [f"co{l}" for l in (7.5, 8.5, 9.5, 10.5)] + \
                          [f"cu{l}" for l in (7.5, 8.5, 9.5, 10.5)]
        agregar(lineas_corners, UMBRAL_MERCADO, "corners")

    if hay_tarjetas:
        lineas_tarjetas = [f"to{l}" for l in (1.5, 2.5, 3.5, 4.5, 5.5)] + \
                           [f"tu{l}" for l in (1.5, 2.5, 3.5, 4.5, 5.5)]
        agregar(lineas_tarjetas, UMBRAL_MERCADO, "tarjetas")

    if hay_fh:
        agregar(["fh1", "fhx", "fh2"], UMBRAL_MERCADO, "primera_mitad")

    if es_eliminatoria:
        ch, ca = _clasifica_masks(h, a)
        catalogo["clasifica_h"] = ("Clasificación", f"{home} clasifica", ch)
        catalogo["clasifica_a"] = ("Clasificación", f"{away} clasifica", ca)
        agregar(["clasifica_h", "clasifica_a"], UMBRAL_RESULTADO, "clasifica")

    if not picks:
        # Ningún mercado de este partido alcanza la confianza mínima.
        # Mejor no ofrecer nada que ofrecer un pick de moneda al aire.
        return []

    # Más confiable primero: cada combinada se arma añadiendo el SIGUIENTE
    # pick más confiable, así que el tamaño refleja cuánta certeza real hay.
    picks.sort(key=lambda x: -x[1])

    candidatas, acumuladas = [], []
    for clave, _p, _fam in picks[:5]:
        acumuladas.append(clave)
        c = _ficha(catalogo, acumuladas, home, away)
        if c and c["cuota"] <= 41.0:
            candidatas.append(c)

    candidatas.sort(key=lambda c: -c["probabilidad"])
    return candidatas[:maximo]


def _combinadas_legado(sim, home, away, es_eliminatoria, maximo):
    """Catálogo reducido (solo goles, vía score_matrix) priorizando ACIERTO.

    Misma filosofía que el camino con `raw`: solo picks con alta probabilidad
    (umbrales de confianza) y combinadas ordenadas de más segura a menos.
    """
    matrix = sim.get("score_matrix") or {}
    if not matrix:
        return []

    def prob_conjunta(pesos):
        total = favorable = 0.0
        for hs, fila in matrix.items():
            hh = int(hs)
            for as_, p in fila.items():
                aa, p = int(as_), float(p)
                total += p
                w = 1.0
                for peso in pesos:
                    w *= peso(hh, aa)
                    if w == 0.0:
                        break
                favorable += p * w
        return (favorable / total * 100.0) if total > 0 else 0.0

    def leg(tipo):
        return {
            "1": ("Resultado", f"Gana {home}", lambda h, a: 1.0 if h > a else 0.0),
            "X": ("Resultado", "Empate", lambda h, a: 1.0 if h == a else 0.0),
            "2": ("Resultado", f"Gana {away}", lambda h, a: 1.0 if h < a else 0.0),
            "1X": ("Doble oportunidad", f"{home} o empate", lambda h, a: 1.0 if h >= a else 0.0),
            "X2": ("Doble oportunidad", f"{away} o empate", lambda h, a: 1.0 if h <= a else 0.0),
            "12": ("Doble oportunidad", "Sin empate", lambda h, a: 1.0 if h != a else 0.0),
            "btts": ("Ambos marcan", "Sí", lambda h, a: 1.0 if h > 0 and a > 0 else 0.0),
            "btts_no": ("Ambos marcan", "No", lambda h, a: 1.0 if h == 0 or a == 0 else 0.0),
            "o05": ("Goles totales", "Más de 0.5", lambda h, a: 1.0 if h + a > 0.5 else 0.0),
            "o15": ("Goles totales", "Más de 1.5", lambda h, a: 1.0 if h + a > 1.5 else 0.0),
            "o25": ("Goles totales", "Más de 2.5", lambda h, a: 1.0 if h + a > 2.5 else 0.0),
            "u15": ("Goles totales", "Menos de 1.5", lambda h, a: 1.0 if h + a < 1.5 else 0.0),
            "u25": ("Goles totales", "Menos de 2.5", lambda h, a: 1.0 if h + a < 2.5 else 0.0),
            "u35": ("Goles totales", "Menos de 3.5", lambda h, a: 1.0 if h + a < 3.5 else 0.0),
        }[tipo]

    def p_de(tipo):
        return prob_conjunta([leg(tipo)[2]])

    # Pick más confiable por familia, solo si supera el umbral.
    picks = []  # (tipo, probabilidad)

    def agregar(candidatas, umbral):
        mejor, mejor_p = None, -1.0
        for t in candidatas:
            try:
                p = p_de(t)
            except KeyError:
                continue
            if p > mejor_p:
                mejor, mejor_p = t, p
        if mejor is not None and mejor_p >= umbral:
            picks.append((mejor, mejor_p))

    agregar(["1", "X", "2", "1X", "X2", "12"], UMBRAL_RESULTADO)
    agregar(["o05", "o15", "o25", "u15", "u25", "u35"], UMBRAL_MERCADO)
    agregar(["btts", "btts_no"], UMBRAL_MERCADO)

    if not picks:
        return []

    # Más segura primero: apilar picks de mayor a menor probabilidad.
    picks.sort(key=lambda x: -x[1])
    candidatas, acumuladas = [], []
    for tipo, _p in picks[:5]:
        acumuladas.append(tipo)
        pesos = [leg(t)[2] for t in acumuladas]
        p = prob_conjunta(pesos)
        if p < 1.0:
            continue
        cuota = round(100.0 / p, 2)
        # Sin mínimo artificial: las más seguras (cuota baja) son válidas.
        if cuota > 41.0:
            continue
        candidatas.append({
            "selecciones": [
                {"mercado": leg(t)[0], "seleccion": leg(t)[1]} for t in acumuladas
            ],
            "probabilidad": round(p, 1),
            "cuota": cuota,
        })

    candidatas.sort(key=lambda c: -c["probabilidad"])
    return candidatas[:maximo]
