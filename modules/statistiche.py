"""
statistiche.py — Analisi storica e statistiche sismiche per SismaVer2 v3.0
Fonte: INGV FDSN Web Service — dati storici liberi
"""
import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
try:
    from streamlit_autorefresh import st_autorefresh as _sar
    _AR = True
except ImportError:
    _AR = False


def _get_tz():
    n = datetime.now(); y = n.year
    ds = datetime(y, 3, 31 - (datetime(y, 3, 31).weekday() + 1) % 7)
    de = datetime(y, 10, 31 - (datetime(y, 10, 31).weekday() + 1) % 7)
    return timezone(timedelta(hours=2 if ds <= n < de else 1))

FUSO_IT = _get_tz()

# ─── Fetch dati storici INGV ───────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_storico(days: int = 90, min_mag: float = 2.0) -> pd.DataFrame:
    """Recupera eventi sismici storici: INGV primario, USGS come fallback affidabile."""
    end   = datetime.utcnow()
    start = end - timedelta(days=days)
    fmt_s = start.strftime("%Y-%m-%dT%H:%M:%S")
    fmt_e = end.strftime("%Y-%m-%dT%H:%M:%S")

    sources = [
        (   # INGV — catalogo ufficiale italiano
            f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson"
            f"&starttime={fmt_s}&endtime={fmt_e}"
            f"&minmag={min_mag}&minlat=35.0&maxlat=48.0&minlon=5.0&maxlon=20.0"
            f"&limit=2000&orderby=time",
            "INGV", 15,
        ),
        (   # USGS — fallback sempre disponibile
            f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
            f"&starttime={fmt_s}&endtime={fmt_e}"
            f"&minmagnitude={min_mag}&minlatitude=35.0&maxlatitude=48.0"
            f"&minlongitude=5.0&maxlongitude=20.0"
            f"&limit=2000&orderby=time",
            "USGS", 20,
        ),
    ]

    for url, source, timeout in sources:
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code != 200:
                continue
            features = r.json().get("features", [])
            if not features:
                continue
            rows = []
            for f in features:
                p = f.get("properties", {})
                g = f.get("geometry", {}).get("coordinates", [None, None, None])
                t = p.get("time")
                try:
                    if isinstance(t, (int, float)):
                        dt = datetime.fromtimestamp(t / 1000.0, FUSO_IT)
                    else:
                        dt = datetime.fromisoformat(
                            str(t).replace("Z", "+00:00")).astimezone(FUSO_IT)
                except Exception:
                    continue
                rows.append({
                    "datetime": dt,
                    "mag":      p.get("mag"),
                    "depth":    round(g[2], 1) if g[2] is not None else None,
                    "lat":      g[1],
                    "lon":      g[0],
                    "place":    p.get("place", ""),
                    "mag_type": p.get("magType", ""),
                    "data":     dt.date(),
                    "ora":      dt.hour,
                    "giorno_settimana": dt.weekday(),
                    "mese":     dt.strftime("%b %Y"),
                    "fonte":    source,
                })
            df = pd.DataFrame(rows)
            if not df.empty:
                df["mag"]   = pd.to_numeric(df["mag"],   errors="coerce")
                df["depth"] = pd.to_numeric(df["depth"], errors="coerce")
                df = df.dropna(subset=["mag"])
                print(f"INFO statistiche: {len(df)} eventi da {source}")
                return df
        except Exception as e:
            print(f"Errore fetch statistiche ({source}): {e}")
            continue
    return pd.DataFrame()


# ─── Categoria magnitudo ───────────────────────────────────────────────────────

def _cat_mag(m):
    if m < 2.0: return "Micro (<2.0)"
    if m < 3.0: return "Minore (2-3)"
    if m < 4.0: return "Leggero (3-4)"
    if m < 5.0: return "Moderato (4-5)"
    if m < 6.0: return "Forte (5-6)"
    return "Severo (≥6.0)"

_CAT_COLORS = {
    "Micro (<2.0)":    "#94A3B8",
    "Minore (2-3)":    "#60A5FA",
    "Leggero (3-4)":   "#34D399",
    "Moderato (4-5)":  "#FBBF24",
    "Forte (5-6)":     "#F97316",
    "Severo (≥6.0)":   "#EF4444",
}

_GIORNI_ITA = ["Lunedì","Martedì","Mercoledì","Giovedì","Venerdì","Sabato","Domenica"]

# ─── Estrai regione approssimata ──────────────────────────────────────────────

