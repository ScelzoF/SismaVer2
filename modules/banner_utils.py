"""
banner_utils.py — Banner visivi coerenti per SismaVer2
Fornisce hero-banner tematizzati per tutte le sezioni della navigazione.
"""
import streamlit as st


def render_banner(icon: str, titolo: str, sottotitolo: str,
                  colore1: str = "#1E3A5F", colore2: str = "#2563EB",
                  testo_badge: str = "", bg_image: str = ""):
    badge_html = ""
    if testo_badge:
        badge_html = (
            '<span style="position:absolute;top:14px;right:16px;'
            'background:rgba(255,255,255,0.2);color:white;'
            'padding:3px 10px;border-radius:20px;font-size:11px;'
            f'font-weight:700;letter-spacing:1px;z-index:2;">{testo_badge}</span>'
        )

    bg_layer = f'background:linear-gradient(135deg,{colore1} 0%,{colore2} 100%);'

    img_html = ""
    overlay_html = ""
    if bg_image:
        img_html = (
            f'<img src="{bg_image}" alt="" loading="eager" decoding="async" '
            f'style="position:absolute;inset:0;width:100%;height:100%;'
            f'object-fit:cover;object-position:center 35%;z-index:0;'
            f'image-rendering:-webkit-optimize-contrast;" '
            f'onerror="this.style.display=\'none\'">'
        )
        # Velo scuro leggero in basso a sx per leggibilità testo
        overlay_html = (
            f'<div style="position:absolute;inset:0;z-index:1;'
            f'background:linear-gradient(120deg,'
            f'rgba({_hex_rgb(colore1)},0.78) 0%,'
            f'rgba({_hex_rgb(colore1)},0.55) 38%,'
            f'rgba({_hex_rgb(colore2)},0.20) 70%,'
            f'rgba({_hex_rgb(colore2)},0.05) 100%);"></div>'
        )

    html = (
        '<div style="position:relative;'
        + bg_layer +
        'border-radius:14px;padding:24px 32px 22px 28px;'
        'margin-bottom:22px;box-shadow:0 6px 24px rgba(0,0,0,0.22);'
        'overflow:hidden;min-height:120px;">'
        + img_html
        + overlay_html
        + badge_html
        + f'<div style="position:relative;z-index:2;font-size:42px;margin-bottom:10px;line-height:1;'
          f'text-shadow:0 2px 8px rgba(0,0,0,0.55);">{icon}</div>'
        + f'<h1 style="position:relative;z-index:2;color:white;margin:0 0 6px 0;'
          f'font-size:24px;font-weight:800;letter-spacing:-0.3px;'
          f'text-shadow:0 2px 8px rgba(0,0,0,0.7);">{titolo}</h1>'
        + f'<p style="position:relative;z-index:2;color:rgba(255,255,255,0.96);'
          f'margin:0;font-size:13.5px;line-height:1.5;'
          f'text-shadow:0 1px 6px rgba(0,0,0,0.75);">{sottotitolo}</p>'
        + '</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


def _hex_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
    except Exception:
        return "30,58,95"


# ── Preset per ogni sezione ──────────────────────────────────────────────────

def banner_home():
    render_banner(
        "🏠", "Benvenuto su SismaVer2",
        "Sistema Nazionale di Monitoraggio e Prevenzione — dati in tempo reale da fonti ufficiali",
        "#0F2557", "#1D4ED8",
    )

def banner_monitoraggio():
    render_banner(
        "🌊", "Monitoraggio Sismico",
        "Terremoti in tempo reale · INGV FDSN · Mappa interattiva · Grafici magnitudo e profondità",
        "#1E1B4B", "#4338CA", "LIVE",
    )

def banner_vulcani():
    render_banner(
        "🌋", "Monitoraggio Vulcani Italiani",
        "Schede dettagliate · Stato di allerta INGV · Sismicità locale · Webcam e bollettini ufficiali",
        "#7C1E1E", "#DC2626",
        bg_image="https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Stromboli_Eruption.jpg/1280px-Stromboli_Eruption.jpg",
    )


# ── Foto Wikimedia verificate per ogni vulcano italiano (CDN upload.wikimedia) ──
_VULCANO_FOTO = {
    "Vesuvio":           "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Il_cratere_del_Vulcano_-_panoramio.jpg/1280px-Il_cratere_del_Vulcano_-_panoramio.jpg",
    "Etna":              "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Mt_Etna_and_Catania1.jpg/1280px-Mt_Etna_and_Catania1.jpg",
    "Stromboli":         "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Aerial_image_of_Stromboli_%28view_from_the_northeast%29.jpg/1280px-Aerial_image_of_Stromboli_%28view_from_the_northeast%29.jpg",
    "Campi Flegrei":     "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Panorama_con_Cratere_degli_Astroni.jpg/1280px-Panorama_con_Cratere_degli_Astroni.jpg",
    "Vulcano":           "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Aerial_image_of_Vulcano_%28view_from_the_east%29.jpg/1280px-Aerial_image_of_Vulcano_%28view_from_the_east%29.jpg",
    "Ischia":            "https://upload.wikimedia.org/wikipedia/commons/0/0d/Ischia_da_procida.jpg",
    "Pantelleria":       "https://upload.wikimedia.org/wikipedia/commons/a/a1/Specchio_di_Venere.jpg",
    "Lipari-Vulcanello": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Lipari_Island_from_the_air.jpg/1280px-Lipari_Island_from_the_air.jpg",
    "Colli Albani":      "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Monte_Cavo_Visto_da_castel_gandolfo.jpg/1280px-Monte_Cavo_Visto_da_castel_gandolfo.jpg",
    "Monte Amiata":      "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/MonteAmiataFromEast.jpg/1280px-MonteAmiataFromEast.jpg",
    "Ustica":            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Area_Marina_Protetta_-_Isola_di_Ustica_-_Sicilia.jpg/1280px-Area_Marina_Protetta_-_Isola_di_Ustica_-_Sicilia.jpg",
    "Linosa":            "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Linosa_2.jpg/1280px-Linosa_2.jpg",
    "Salina":            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Aerial_image_of_Salina_%28view_from_the_southwest%29.jpg/1280px-Aerial_image_of_Salina_%28view_from_the_southwest%29.jpg",
    "Alicudi":           "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Lipari_Island_from_the_air.jpg/1280px-Lipari_Island_from_the_air.jpg",
    "Filicudi":          "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Aerial_image_of_Filicudi_%28view_from_the_south%29.jpg/1280px-Aerial_image_of_Filicudi_%28view_from_the_south%29.jpg",
    # Vulcani sottomarini → immagine arco eoliano / storica
    "Marsili":           "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/CalabrianArc-GeotectonicSection.jpg/1280px-CalabrianArc-GeotectonicSection.jpg",
    "Ferdinandea":       "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/L%27isola_Ferdinandea_-_Camillo_De_Vito.jpg/1280px-L%27isola_Ferdinandea_-_Camillo_De_Vito.jpg",
}

# Inquadratura ottimale per vulcano (object-position) — evita teste tagliate / mare vuoto
_VULCANO_FOCUS = {
    "Vesuvio":           "center 50%",
    "Etna":              "center 45%",
    "Stromboli":         "center 40%",
    "Campi Flegrei":     "center 50%",
    "Vulcano":           "center 50%",
    "Ischia":            "center 55%",
    "Pantelleria":       "center 50%",
    "Lipari-Vulcanello": "center 45%",
    "Colli Albani":      "center 50%",
    "Monte Amiata":      "center 35%",
    "Ustica":            "center 45%",
    "Linosa":            "center 50%",
    "Salina":            "center 45%",
    "Alicudi":           "center 45%",
    "Filicudi":          "center 40%",
    "Marsili":           "center center",
    "Ferdinandea":       "center 35%",
}


def banner_vulcano_specifico(nome: str, info: dict):
    """Banner personalizzato con foto del vulcano selezionato."""
    foto = _VULCANO_FOTO.get(nome, "https://commons.wikimedia.org/wiki/Special:FilePath/Stromboli_Eruption.jpg?width=1280")
    livello = info.get("livello_allerta", "")
    regione = info.get("regione", "")
    tipo = info.get("tipo", "")
    altezza = info.get("altezza", "")
    if isinstance(altezza, (int, float)):
        if altezza < 0:
            altezza_str = f"{abs(int(altezza))} m sotto il livello del mare"
        else:
            altezza_str = f"{int(altezza)} m s.l.m."
    else:
        altezza_str = str(altezza) if altezza else ""

    # Colore banner in base al livello di allerta
    livello_colors = {
        "Verde":     ("#064E3B", "#059669"),
        "Giallo":    ("#78350F", "#D97706"),
        "Arancione": ("#7C2D12", "#EA580C"),
        "Rosso":     ("#7F1D1D", "#DC2626"),
    }
    c1, c2 = livello_colors.get(livello, ("#7C1E1E", "#DC2626"))

    sottotitolo_parts = [p for p in [regione, tipo, altezza_str] if p]
    sottotitolo = " · ".join(sottotitolo_parts) if sottotitolo_parts else "Scheda informativa"

    badge = f"ALLERTA {livello.upper()}" if livello else ""
    render_banner(
        "🌋", nome, sottotitolo, c1, c2, badge, bg_image=foto,
    )

def vulcano_hero_card(nome: str, info: dict):
    """Card grande con foto del vulcano sotto il selettore — riempie spazio bianco."""
    foto = _VULCANO_FOTO.get(nome, "")
    if not foto:
        return
    livello = info.get("livello_allerta", "")
    regione = info.get("regione", "")
    tipo = info.get("tipo", "")
    stato = info.get("stato", "")
    altezza = info.get("altezza", "")
    if isinstance(altezza, (int, float)):
        altezza_str = (f"{abs(int(altezza))} m sotto il livello del mare"
                       if altezza < 0 else f"{int(altezza)} m s.l.m.")
    else:
        altezza_str = str(altezza) if altezza else ""

    livello_colors = {
        "Verde": "#059669", "Giallo": "#D97706",
        "Arancione": "#EA580C", "Rosso": "#DC2626",
    }
    badge_bg = livello_colors.get(livello, "#6B7280")

    chips = []
    if tipo:        chips.append(("🌋", tipo))
    if regione:     chips.append(("📍", regione))
    if altezza_str: chips.append(("⛰️", altezza_str))
    if stato:       chips.append(("📡", stato))
    chips_html = "".join(
        f'<span style="background:rgba(0,0,0,0.55);backdrop-filter:blur(6px);'
        f'color:white;padding:6px 11px;border-radius:18px;font-size:12px;'
        f'font-weight:600;margin-right:6px;display:inline-block;">'
        f'{ic} {tx}</span>'
        for ic, tx in chips
    )

    badge_html = (
        f'<div style="position:absolute;top:14px;right:14px;z-index:3;'
        f'background:{badge_bg};color:white;padding:6px 14px;'
        f'border-radius:20px;font-size:12px;font-weight:800;'
        f'letter-spacing:0.5px;box-shadow:0 4px 12px rgba(0,0,0,0.4);">'
        f'● ALLERTA {livello.upper()}</div>'
    ) if livello else ""

    obj_pos = _VULCANO_FOCUS.get(nome, "center 45%")

    html = (
        '<div style="position:relative;width:100%;aspect-ratio:21/9;'
        'max-height:280px;border-radius:16px;overflow:hidden;margin-bottom:18px;'
        'box-shadow:0 8px 28px rgba(0,0,0,0.32);background:#0F172A;">'
        f'<img src="{foto}" alt="{nome}" loading="eager" decoding="async" '
        f'fetchpriority="high" '
        f'style="position:absolute;inset:0;width:100%;height:100%;'
        f'object-fit:cover;object-position:{obj_pos};z-index:0;'
        f'image-rendering:auto;" '
        f'onerror="this.style.display=\'none\'">'
        '<div style="position:absolute;inset:0;z-index:1;'
        'background:linear-gradient(180deg,'
        'rgba(0,0,0,0.08) 0%,'
        'rgba(0,0,0,0.00) 30%,'
        'rgba(0,0,0,0.45) 65%,'
        'rgba(0,0,0,0.88) 100%);"></div>'
        + badge_html +
        '<div style="position:absolute;left:22px;right:22px;bottom:18px;z-index:2;">'
        f'<h2 style="color:white;margin:0 0 10px 0;font-size:30px;'
        f'font-weight:800;letter-spacing:-0.5px;'
        f'text-shadow:0 3px 14px rgba(0,0,0,0.85);">{nome}</h2>'
        f'<div style="line-height:2;">{chips_html}</div>'
        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def banner_allerte():
    render_banner(
        "📊", "Allerte e Rischi",
        "Dashboard live · Allerte MeteoAlarm · Rischio sismico · Idrogeologico · Tsunami CAT-INGV",
        "#7C2D12", "#EA580C", "LIVE",
    )

def banner_meteo():
    render_banner(
        "🌦", "Meteo Italia",
        "Previsioni 7 giorni · Radar precipitazioni · Allerte meteo per qualsiasi comune italiano",
        "#0C4A6E", "#0369A1",
    )

def banner_qualita_aria():
    render_banner(
        "🌬️", "Qualità dell'Aria",
        "Indice AQI europeo per 20 città italiane · Dati Copernicus CAMS / Open-Meteo · Aggiornamento orario",
        "#064E3B", "#059669",
    )

def banner_numeri_utili():
    render_banner(
        "📞", "Numeri di Emergenza",
        "Tutti i numeri utili nazionali e regionali · Vigili del Fuoco · SUEM 118 · DPC · Carabinieri",
        "#134E4A", "#0F766E",
    )

def banner_chat():
    render_banner(
        "💬", "Chat Pubblica",
        "Comunicazione in tempo reale tra cittadini · Segnalazioni · Aggiornamenti di emergenza",
        "#3B0764", "#7C3AED",
    )

def banner_emergenza():
    render_banner(
        "🚨", "Punti di Emergenza",
        "Mappa punti raccolta · Strutture di emergenza · Centri operativi per tutte le regioni italiane",
        "#7F1D1D", "#B91C1C",
    )

def banner_primo_soccorso():
    render_banner(
        "🩺", "Primo Soccorso",
        "Guide pratiche · RCP adulti/bambini/lattanti · Manovre disostruzione · Numeri emergenza sanitaria",
        "#831843", "#BE185D",
    )

def banner_segnala():
    render_banner(
        "📱", "Segnala un Evento",
        "Segnala terremoti, frane, alluvioni o altri eventi · Contribuisci al monitoraggio nazionale",
        "#78350F", "#D97706",
    )

def banner_donazioni():
    render_banner(
        "💰", "Supporta il Progetto",
        "SismaVer2 è indipendente e gratuito · Il tuo contributo garantisce continuità e sviluppo",
        "#14532D", "#16A34A",
    )

def banner_fonti():
    render_banner(
        "📚", "Fonti dei Dati",
        "INGV · EMSC · Protezione Civile · MeteoAlarm · ISPRA · Open-Meteo · Copernicus CAMS",
        "#1E293B", "#334155",
    )

def banner_note_rilascio():
    render_banner(
        "📋", "Note di Rilascio",
        "Cronologia degli aggiornamenti · Nuove funzionalità · Bug fix · Miglioramenti",
        "#1E3A5F", "#2563EB",
    )

def banner_licenza():
    render_banner(
        "ℹ️", "Licenza e Informazioni",
        "Sviluppato da Fabio SCELZO · Progetto open-source · Termini d'uso · Contatti",
        "#374151", "#6B7280",
    )
