
def show():
    import streamlit as st

    from modules.banner_utils import banner_donazioni
    banner_donazioni()

    st.markdown("""
    ## Supporta SismaVer2

    SismaVer2 è un progetto indipendente sviluppato con passione da **Fabio SCELZO** per fornire alla comunità uno strumento affidabile di monitoraggio sismico, vulcanico e meteorologico su tutto il territorio italiano.

    ### 💰 Perché donare

    Il mantenimento e lo sviluppo di SismaVer2 comportano diversi costi:

    - ☁️ **Hosting e infrastruttura server**
    - 🔑 **API premium** per dati meteorologici e servizi geospaziali
    - 💾 **Database** per la gestione delle segnalazioni e della chat
    - ⏱️ **Tempo di sviluppo** per migliorare continuamente la piattaforma
    - 📱 **Test e compatibilità** con diversi dispositivi

    Il tuo supporto permette di mantenere questo servizio attivo, di migliorarlo costantemente e di estenderlo a nuove funzionalità.
    """)

    st.markdown("---")

    # ── DONAZIONE PAYPAL ───────────────────────────────────────────────────────
    paypal_html = (
        '<div style="display:flex;align-items:center;gap:24px;'
        'background:linear-gradient(135deg,#F0F4FF,#E8F0FE);'
        'border:1px solid #C7D7FD;border-radius:16px;'
        'padding:24px 28px;margin:0 0 20px 0;">'
        '<div style="font-size:3rem;flex-shrink:0;">💙</div>'
        '<div style="flex:1;">'
        '<div style="font-weight:800;font-size:1.15rem;color:#1E293B;margin-bottom:4px;">'
        'Sostieni SismaVer2 con PayPal</div>'
        '<div style="font-size:0.88rem;color:#475569;margin-bottom:14px;">'
        'Donazione amici e parenti · zero commissioni · '
        '<span style="color:#1D4ED8;font-weight:600;">meteotorre@gmail.com</span></div>'
        '<a href="https://www.paypal.com/donate/?business=meteotorre%40gmail.com" '
        'target="_blank" '
        'style="background:#003087;color:white;padding:10px 26px;'
        'border-radius:24px;font-weight:700;text-decoration:none;'
        'font-size:0.92rem;display:inline-block;">'
        '💙 Dona ora con PayPal</a></div>'
        '<div style="flex-shrink:0;text-align:center;padding:12px 16px;'
        'background:white;border-radius:12px;border:1px solid #C7D7FD;min-width:110px;">'
        '<div style="font-size:1.6rem;">🛡️</div>'
        '<div style="font-size:0.72rem;color:#64748B;margin-top:4px;font-weight:600;">'
        '100% sicuro<br>cifrato SSL</div>'
        '</div></div>'
    )
    st.markdown(paypal_html, unsafe_allow_html=True)

    st.markdown("---")

    # ── AFFILIATE EMERGENZA (Guadagno passivo) ─────────────────────────────────
    st.subheader("🛡️ Kit di Emergenza Consigliati")
    st.info("""
    💡 **Acquistando i prodotti qui sotto tramite questi link, supporti SismaVer2 senza costi aggiuntivi per te.**
    I link sono affiliati Amazon: riceviamo una piccola commissione ad ogni acquisto.
    """)

    kit_items = [
        {
            "emoji": "🎒",
            "nome": "Zaino da Emergenza 72h",
            "desc": "Kit sopravvivenza completo per tutta la famiglia — raccomandato dalla Protezione Civile.",
            "link": "https://www.amazon.it/s?k=zaino+emergenza+sopravvivenza+protezione+civile&tag=sismoitalia-21",
            "tag": "Best seller"
        },
        {
            "emoji": "🔦",
            "nome": "Torcia LED da Emergenza",
            "desc": "Torcia ricaricabile con dinamo, pannello solare e radio FM — indispensabile senza corrente.",
            "link": "https://www.amazon.it/s?k=torcia+led+emergenza+dinamo+solare+radio&tag=sismoitalia-21",
            "tag": "Essenziale"
        },
        {
            "emoji": "💊",
            "nome": "Cassetta Pronto Soccorso",
            "desc": "Kit medicale professionale conforme al DL 388/2003 per famiglie e aziende.",
            "link": "https://www.amazon.it/s?k=cassetta+pronto+soccorso+professionale+dlgs&tag=sismoitalia-21",
            "tag": "Obbligatoria"
        },
        {
            "emoji": "📻",
            "nome": "Radio di Emergenza",
            "desc": "Radio AM/FM portatile con pila e dinamo per ricevere allerte in caso di blackout.",
            "link": "https://www.amazon.it/s?k=radio+emergenza+portatile+dinamo+batteria&tag=sismoitalia-21",
            "tag": "Consigliata"
        },
        {
            "emoji": "💧",
            "nome": "Filtro Acqua Portatile",
            "desc": "Sistema filtrazione acqua potabile di emergenza — filtra fino a 1.500 litri.",
            "link": "https://www.amazon.it/s?k=filtro+acqua+portatile+emergenza+sopravvivenza&tag=sismoitalia-21",
            "tag": "Vita o morte"
        },
        {
            "emoji": "🔋",
            "nome": "Power Bank Solare",
            "desc": "Caricatore solare ad alta capacità per ricaricare telefoni e dispositivi d'emergenza.",
            "link": "https://www.amazon.it/s?k=power+bank+solare+alta+capacita+emergenza&tag=sismoitalia-21",
            "tag": "Top rated"
        },
    ]

    cols = st.columns(3)
    for i, item in enumerate(kit_items):
        with cols[i % 3]:
            card = (
                f'<div style="border:1px solid #E2E8F0;border-radius:12px;padding:14px;'
                f'margin-bottom:12px;background:white;">'
                f'<div style="font-size:1.8rem;margin-bottom:6px;">{item["emoji"]}</div>'
                f'<div style="font-weight:700;color:#1E293B;margin-bottom:4px;">{item["nome"]}</div>'
                f'<span style="background:#DBEAFE;color:#1E40AF;border-radius:10px;'
                f'padding:2px 8px;font-size:0.72rem;font-weight:600;">{item["tag"]}</span>'
                f'<div style="font-size:0.83rem;color:#64748B;margin:8px 0;">{item["desc"]}</div>'
                f'<a href="{item["link"]}" target="_blank" '
                f'style="background:#FF9900;color:white;padding:7px 14px;border-radius:8px;'
                f'font-weight:700;text-decoration:none;font-size:0.85rem;display:inline-block;">'
                f'🛒 Vedi su Amazon</a>'
                f'</div>'
            )
            st.markdown(card, unsafe_allow_html=True)

    st.caption("⚠️ I link Amazon sono affiliati. L'acquisto non ha costi aggiuntivi per te.")

    st.markdown("---")

    # ── PROGETTI FUTURI ────────────────────────────────────────────────────────
    st.subheader("🚀 Progetti futuri")
    st.markdown("""
    Con il supporto della comunità, SismaVer2 potrà ampliare le proprie funzionalità con:

    - 📱 App mobile dedicata per Android e iOS
    - 🔔 Sistema di notifiche personalizzate per eventi rilevanti nella propria area
    - 🎓 Sezione educativa avanzata con corsi e materiali informativi
    - 🌍 Estensione del monitoraggio a livello europeo
    - 📊 Dashboard personalizzabili per il monitoraggio
    """)

    st.markdown("---")

    # ── RINGRAZIAMENTI ─────────────────────────────────────────────────────────
    st.subheader("🙏 Ringraziamenti")
    st.markdown("""
    Un sentito ringraziamento a tutti coloro che hanno sostenuto e continuano a sostenere questo progetto:

    - Tutti i donatori che hanno contribuito economicamente
    - Gli utenti che forniscono feedback e segnalazioni
    - Gli enti e le istituzioni che rendono disponibili i dati
    - La comunità scientifica per il continuo supporto informativo
    """)

    # ── EMAIL DIRETTA ──────────────────────────────────────────────────────────
    st.markdown("---")
    email_html = (
        '<div style="background:linear-gradient(135deg,#EFF6FF,#DBEAFE);border-radius:12px;'
        'padding:16px;text-align:center;border:1px solid #BFDBFE;">'
        '<p style="margin:0;color:#1E40AF;font-weight:600;">'
        '💌 Preferisci scrivere direttamente? Contatta Fabio: '
        '<a href="mailto:meteotorre@gmail.com" style="color:#1D4ED8;">meteotorre@gmail.com</a>'
        '</p></div>'
    )
    st.markdown(email_html, unsafe_allow_html=True)
