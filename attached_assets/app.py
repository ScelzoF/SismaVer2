import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
sb_client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        sb_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error("Errore di connessione a Supabase")
else:
    st.error("Mancano i secrets SUPABASE_URL e SUPABASE_KEY")

from modules import home
from modules import monitoraggio
from modules import emergenza
from modules import primo_soccorso
from modules import vulcani
from modules import segnala_evento
from modules import chat_pubblica
from modules import donazioni
from modules import fonti

st.set_page_config(page_title="SismaVer2", page_icon="🌍", layout="wide")

st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Italy_satellite_map_2020.jpg/300px-Italy_satellite_map_2020.jpg", use_container_width=True)
st.sidebar.title("🌍 SismaVer2")
scelta = st.sidebar.radio("📌 Vai a:", [
    "Home", "Monitoraggio", "Emergenza", "Primo soccorso",
    "Vulcani", "Segnalazioni", "Chat", "Donazioni", "Fonti"
])

if scelta == "Home":
    home.show()
elif scelta == "Monitoraggio":
    monitoraggio.show()
elif scelta == "Emergenza":
    emergenza.show()
elif scelta == "Primo soccorso":
    primo_soccorso.show()
elif scelta == "Vulcani":
    vulcani.show()
elif scelta == "Segnalazioni":
    segnala_evento.show()
elif scelta == "Chat":
    chat_pubblica.chat_pubblica(sb_client)
elif scelta == "Donazioni":
    donazioni.show()
elif scelta == "Fonti":
    fonti.show()