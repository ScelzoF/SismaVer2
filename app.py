import streamlit as st
import os
import importlib
from supabase import create_client, Client

# Configurazione pagina - DEVE essere il primo comando Streamlit
st.set_page_config(
    page_title="SismaVer2 - Monitoraggio Sismico Italiano",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importo i moduli dell'applicazione
from modules import home, meteo, monitoraggio, vulcani, chat, emergenza, segnala_evento
from modules import primo_soccorso, fonti, donazioni, licenza

# NON cancellare le cache all'avvio per migliorare le prestazioni
# st.cache_data.clear()
# st.cache_resource.clear()

# Inizializza contatori nelle session state se non esistono
if 'visitors' not in st.session_state:
    st.session_state.visitors = set()
if 'page_views' not in st.session_state:
    st.session_state.page_views = {}
if 'total_views' not in st.session_state:
    st.session_state.total_views = 0

# Ottieni l'IP del client (usando st.query_params invece di experimental)
client_ip = st.query_params.get('client_ip', 'unknown')

# Aggiorna contatori
#Incrementa visualizzazioni totali
st.session_state.total_views += 1

# Sidebar navigation
st.sidebar.title("🌍 SismaVer2")
st.sidebar.subheader("Navigazione")

# Main navigation con riferimenti ai moduli importati
pages = {
    "🏠 Home": home,
    "📡 Monitoraggio Sismico": monitoraggio,
    "🌋 Vulcani Attivi": vulcani,
    "🌤️ Meteo": meteo,
    "💬 Chat Pubblica": chat,
    "🚨 Emergenza Regionale": emergenza,
    "📢 Segnala Evento": segnala_evento,
    "🩺 Primo Soccorso": primo_soccorso,
    "📚 Fonti": fonti,
    "❤️ Donazioni": donazioni,
    "📜 Licenza": licenza
}

choice = st.sidebar.radio("Seleziona sezione", list(pages.keys()))

# Aggiorna contatori dopo la selezione della pagina
if client_ip not in st.session_state.visitors:
    st.session_state.visitors.add(client_ip)

if choice:
    st.session_state.page_views[choice] = st.session_state.page_views.get(choice, 0) + 1

# Display selected page con ottimizzazione per errori
if choice:
    try:
        # Utilizzo diretto del modulo già importato
        selected_module = pages[choice]
        selected_module.show()
    except Exception as e:
        st.error(f"Errore nell'esecuzione del modulo: {e}")
        st.write("Riprova selezionando un'altra sezione.")

# Info box in sidebar
st.sidebar.markdown("---")
st.sidebar.info(
    "**SismaVer2** è sviluppato da **Fabio SCELZO**.\n\n"
    "📧 Contatto: meteotorre@gmail.com"
)


# Footer
st.sidebar.markdown("---")
# Visualizza statistiche
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Statistiche")
st.sidebar.metric("Visitatori Unici", len(st.session_state.visitors))
st.sidebar.metric("Visualizzazioni Totali", st.session_state.total_views)
st.sidebar.markdown("**Visualizzazioni per pagina:**")
for page, views in st.session_state.page_views.items():
    st.sidebar.text(f"{page}: {views}")

st.sidebar.caption("© 2023-2024 Fabio SCELZO - Tutti i diritti riservati")

# Configurazione di Supabase (se le credenziali sono disponibili)
if "supabase_client" not in st.session_state:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if supabase_url and supabase_key:
        try:
            st.session_state.supabase_client = create_client(supabase_url, supabase_key)
            st.session_state.supabase_connected = True
        except Exception as e:
            st.session_state.supabase_connected = False
            print(f"Errore nella connessione a Supabase: {str(e)}")
    else:
        st.session_state.supabase_connected = False