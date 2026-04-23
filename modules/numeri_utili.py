"""
numeri_utili.py — Numeri di emergenza nazionali e regionali per SismaVer2
"""
import streamlit as st

def show():
    from modules.banner_utils import banner_numeri_utili
    banner_numeri_utili()
    st.markdown(
        "<p style='color:#64748B;font-size:0.9rem;margin-top:-12px;'>"
        "Numeri nazionali e regionali di emergenza — in caso di pericolo chiama il <b>112</b></p>",
        unsafe_allow_html=True
    )

    # Numero unico
    st.markdown("""
    <div style='background:#dc2626;color:white;padding:20px;border-radius:12px;text-align:center;margin:10px 0 20px 0;'>
        <h1 style='margin:0;font-size:4rem;'>☎️ 112</h1>
        <h3 style='margin:5px 0;'>Numero Unico di Emergenza Europeo</h3>
        <p style='margin:0;opacity:0.9;'>Attivo 24/7 — Gratuito — Disponibile da fisso e cellulare — Disponibile anche senza scheda SIM</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Numeri principali
    st.subheader("🇮🇹 Numeri Nazionali")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        #### 🚑 Emergenza Sanitaria
        | Numero | Servizio |
        |--------|----------|
        | **118** | Emergenza Sanitaria |
        | **112** | NUE (sostituisce 118 in molte regioni) |
        | **06 49978600** | Veleni — Centro Antiveleni Roma |
        | **02 66101029** | Veleni — Centro Antiveleni Milano |

        #### 🔥 Vigili del Fuoco
        | Numero | Servizio |
        |--------|----------|
        | **115** | Vigili del Fuoco |
        | **112** | NUE (alternativo) |
        """)

    with col2:
        st.markdown("""
        #### 🚔 Forze dell'Ordine
        | Numero | Servizio |
        |--------|----------|
        | **113** | Polizia di Stato |
        | **112** | Carabinieri / NUE |
        | **117** | Guardia di Finanza |
        | **1515** | Carabinieri Forestali |
        | **1530** | Guardia Costiera |

        #### 🏛️ Protezione Civile
        | Numero | Servizio |
        |--------|----------|
        | **800 840 840** | DPC — Numero Verde |
        | **800 232 525** | Sos Alluvioni (attivato in emergenza) |
        """)

    with col3:
        st.markdown("""
        #### 🆘 Altri Numeri Utili
        | Numero | Servizio |
        |--------|----------|
        | **1500** | Ministero della Salute |
        | **800 274 274** | INPS — Numero Verde |
        | **803 116** | ACI Soccorso Stradale |
        | **116** | Croce Rossa Italiana |
        | **116117** | Guardia Medica / MMG |
        | **114** | Emergenza Infanzia |
        | **1522** | Antiviolenza — Donne |
        | **800 27 43 74** | Telefono Azzurro |
        | **800 274 274** | Sostegno psicologico |
        """)

    st.markdown("---")

    # Numeri regionali protezione civile
    st.subheader("🗺️ Protezione Civile Regionale")
    st.info("Questi numeri sono attivi per emergenze locali e allerte meteo/idrogeologiche. Per emergenze immediate chiama sempre il **112**.")

    regioni_pc = {
        "Abruzzo": "800 860 780",
        "Basilicata": "0971 417 111",
        "Calabria": "800 96 99 75",
        "Campania": "800 232 525",
        "Emilia-Romagna": "051 659 7650",
        "Friuli-Venezia Giulia": "800 031 020",
        "Lazio": "803 555",
        "Liguria": "010 548 5261",
        "Lombardia": "800 061 160",
        "Marche": "071 806 3900",
        "Molise": "0874 429 111",
        "Piemonte": "800 061 160",
        "Puglia": "080 540 2220",
        "Sardegna": "070 606 6064",
        "Sicilia": "800 458 787",
        "Toscana": "055 838 3838",
        "Trentino-Alto Adige (TN)": "0461 492 000",
        "Trentino-Alto Adige (BZ)": "0471 414 160",
        "Umbria": "075 572 8400",
        "Valle d'Aosta": "0165 274 100",
        "Veneto": "800 990 009",
    }

    import pandas as pd
    df_reg = pd.DataFrame(list(regioni_pc.items()), columns=["Regione", "Numero PC Regionale"])
    col1, col2 = st.columns(2)
    half = len(df_reg) // 2
    with col1:
        st.dataframe(df_reg.iloc[:half], width='stretch', hide_index=True)
    with col2:
        st.dataframe(df_reg.iloc[half:], width='stretch', hide_index=True)

    st.markdown("---")

    # Centri antiveleni
    st.subheader("☠️ Centri Antiveleni Italiani")
    centri_av = {
        "Milano — Ospedale Niguarda": "02 66101029",
        "Pavia — IRCCS Maugeri": "0382 24444",
        "Roma — Policlinico A. Gemelli": "06 3054343",
        "Roma — Policlinico Umberto I": "06 49978000",
        "Napoli — A.O.U. Federico II": "081 7464744",
        "Genova — A.O.U. San Martino": "010 5636245",
        "Torino — A.O.U. Città della Salute": "011 6637637",
        "Foggia — A.O.O. Policlinico": "0881 732 111",
        "Firenze — A.O.U. Careggi": "055 4277238",
        "Catania — A.O.U. Policlinico": "095 327 650",
        "Sassari — A.O.U. Sassari": "079 228 482",
    }
    df_av = pd.DataFrame(list(centri_av.items()), columns=["Centro Antiveleni", "Telefono"])
    st.dataframe(df_av, width='stretch', hide_index=True)

    st.markdown("---")

    # Ospedali SEMPRE APERTI
    st.subheader("🏥 Pronto Soccorso — Codici Triage")
    st.markdown("""
    | Colore | Significato | Tempo attesa |
    |--------|-------------|--------------|
    | 🔴 **Rosso** | Emergenza — pericolo di vita imminente | Immediato |
    | 🟠 **Arancione** | Urgenza — rischio evolutivo elevato | Max 15 min |
    | 🟡 **Azzurro** | Semi-urgenza — condizione stabile ma potenzialmente evolutiva | Max 60 min |
    | 🟢 **Verde** | Non urgente — condizione non critica | Max 120 min |
    | ⬜ **Bianco** | Nessuna urgenza — accesso improprio al PS | Oltre 240 min |
    """)

    st.info("💡 **Consiglio**: Per problemi non urgenti usa il **Medico di Medicina Generale (MMG)** o la **Guardia Medica (116117)** per evitare sovraffollamento al Pronto Soccorso.")

    st.markdown("---")

    # App e risorse digitali
    st.subheader("📱 App e Risorse Digitali di Emergenza")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        #### App ufficiali italiane:
        - **IT-Alert** — Sistema nazionale di allarme pubblico (DPC)
        - **YOUng DPC** — App protezione civile per giovani
        - **Io Non Rischio** — Campagna DPC (alluvioni, sismi, maremoti)
        - **Meteoalarm** — Allerte meteo europee

        #### Portali di emergenza:
        - [mappe.protezionecivile.gov.it](https://mappe.protezionecivile.gov.it)
        - [allertameteo.gov.it](https://allertameteo.gov.it)
        - [it-alert.gov.it](https://it-alert.gov.it)
        """)
    with col2:
        st.markdown("""
        #### Cosa fare PRIMA dell'emergenza:
        1. 📋 Prepara un **kit di emergenza**: acqua, cibo, documenti, farmaci, torcia
        2. 📍 Conosci i **punti di raccolta** del tuo comune
        3. 📻 Tieni una **radio a batterie** (funziona senza corrente)
        4. 💊 Mantieni scorte di **medicinali essenziali** per 72h
        5. 📞 Memorizza i **numeri di emergenza** senza dipendere dallo smartphone
        6. 🔋 Mantieni il **telefono carico** e usa una powerbank
        7. 🗺️ Conosci **due vie di fuga** dalla tua abitazione
        8. ☑️ Accordati con i **vicini** per un piano di mutuo soccorso
        """)

    st.markdown("---")
    st.caption("Fonte: Dipartimento della Protezione Civile · Ministero dell'Interno · NUE 112 · Aggiornato: Aprile 2026")