def _estrai_zona(place: str) -> str:
    """Estrae area geografica dal campo 'place' INGV."""
    if not place:
        return "Altra zona"
    place_lower = place.lower()
    zone_map = {
        "sicilia": "Sicilia", "etna": "Sicilia", "messina": "Sicilia",
        "calabria": "Calabria", "reggio": "Calabria",
        "campania": "Campania", "vesuvio": "Campania", "flegrei": "Campania", "naples": "Campania",
        "puglia": "Puglia", "bari": "Puglia", "foggia": "Puglia",
        "basilicata": "Basilicata", "potenza": "Basilicata",
        "abruzzo": "Abruzzo", "l'aquila": "Abruzzo", "pescara": "Abruzzo",
        "marche": "Marche", "ancona": "Marche",
        "lazio": "Lazio", "roma": "Lazio", "rieti": "Lazio",
        "umbria": "Umbria", "perugia": "Umbria",
        "toscana": "Toscana", "florence": "Toscana",
        "emilia": "Emilia-Romagna", "bologna": "Emilia-Romagna",
        "lombardia": "Lombardia", "milan": "Lombardia",
        "friuli": "Friuli-VG", "trieste": "Friuli-VG",
        "veneto": "Veneto", "venezia": "Veneto",
        "trentino": "Trentino-AA", "alto adige": "Trentino-AA",
        "sardegna": "Sardegna", "sardinia": "Sardegna",
        "mar tirreno": "Mar Tirreno", "tirreno": "Mar Tirreno",
        "mar adriatico": "Adriatico", "adriatico": "Adriatico",
        "mar ionio": "Mar Ionio", "ionio": "Mar Ionio",
        "stromboli": "Eolie", "lipari": "Eolie",
    }
    for chiave, zona in zone_map.items():
        if chiave in place_lower:
            return zona
    return "Altra zona"


# ─── Pagina principale ────────────────────────────────────────────────────────

