"""
banner_utils.py — Banner visivi coerenti per SismaVer2
Fornisce hero-banner tematizzati per tutte le sezioni della navigazione.
"""
import streamlit as st


def render_banner(icon: str, titolo: str, sottotitolo: str,
                  colore1: str = "#1E3A5F", colore2: str = "#2563EB",
                  testo_badge: str = ""):
    """
    Renderizza un banner/hero visivo in cima alla sezione.

    Parametri
    ---------
    icon        : emoji grande (es. "🌋")
    titolo      : titolo principale del banner
    sottotitolo : breve descrizione (max 2 righe)
    colore1     : colore iniziale del gradiente (hex)
    colore2     : colore finale del gradiente (hex)
    testo_badge : testo opzionale per il badge in alto a destra (es. "LIVE")
    """
    badge_html = ""
    if testo_badge:
        badge_html = (
            f'<span style="position:absolute;top:14px;right:16px;'
            f'background:rgba(255,255,255,0.2);color:white;'
            f'padding:3px 10px;border-radius:20px;font-size:11px;'
            f'font-weight:700;letter-spacing:1px;">{testo_badge}</span>'
        )

    st.markdown(
        f"""
        <div style="
            position:relative;
            background: linear-gradient(135deg, {colore1} 0%, {colore2} 100%);
            border-radius: 14px;
            padding: 24px 32px 22px 28px;
            margin-bottom: 22px;
            box-shadow: 0 6px 24px rgba(0,0,0,0.22);
            overflow: hidden;
        ">
            {badge_html}
            <div style="
                position:absolute;right:-20px;bottom:-20px;
                font-size:110px;opacity:0.08;line-height:1;
                pointer-events:none;user-select:none;
            ">{icon}</div>
            <div style="font-size:42px;margin-bottom:10px;line-height:1;">{icon}</div>
            <h1 style="
                color:white;margin:0 0 6px 0;
                font-size:24px;font-weight:800;letter-spacing:-0.3px;
            ">{titolo}</h1>
            <p style="
                color:rgba(255,255,255,0.82);
                margin:0;font-size:13.5px;line-height:1.5;
            ">{sottotitolo}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    )

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
