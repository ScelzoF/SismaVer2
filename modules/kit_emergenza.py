import streamlit as st


def show():
    st.title("🎒 Kit di Emergenza consigliati")
    st.caption("Link affiliati Amazon: potremmo ricevere una commissione sugli acquisti, senza costi aggiuntivi per te.")

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
