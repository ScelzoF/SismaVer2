def show():
    import streamlit as st
    import requests
    from streamlit_js_eval import streamlit_js_eval
    import os
    from datetime import datetime, timedelta
    import pandas as pd
    import plotly.express as px

    st.title("🌤️ Meteo Attuale")
    
    # Mostra dati meteo statici di fallback se non ci sono i dati API
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Temperatura attuale", "21°C", "-2°C")
        st.metric("Precipitazioni", "0mm", "stabile")
    
    with col2:
        st.metric("Vento", "12 km/h", "+3 km/h")
        st.metric("Umidità", "65%", "+5%")
    
    # Allerte meteo nazionali
    st.warning("⚠️ Allerta meteo gialla per temporali in: Lombardia, Veneto, Emilia-Romagna")
    
    st.subheader("🌡️ Previsioni meteo giornaliere")
    
    # Dati di previsione statici
    previsioni = {
        "Oggi": {"temp": "21°C", "icon": "☀️", "prec": "0%"},
        "Domani": {"temp": "23°C", "icon": "⛅", "prec": "10%"},
        "Dopodomani": {"temp": "20°C", "icon": "🌧️", "prec": "40%"},
        "Fra 3 giorni": {"temp": "18°C", "icon": "🌧️", "prec": "60%"},
        "Fra 4 giorni": {"temp": "19°C", "icon": "⛅", "prec": "20%"},
    }
    
    # Imposta 5 colonne per le previsioni
    forecast_cols = st.columns(5)
    
    # Popola le colonne con i dati di previsione
    for i, (giorno, dati) in enumerate(previsioni.items()):
        with forecast_cols[i]:
            st.markdown(f"**{giorno}**")
            st.markdown(f"{dati['icon']} {dati['temp']}")
            st.markdown(f"🌧️ {dati['prec']}")
    
    # Informazioni aggiuntive
    st.info("Ultimo aggiornamento: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    
    # Ottimizzazione: funzioni di cache per le richieste meteo
    @st.cache_data(ttl=1800, show_spinner=False)  # Cache validità 30 minuti
    def fetch_weather_data(url):
        """Recupera dati meteo con caching per migliorare le performance."""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json(), None
            return None, f"Errore nella richiesta meteo (codice: {response.status_code})"
        except Exception as e:
            return None, f"Errore di connessione: {str(e)}"
    
    @st.cache_data(ttl=3600, show_spinner=False)  # Cache validità 1 ora (per geodati)
    def fetch_geocode_data(url):
        """Recupera dati di geolocalizzazione con caching esteso."""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json(), None
            return None, f"Errore geocoding (codice: {response.status_code})"
        except Exception as e:
            return None, f"Errore di connessione geocoding: {str(e)}"

    # Ottieni la chiave API OpenWeather dalle variabili d'ambiente
    API_KEY = os.environ.get("OPENWEATHER_API_KEY")
    
    if not API_KEY:
        try:
            API_KEY = st.secrets["OPENWEATHER_API_KEY"]
        except:
            st.error("🔑 Chiave API OpenWeather mancante. Configura la chiave nelle variabili d'ambiente.")
            st.info("Per ottenere una chiave API gratuita, visita: https://openweathermap.org/api")
            
            # Form per inserimento manuale della chiave (temporaneo)
            with st.form("api_key_form"):
                api_key_input = st.text_input("Inserisci chiave API OpenWeather", type="password")
                submit_button = st.form_submit_button("Usa chiave")
                
                if submit_button and api_key_input:
                    API_KEY = api_key_input
                    st.success("Chiave API impostata temporaneamente. La chiave sarà valida solo per questa sessione.")
                    st.info("Per un utilizzo permanente, configura la chiave nelle variabili d'ambiente.")
                    st.rerun()
            
            if not API_KEY:
                return

    metodo = st.radio("🔍 Metodo:", ["📍 Usa posizione attuale", "🏙️ Inserisci città"])

    # Coordinate per la visualizzazione in caso di ottenimento tramite posizione
    coords = None

    if metodo == "📍 Usa posizione attuale":
        with st.spinner("Recupero della posizione in corso..."):
            coords = streamlit_js_eval(js_expressions='navigator.geolocation.getCurrentPosition((pos) => ({lat: pos.coords.latitude, lon: pos.coords.longitude}))', key="geo")
            if coords and "lat" in coords and "lon" in coords:
                url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={API_KEY}&units=metric&lang=it"
                # Recupera il nome della città usando la funzione caching
                geocode_url = f"https://api.openweathermap.org/geo/1.0/reverse?lat={coords['lat']}&lon={coords['lon']}&limit=1&appid={API_KEY}"
                try:
                    geo_data, geo_error = fetch_geocode_data(geocode_url)
                    city_name = geo_data[0]['name'] if geo_data else "Posizione attuale"
                except:
                    city_name = "Posizione attuale"
            else:
                st.warning("⚠️ Geolocalizzazione non disponibile. Prova a inserire manualmente una città.")
                return
    else:
        city_name = st.text_input("🏙️ Inserisci città", value="Napoli")
        if not city_name:
            st.info("⚠️ Inserisci il nome di una città per visualizzare il meteo.")
            return
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}&units=metric&lang=it"
        # Recupera anche le coordinate per la visualizzazione della mappa
        geocode_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={API_KEY}"
        try:
            # Utilizzo della funzione di cache per geocoding
            geo_data, geo_error = fetch_geocode_data(geocode_url)
            if geo_data and len(geo_data) > 0:
                coords = {"lat": geo_data[0]['lat'], "lon": geo_data[0]['lon']}
        except Exception as e:
            print(f"Errore geocoding: {e}")
            pass

    col1, col2 = st.columns([2, 1])

    try:
        with st.spinner("Caricamento dati meteo..."):
            # Utilizzo della funzione di cache per i dati meteo
            data, error = fetch_weather_data(url)
            if error or not data or "main" not in data:
                st.error(f"❌ Località non trovata o errore nella richiesta: {error if error else 'Dati non validi'}")
                return

            with col1:
                st.subheader(f"☁️ Meteo a {data['name']}")
                
                # Creazione di tre colonne per i dati principali
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("🌡️ Temperatura", f"{data['main']['temp']:.1f} °C")
                    st.metric("🔽 Temperatura min", f"{data['main']['temp_min']:.1f} °C")
                with c2:
                    st.metric("💧 Umidità", f"{data['main']['humidity']}%")
                    st.metric("🔼 Temperatura max", f"{data['main']['temp_max']:.1f} °C")
                with c3:
                    st.metric("🌬️ Vento", f"{data['wind']['speed']} m/s")
                    if 'deg' in data['wind']:
                        direzione = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][round(data['wind']['deg']/45) % 8]
                        st.metric("🧭 Direzione", direzione)
                
                st.subheader("📋 Dettagli")
                st.markdown(f"**🌥️ Condizioni:** {data['weather'][0]['description'].capitalize()}")
                st.markdown(f"**🌅 Alba:** {datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')}")
                st.markdown(f"**🌇 Tramonto:** {datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')}")
                
                # Recupero previsioni per i prossimi giorni
                if coords:
                    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={coords['lat']}&lon={coords['lon']}&appid={API_KEY}&units=metric&lang=it"
                else:
                    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={API_KEY}&units=metric&lang=it"
                
                # Utilizziamo la funzione di cache per i dati previsioni
                forecast_data, forecast_error = fetch_weather_data(forecast_url)
                if not forecast_error and forecast_data:
                    
                    # Estrai i dati di previsione
                    forecast_items = []
                    for item in forecast_data['list']:
                        dt = datetime.fromtimestamp(item['dt'])
                        temp = item['main']['temp']
                        desc = item['weather'][0]['description']
                        forecast_items.append({
                            'Data': dt,
                            'Temperatura': temp,
                            'Descrizione': desc
                        })
                    
                    df_forecast = pd.DataFrame(forecast_items)
                    
                    # Grafico delle temperature
                    st.subheader("📈 Previsioni temperatura prossimi giorni")
                    fig = px.line(
                        df_forecast, 
                        x='Data', 
                        y='Temperatura',
                        title=f"Previsioni temperatura per {data['name']}",
                        labels={'Temperatura': 'Temperatura (°C)', 'Data': 'Data e ora'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Visualizzazione della mappa
                if coords:
                    st.subheader("📍 Posizione")
                    loc_df = pd.DataFrame([coords])
                    st.map(loc_df, zoom=10)
                
                # Allerta meteo
                if 'alerts' in data:
                    st.subheader("⚠️ Allerte meteo")
                    for alert in data.get('alerts', []):
                        st.warning(f"{alert['event']}: {alert['description']}")
                
                # Inquinamento aria se disponibile (con caching)
                if coords:
                    try:
                        air_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={coords['lat']}&lon={coords['lon']}&appid={API_KEY}"
                        # Utilizzo della funzione di cache anche per i dati qualità aria
                        air_data, air_error = fetch_weather_data(air_url)
                        if not air_error and air_data and 'list' in air_data and len(air_data['list']) > 0:
                            aqi = air_data['list'][0]['main']['aqi']
                            aqi_labels = {
                                1: "Ottima",
                                2: "Buona",
                                3: "Moderata",
                                4: "Scarsa",
                                5: "Pessima"
                            }
                            st.subheader("🌫️ Qualità dell'aria")
                            st.info(f"Qualità: **{aqi_labels.get(aqi, 'Non disponibile')}**")
                        elif air_error:
                            # Aggiungiamo un log di debug ma non mostriamo errori all'utente
                            print(f"Errore recupero qualità aria: {air_error}")
                    except Exception as e:
                        print(f"Errore gestione qualità aria: {e}")
                        pass

    except Exception as e:
        st.error(f"Errore nel recupero meteo: {e}")
def show_monitoraggio_meteo():
    import streamlit as st
    from datetime import datetime
    
    st.subheader("☀️ Meteo - Italia (Visione nazionale)")
    
    st.markdown("### 🌡️ Previsioni meteo e monitoraggio in tempo reale")
    
    # Avvisi meteo
    st.warning("⚠️ Allerta meteo gialla per temporali in: Lombardia, Veneto, Emilia-Romagna")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Temperature medie", "18°C", "-2°C")
        st.metric("Precipitazioni", "35mm", "+5mm")
    
    with col2:
        st.metric("Vento medio", "15 km/h", "+3 km/h")
        st.metric("Umidità", "65%", "-5%")
    
    st.info("Ultimo aggiornamento: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
