def show():
    import streamlit as st
    from datetime import datetime, timezone, timedelta

    def _get_tz():
        n = datetime.now()
        y = n.year
        ds = datetime(y, 3, 31 - (datetime(y, 3, 31).weekday() + 1) % 7)
        de = datetime(y, 10, 31 - (datetime(y, 10, 31).weekday() + 1) % 7)
        return timezone(timedelta(hours=2 if ds <= n < de else 1))

    ora = datetime.now(_get_tz())

    st.title("📚 Fonti dei Dati")
    st.markdown(
        f"<p style='color:#64748B;font-size:0.9rem;'>SismaVer2 utilizza esclusivamente fonti "
        f"ufficiali e pubbliche. Ultimo aggiornamento: <b>{ora.strftime('%d/%m/%Y %H:%M')}</b></p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Seismicità ──────────────────────────────────────────────────────
    st.subheader("🌍 Dati Sismici")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        #### [INGV — Istituto Nazionale di Geofisica e Vulcanologia](https://www.ingv.it)
        Fonte primaria per tutti i dati sismici e vulcanici italiani.
        - API FDSN WebServices: `webservices.ingv.it/fdsnws/event/1/`
        - Stazioni sismiche: 500+ su tutto il territorio nazionale
        - Latenza tipica: 2–10 minuti dall'evento
        - Formato: GeoJSON / QuakeML
        - Aggiornamento in SismaVer2: ogni **5 minuti**

        #### [USGS — United States Geological Survey](https://earthquake.usgs.gov)
        Fonte secondaria per eventi globali e cross-check mediterraneo.
        - Feed significativo settimanale: `earthquake.usgs.gov/earthquakes/feed/v1.0/`
        - Latenza tipica: 5–30 minuti
        """)
    with col2:
        st.markdown("""
        #### [EMSC — European Mediterranean Seismological Centre](https://www.seismicportal.eu)
        Usato per il monitoraggio degli eventi nel Mediterraneo (allerta tsunami).
        - API FDSN: `seismicportal.eu/fdsnws/event/1/`
        - Copertura: area mediterranea, Mar Nero, Atlantico
        - Aggiornamento in SismaVer2: ogni **2 minuti** (sezione Allerte)

        #### [CAT-INGV — Centro Allerta Tsunami](https://www.ingv.it/cat/)
        Sistema nazionale di allerta tsunami (NEAMTWS member).
        - Allerta attivata per eventi M≥5.5 nel Mediterraneo
        - Comunicazioni ufficiali via DPC e media nazionali
        - SismaVer2 monitora eventi M≥5.5 nel Mediterraneo e mostra
          un indicatore derivato — per l'allerta ufficiale usare il link CAT-INGV
        """)

    st.markdown("---")

    # ── Vulcani ─────────────────────────────────────────────────────────
    st.subheader("🌋 Monitoraggio Vulcanico")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        #### [Osservatorio Etneo INGV (OE)](https://www.ct.ingv.it/)
        Centro per Etna, Stromboli, Vulcano, Pantelleria, isole Eolie.
        - Bollettini settimanali e aggiornamenti di attività
        - Dati sismici locali via FDSN

        #### [Osservatorio Vesuviano INGV (OV)](https://www.ov.ingv.it/)
        Centro per Vesuvio, Campi Flegrei, Ischia.
        - Monitoraggio bradisismo (Campi Flegrei)
        - Alert livelli di allerta (da verde a rosso)
        """)
    with col2:
        st.markdown("""
        #### [INGV Vulcani — Portale nazionale](https://www.ingv.it/it/vulcani/)
        - 9 vulcani monitorati attivamente
        - Bollettini mensili e settimanali
        - Report di attività in italiano e inglese

        **Aggiornamento in SismaVer2:** conteggio eventi via FDSN
        ogni **5 minuti** per la home, ogni **30 minuti** per la sezione vulcani.
        """)

    st.markdown("---")

    # ── Meteo ────────────────────────────────────────────────────────────
    st.subheader("🌤️ Dati Meteorologici")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        #### [Open-Meteo](https://open-meteo.com/) ✅ (in uso)
        API meteo gratuita e senza registrazione — usata in SismaVer2 per:
        - Condizioni attuali e previsioni 7 giorni
        - Geocoding integrato (OpenStreetMap Nominatim)
        - Dati provenienti da modelli: ECMWF IFS, GFS, DWD ICON
        - Aggiornamento: ogni ora
        - Nessuna API key richiesta
        """)
    with col2:
        st.markdown("""
        #### [MeteoAlarm (EUMETNET)](https://www.meteoalarm.org/)
        Rete europea di allerte meteo ufficiali — usata in SismaVer2 per:
        - Feed Atom allerte colore per l'Italia
        - Fonte: reti nazionali di meteorologia (ARPAE, ARPA, etc.)
        - Aggiornamento in SismaVer2: ogni **30 minuti**

        #### [Aeronautica Militare — CNMCA](http://www.meteoam.it/)
        Fonte ufficiale italiana per previsioni e avvisi di burrasca.
        """)

    st.markdown("---")

    # ── Protezione Civile & Idrogeologico ────────────────────────────────
    st.subheader("🚨 Protezione Civile e Rischio Idrogeologico")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        #### [DPC — Dipartimento della Protezione Civile](https://www.protezionecivile.gov.it/)
        - Piani nazionali di emergenza e allerta meteo
        - [Mappa allerte in tempo reale](https://mappe.protezionecivile.gov.it/)
        - Aggiornamento: variabile in base all'evento

        #### [Protezioni Civili Regionali](https://www.protezionecivile.gov.it/it/sistemi-di-allertamento/)
        - Allerte specifiche per ogni regione
        - Piani di evacuazione e punti di raccolta
        """)
    with col2:
        st.markdown("""
        #### [ISPRA — Istituto Superiore per la Protezione e la Ricerca Ambientale](https://www.isprambiente.gov.it/)
        - [IdroGEO](https://idrogeo.isprambiente.it/): portale frane e alluvioni
        - [ReNDiS](https://rendis.isprambiente.it/): rischio idrogeologico nazionale
        - [WebGIS ISPRA](https://www.sgi2.isprambiente.it/)

        #### [ARPA regionali](https://www.snpa.it/home)
        Monitoraggio qualità aria, idrologia e meteorologia per ogni regione.
        """)

    st.markdown("---")

    # ── Aggiornamento TTL riepilogo ───────────────────────────────────────
    st.subheader("⏱️ Frequenza di aggiornamento in SismaVer2")
    dati_ttl = [
        ("🌍 Sismica Italia (INGV)", "ogni 5 min", "Home e Monitoraggio Sismico"),
        ("🌊 Allerta Tsunami (EMSC)", "ogni 2 min", "Allerte e Rischi"),
        ("🌋 Attività vulcanica (INGV)", "ogni 5 min (home) / 30 min (vulcani)", "Home e Vulcani"),
        ("🌦️ Meteo (Open-Meteo)", "ogni ora", "Meteo"),
        ("⚠️ Allerte meteo (MeteoAlarm)", "ogni 30 min", "Allerte e Rischi"),
        ("🏔️ Rischio idrogeologico (ISPRA/DPC)", "Aggiornamento annuale (dato strutturale)", "Allerte e Rischi"),
    ]
    for fonte, freq, sezione in dati_ttl:
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;padding:7px 14px;"
            f"margin:3px 0;background:#F8FAFC;border-radius:6px;border:1px solid #E2E8F0;'>"
            f"<span style='color:#1E293B;font-weight:500;'>{fonte}</span>"
            f"<span style='color:#64748B;'><b>{freq}</b> &nbsp;·&nbsp; <i>{sezione}</i></span></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.caption(
        "Tutte le fonti sono pubbliche e gratuite. SismaVer2 non modifica i dati originali, "
        "ma li presenta in forma accessibile ai cittadini. "
        "I dati sismici e vulcanici hanno una latenza di pochi minuti rispetto all'evento reale."
    )
