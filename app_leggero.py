import streamlit as st
import importlib
import os

# Configurazione pagina - DEVE essere il primo comando Streamlit
st.set_page_config(
    page_title="SismaVer2 - Monitoraggio Light",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("🌍 SismaVer2")
st.sidebar.subheader("Navigazione")

# Main navigation con moduli minimali
# Inizializzo un dizionario vuoto per i moduli
page_modules = {}

# Controllo se esistono le versioni light dei moduli
light_modules = {
    "🏠 Home": ("home_light", "home"),
    "📡 Monitoraggio Sismico": ("monitoraggio_light", "monitoraggio"),
    "🌋 Vulcani Attivi": ("vulcani", "vulcani"),
    "🌤️ Meteo": ("meteo", "meteo"),
    "💬 Chat Pubblica": ("chat", "chat"),
    "🚨 Emergenza Regionale": ("emergenza", "emergenza"),
    "📢 Segnala Evento": ("segnala_evento", "segnala_evento"),
    "🩺 Primo Soccorso": ("primo_soccorso", "primo_soccorso"),
    "📚 Fonti": ("fonti", "fonti"),
    "❤️ Donazioni": ("donazioni", "donazioni"),
    "📜 Licenza": ("licenza", "licenza")
}

# Popola il dizionario page_modules con i moduli light se esistono, altrimenti usa i moduli standard
for key, (light_module, standard_module) in light_modules.items():
    # Verifica se esiste il modulo light
    light_path = f"modules/{light_module}.py"
    if os.path.exists(light_path):
        page_modules[key] = light_module
    else:
        page_modules[key] = standard_module

choice = st.sidebar.radio("Seleziona sezione", list(page_modules.keys()))

# Display selected page - caricamento sicuro del modulo selezionato
if choice:
    # Nome del modulo da caricare
    module_name = page_modules[choice]
    try:
        # Importa solo il modulo richiesto in modo sicuro
        module = importlib.import_module(f"modules.{module_name}")
        module.show()
    except Exception as e:
        st.error(f"Errore nel caricamento del modulo {module_name}: {e}")
        st.write("Riprova selezionando un'altra sezione.")
        st.write("Dettaglio errore per sviluppatori:", str(e))

# Info box in sidebar
st.sidebar.markdown("---")
st.sidebar.info(
    "**SismaVer2** è sviluppato da **Fabio SCELZO**.\n\n"
    "📧 Contatto: meteotorre@gmail.com"
)

# Footer 
st.sidebar.markdown("---")
st.sidebar.caption("© 2023-2024 Fabio SCELZO - Tutti i diritti riservati")