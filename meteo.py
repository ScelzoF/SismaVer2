
def show():
    import streamlit as st
    import requests
    from streamlit_js_eval import streamlit_js_eval
    from datetime import datetime, timezone, timedelta
    import os

    st.title("🌤️ Meteo Attuale")

    # Ottieni la chiave API OpenWeather
    API_KEY = os.environ.get("OPENWEATHER_API_KEY")
    if not API_KEY:
        try:
            API_KEY = st.secrets.get("OPENWEATHER_API_KEY")
        except:
            pass
    if not API_KEY:
        st.error("⚠️ Chiave API meteo non configurata. Imposta `OPENWEATHER_API_KEY` nei secrets.")
        return

    metodo = st.radio("🔍 Metodo:", ["📍 Usa posizione attuale", "🏙️ Inserisci città"])
    url = None

    if metodo == "📍 Usa posizione attuale":
        coords = streamlit_js_eval(js_expressions='navigator.geolocation.getCurrentPosition((pos) => ({lat: pos.coords.latitude, lon: pos.coords.longitude}), (err) => ({error: err.message}))', key="geo")
        
        if coords and "lat" in coords and "lon" in coords:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={API_KEY}&units=metric&lang=it"
        else:
            st.warning("Geolocalizzazione non disponibile. Per favore, inserisci manualmente la tua città.")
            metodo = "🏙️ Inserisci città"

    if metodo == "🏙️ Inserisci città":
        città = st.text_input("Inserisci città", value="Napoli")
        if città:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={città}&appid={API_KEY}&units=metric&lang=it"

    if url:
        try:
            res = requests.get(url)
            data = res.json()
            if res.status_code != 200 or "main" not in data:
                st.error("❌ Località non trovata o errore nella richiesta.")
                return

            st.subheader(f"☁️ Meteo a {data['name']}")
            st.metric("🌡️ Temperatura", f"{data['main']['temp']} °C")
            st.metric("💧 Umidità", f"{data['main']['humidity']}%")
            st.metric("🌬️ Vento", f"{data['wind']['speed']} m/s")
            st.info(f"📌 Descrizione: {data['weather'][0]['description'].capitalize()}")

            st.warning("⚠️ Le previsioni meteo sono fornite da OpenWeather e potrebbero non essere completamente accurate o aggiornate in tempo reale.")
            st.info("Suggerimento: Per una corretta geolocalizzazione, esegui l'app su HTTPS (ad esempio tramite Streamlit Sharing).")
            
        except Exception as e:
            st.error(f"Errore nel recupero meteo: {e}")