def show():
    from modules.banner_utils import render_banner
    render_banner(
        "📈", "Statistiche Sismiche",
        "Analisi storica · Distribuzione magnitudo · Tendenze temporali · Mappe di densità",
        "#1E1B4B", "#4338CA", "NUOVO",
    )

    if _AR:
        _sar(interval=600_000, limit=None, key="statistiche_autorefresh")

    ora = datetime.now(FUSO_IT)
    st.markdown(
        f"<p style='color:#64748B;font-size:0.9rem;margin-top:0;'>"
        f"Analisi statistica basata su dati INGV FDSN · fallback USGS · "
        f"Aggiornato: <b>{ora.strftime('%d/%m/%Y %H:%M')}</b> (IT)</p>",
        unsafe_allow_html=True,
    )

    # ── Controlli sidebar ─────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Parametri analisi")
    days = st.sidebar.selectbox(
        "Periodo storico",
        [30, 60, 90, 180, 365],
        index=2,
        format_func=lambda x: f"Ultimi {x} giorni" if x < 365 else "Ultimo anno"
    )
    min_mag = st.sidebar.slider("Magnitudo minima", 1.5, 4.0, 2.0, 0.5)

    with st.spinner("Caricamento dati storici (INGV → USGS fallback)..."):
        df = _fetch_storico(days=days, min_mag=min_mag)

    if df.empty:
        st.error(
            "⚠️ Dati storici non disponibili — sia INGV che USGS irraggiungibili. "
            "Riprova tra qualche minuto."
        )
        return

    df["categoria"] = df["mag"].apply(_cat_mag)
    df["zona"] = df["place"].apply(_estrai_zona)

    # ── KPI globali ──────────────────────────────────────────────────────────
    n_totale = len(df)
    mag_max = df["mag"].max()
    mag_media = df["mag"].mean()
    depth_media = df["depth"].dropna().mean()
    n_significativi = len(df[df["mag"] >= 4.0])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Totale eventi", f"{n_totale:,}", f"M≥{min_mag} · {days}gg")
    c2.metric("Magnitudo max", f"M {mag_max:.1f}")
    c3.metric("Magnitudo media", f"M {mag_media:.2f}")
    c4.metric("Profondità media", f"{depth_media:.1f} km" if not np.isnan(depth_media) else "N/D")
    c5.metric("Significativi (M≥4)", f"{n_significativi}", f"{'⚠️' if n_significativi > 5 else '✅'}")

    st.markdown("---")

    # ── TAB Grafici ──────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Frequenza nel tempo",
        "📊 Distribuzione magnitudo",
        "🌍 Distribuzione geografica",
        "🕐 Analisi temporale",
    ])

    # ── TAB 1: Frequenza nel tempo ────────────────────────────────────────────
    with tab1:
        st.subheader("Frequenza giornaliera eventi sismici")

        df_giorno = df.groupby("data").size().reset_index(name="count")
        df_giorno["data"] = pd.to_datetime(df_giorno["data"])
        df_giorno = df_giorno.sort_values("data")
        df_giorno["media_mobile_7g"] = df_giorno["count"].rolling(7, min_periods=1).mean()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_giorno["data"], y=df_giorno["count"],
            name="Eventi/giorno",
            marker_color="#BFDBFE",
            hovertemplate="<b>%{x|%d/%m/%Y}</b><br>%{y} eventi<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=df_giorno["data"], y=df_giorno["media_mobile_7g"],
            name="Media mobile 7gg",
            line=dict(color="#2563EB", width=2.5),
            hovertemplate="<b>%{x|%d/%m/%Y}</b><br>Media: %{y:.1f}<extra></extra>",
        ))
        fig.update_layout(
            height=380,
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9", title=""),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Numero eventi"),
            margin=dict(l=0, r=0, t=20, b=0),
            font=dict(family="Inter, sans-serif"),
            hovermode="x unified",
        )
        st.plotly_chart(fig, width='stretch')

        # Grafico per categoria magnitudo nel tempo
        st.subheader("Composizione per magnitudo nel tempo")
        df_giorno_cat = df.groupby(["data", "categoria"]).size().reset_index(name="count")
        df_giorno_cat["data"] = pd.to_datetime(df_giorno_cat["data"])
        cat_ordine = ["Leggero (3-4)", "Moderato (4-5)", "Forte (5-6)", "Severo (≥6.0)"]
        df_sig = df_giorno_cat[df_giorno_cat["categoria"].isin(cat_ordine)]

        if not df_sig.empty:
            fig2 = px.bar(
                df_sig.sort_values("data"),
                x="data", y="count", color="categoria",
                color_discrete_map=_CAT_COLORS,
                labels={"data": "", "count": "Numero eventi", "categoria": "Categoria"},
                height=320,
            )
            fig2.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
                margin=dict(l=0, r=0, t=20, b=0),
                font=dict(family="Inter, sans-serif"),
            )
            st.plotly_chart(fig2, width='stretch')
        else:
            st.info("Nessun evento M≥3 nel periodo selezionato.")

    # ── TAB 2: Distribuzione magnitudo ────────────────────────────────────────
    with tab2:
        col_l, col_r = st.columns(2)

        with col_l:
            st.subheader("Distribuzione delle magnitudo")
            fig3 = px.histogram(
                df, x="mag", nbins=40,
                color_discrete_sequence=["#3B82F6"],
                labels={"mag": "Magnitudo", "count": "Numero eventi"},
                height=340,
            )
            fig3.update_traces(
                marker_line_color="white",
                marker_line_width=0.5,
            )
            fig3.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Magnitudo"),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Numero eventi"),
                margin=dict(l=0, r=0, t=20, b=0),
                font=dict(family="Inter, sans-serif"),
            )
            # Aggiungi linea media
            fig3.add_vline(
                x=mag_media, line_dash="dash", line_color="#EF4444",
                annotation_text=f"Media: M{mag_media:.2f}",
                annotation_position="top right"
            )
            st.plotly_chart(fig3, width='stretch')

        with col_r:
            st.subheader("Ripartizione per categoria")
            cat_counts = df["categoria"].value_counts().reset_index()
            cat_counts.columns = ["categoria", "count"]
            colori = [_CAT_COLORS.get(c, "#94A3B8") for c in cat_counts["categoria"]]
            fig4 = go.Figure(go.Pie(
                labels=cat_counts["categoria"],
                values=cat_counts["count"],
                hole=0.45,
                marker_colors=colori,
                textfont_size=12,
                hovertemplate="<b>%{label}</b><br>%{value} eventi (%{percent})<extra></extra>",
            ))
            fig4.update_layout(
                height=340,
                paper_bgcolor="white",
                legend=dict(orientation="v", font=dict(size=11)),
                margin=dict(l=0, r=0, t=20, b=0),
                font=dict(family="Inter, sans-serif"),
            )
            st.plotly_chart(fig4, width='stretch')

        # Distribuzione profondità
        st.subheader("Distribuzione della profondità ipocentrale")
        df_depth = df.dropna(subset=["depth"])
        if not df_depth.empty:
            fig5 = px.histogram(
                df_depth, x="depth", nbins=50,
                color_discrete_sequence=["#8B5CF6"],
                labels={"depth": "Profondità (km)", "count": "Numero eventi"},
                height=300,
            )
            fig5.update_traces(marker_line_color="white", marker_line_width=0.5)
            fig5.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Profondità (km)"),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Numero eventi"),
                margin=dict(l=0, r=0, t=20, b=0),
                font=dict(family="Inter, sans-serif"),
            )
            fig5.add_vline(
                x=depth_media, line_dash="dash", line_color="#F59E0B",
                annotation_text=f"Media: {depth_media:.1f} km",
                annotation_position="top right"
            )
            st.plotly_chart(fig5, width='stretch')

    # ── TAB 3: Distribuzione geografica ───────────────────────────────────────
    with tab3:
        st.subheader("Mappa di densità epicentri")
        df_geo = df.dropna(subset=["lat", "lon", "mag"])
        if not df_geo.empty:
            fig6 = px.scatter_mapbox(
                df_geo,
                lat="lat", lon="lon",
                size=df_geo["mag"].apply(lambda m: max(1.5, m) ** 2.2),
                size_max=28,
                color="mag",
                color_continuous_scale=[
                    [0.0, "#60A5FA"], [0.3, "#34D399"],
                    [0.55, "#FBBF24"], [0.75, "#F97316"],
                    [1.0, "#EF4444"]
                ],
                range_color=[min_mag, max(df_geo["mag"].max(), min_mag + 1)],
                hover_data={"mag": ":.1f", "depth": ":.1f", "place": True, "lat": False, "lon": False},
                labels={"mag": "Magnitudo", "depth": "Profondità (km)", "place": "Luogo"},
                mapbox_style="carto-positron",
                center={"lat": 41.9, "lon": 12.5},
                zoom=4.5,
                height=520,
                opacity=0.8,
            )
            fig6.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                coloraxis_colorbar=dict(title="Magnitudo"),
            )
            st.plotly_chart(fig6, width='stretch')

        # Top zone sismiche
        st.subheader("Zone più attive nel periodo")
        zone_counts = df.groupby("zona").agg(
            n_eventi=("mag", "count"),
            mag_max=("mag", "max"),
            mag_media=("mag", "mean"),
        ).sort_values("n_eventi", ascending=False).head(15).reset_index()
        zone_counts["mag_media"] = zone_counts["mag_media"].round(2)
        zone_counts["mag_max"] = zone_counts["mag_max"].round(1)
        zone_counts.columns = ["Zona", "N. eventi", "Mag. max", "Mag. media"]

        fig7 = px.bar(
            zone_counts, x="N. eventi", y="Zona",
            orientation="h",
            color="Mag. max",
            color_continuous_scale=["#60A5FA", "#FBBF24", "#EF4444"],
            text="N. eventi",
            height=420,
        )
        fig7.update_traces(textposition="outside")
        fig7.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
            yaxis=dict(showgrid=False, autorange="reversed"),
            margin=dict(l=0, r=0, t=10, b=0),
            font=dict(family="Inter, sans-serif"),
        )
        st.plotly_chart(fig7, width='stretch')

    # ── TAB 4: Analisi temporale ───────────────────────────────────────────────
    with tab4:
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Distribuzione oraria degli eventi")
            hourly = df.groupby("ora").size().reset_index(name="count")
            all_hours = pd.DataFrame({"ora": range(24)})
            hourly = all_hours.merge(hourly, on="ora", how="left").fillna(0)
            hourly["count"] = hourly["count"].astype(int)
            colori_ore = ["#BFDBFE"] * 24
            peak_h = hourly["count"].idxmax()
            colori_ore[peak_h] = "#2563EB"
            fig8 = go.Figure(go.Bar(
                x=hourly["ora"], y=hourly["count"],
                marker_color=colori_ore,
                hovertemplate="Ore %{x}:00 — %{y} eventi<extra></extra>",
            ))
            fig8.update_layout(
                height=320,
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis=dict(tickvals=list(range(0, 24, 2)),
                           ticktext=[f"{h:02d}:00" for h in range(0, 24, 2)],
                           showgrid=True, gridcolor="#F1F5F9", title="Ora del giorno"),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="N. eventi"),
                margin=dict(l=0, r=0, t=10, b=0),
                font=dict(family="Inter, sans-serif"),
            )
            st.plotly_chart(fig8, width='stretch')
            st.caption(f"Picco: ore {int(hourly.loc[peak_h,'ora']):02d}:00 "
                       f"con {int(hourly.loc[peak_h,'count'])} eventi")

        with col_b:
            st.subheader("Distribuzione per giorno della settimana")
            weekly = df.groupby("giorno_settimana").size().reset_index(name="count")
            all_days = pd.DataFrame({"giorno_settimana": range(7)})
            weekly = all_days.merge(weekly, on="giorno_settimana", how="left").fillna(0)
            weekly["count"] = weekly["count"].astype(int)
            weekly["giorno_nome"] = [_GIORNI_ITA[i] for i in weekly["giorno_settimana"]]
            peak_d = weekly["count"].idxmax()
            colori_giorni = ["#BFDBFE"] * 7
            colori_giorni[peak_d] = "#2563EB"
            fig9 = go.Figure(go.Bar(
                x=weekly["giorno_nome"], y=weekly["count"],
                marker_color=colori_giorni,
                hovertemplate="<b>%{x}</b><br>%{y} eventi<extra></extra>",
            ))
            fig9.update_layout(
                height=320,
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis=dict(showgrid=False, title=""),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="N. eventi"),
                margin=dict(l=0, r=0, t=10, b=0),
                font=dict(family="Inter, sans-serif"),
            )
            st.plotly_chart(fig9, width='stretch')
            st.caption(f"Giorno più attivo: {weekly.loc[peak_d,'giorno_nome']} "
                       f"({int(weekly.loc[peak_d,'count'])} eventi)")

        # Magnitudo massima per settimana
        st.subheader("Evoluzione settimanale — Magnitudo massima registrata")
        df_ts = df.copy()
        df_ts["settimana"] = pd.to_datetime(df_ts["data"]).dt.to_period("W").apply(lambda p: p.start_time)
        weekly_mag = df_ts.groupby("settimana").agg(
            mag_max=("mag", "max"),
            n_eventi=("mag", "count"),
        ).reset_index()

        fig10 = make_subplots(specs=[[{"secondary_y": True}]])
        fig10.add_trace(go.Bar(
            x=weekly_mag["settimana"], y=weekly_mag["n_eventi"],
            name="N. eventi",
            marker_color="#DBEAFE",
            hovertemplate="<b>%{x|Sett. %d %b}</b><br>%{y} eventi<extra></extra>",
        ), secondary_y=False)
        fig10.add_trace(go.Scatter(
            x=weekly_mag["settimana"], y=weekly_mag["mag_max"],
            name="Mag. max settimanale",
            line=dict(color="#DC2626", width=2.5),
            mode="lines+markers",
            marker=dict(size=7, color="#DC2626"),
            hovertemplate="<b>%{x|Sett. %d %b}</b><br>Max: M%{y:.1f}<extra></extra>",
        ), secondary_y=True)
        fig10.update_layout(
            height=360,
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=20, b=0),
            font=dict(family="Inter, sans-serif"),
            hovermode="x unified",
        )
        fig10.update_yaxes(title_text="N. eventi", secondary_y=False,
                           showgrid=True, gridcolor="#F1F5F9")
        fig10.update_yaxes(title_text="Magnitudo max", secondary_y=True,
                           showgrid=False)
        fig10.update_xaxes(showgrid=True, gridcolor="#F1F5F9")
        st.plotly_chart(fig10, width='stretch')

    # ── Tabella eventi significativi ──────────────────────────────────────────
    st.markdown("---")
    st.subheader("Elenco eventi più significativi nel periodo")
    df_top = df.nlargest(20, "mag")[["datetime", "mag", "depth", "place", "mag_type"]].copy()
    df_top["datetime"] = df_top["datetime"].dt.strftime("%d/%m/%Y %H:%M")
    df_top["depth"] = df_top["depth"].apply(lambda x: f"{x:.1f} km" if pd.notna(x) else "—")
    df_top.columns = ["Data/ora (IT)", "Magnitudo", "Profondità", "Luogo", "Tipo Mag."]
    st.dataframe(df_top, width='stretch', hide_index=True)
    st.caption(f"Fonte: INGV FDSN · Periodo: ultimi {days} giorni · M≥{min_mag} · Area Italia+Mediterraneo")
