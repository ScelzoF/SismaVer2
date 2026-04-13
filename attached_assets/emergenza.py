from modules.dati_regioni_b import dati_regioni_b
from modules.dati_regioni_c import dati_regioni_c
import streamlit as st


dati_regioni = {
    "Marche": {
        "criticita": "Rischio sismico elevato nelle aree interne e rischio idrogeologico in tutto il territorio regionale.",
        "punti_raccolta": [
            "Ancona: Piazza Cavour, Parco del Cardeto",
            "Pesaro: Piazza del Popolo, Parco Miralfiore",
            "Macerata: Piazza della Libertà, Giardini Diaz",
            "Ascoli Piceno: Piazza del Popolo, Parco Annunziata",
            "Fermo: Piazza del Popolo, Parco della Mentuccia"
        ],
        "link_utili": {
            "Protezione Civile Marche": "https://www.protezionecivile.marche.it/"
        },
        "rischio_idrogeologico": {
            "descrizione": "Alluvioni e frane frequenti, soprattutto nelle vallate e zone collinari.",
            "link": "https://www.protezionecivile.marche.it/Allertamento/"
        }
    },

        "criticita": "Rischio idrogeologico molto elevato, soprattutto per frane e alluvioni nelle aree costiere e collinari.",
        "punti_raccolta": [
            "Genova: Piazza De Ferrari, Giardini di Brignole",
            "La Spezia: Piazza Europa, Parco XXV Aprile",
            "Savona: Piazza Mameli, Giardini del Priamar",
            "Imperia: Piazza Dante, Parco Urbano San Leonardo"
        ],
        "link_utili": {
            "Protezione Civile Liguria": "https://protezionecivile.regione.liguria.it/"
        },
        "rischio_idrogeologico": {
            "descrizione": "Alluvioni ricorrenti, frane nelle aree collinari, rischio molto alto nelle 4 province.",
            "link": "https://allertaliguria.regione.liguria.it/"
        }
    },

    "Lazio": {
        "criticita": (
            "Il Lazio presenta un rischio sismico significativo nelle zone interne, in particolare nelle province di Rieti e Frosinone. "
            "Sono presenti anche fenomeni di dissesto idrogeologico, frane e alluvioni in diverse aree collinari e costiere."
        ),
        "punti_raccolta": [
            "Roma: Piazza del Popolo, Piazza Venezia, Parco della Caffarella",
            "Latina: Piazza del Popolo, Parco Falcone-Borsellino",
            "Frosinone: Piazza della Libertà, Villa Comunale",
            "Rieti: Piazza Vittorio Emanuele II, Parco San Francesco",
            "Viterbo: Piazza del Plebiscito, Parco Prato Giardino"
        ],
        "link_utili": {
            "Protezione Civile Lazio": "https://www.regione.lazio.it/protezionecivile",
            "Piani emergenza Lazio": "https://www.regione.lazio.it/protezionecivile/piani-emergenza"
        }
    },
    "Emilia Romagna": {
        "criticita": "Rischio alluvioni frequente, rischio sismico appenninico.",
        "punti_raccolta": [
            "Bologna: Piazza Maggiore, Giardini Margherita",
            "Modena: Piazza Grande, Parco Novi Sad",
            "Parma: Piazza Garibaldi, Parco Ducale",
            "Rimini: Piazzale Fellini, Parco Cervi",
            "Reggio Emilia: Piazza Prampolini, Parco del Popolo",
            "Ferrara: Piazza Castello, Parco Massari",
            "Forlì: Piazza Saffi, Parco della Resistenza",
            "Piacenza: Piazza Cavalli, Parco della Galleana",
            "Ravenna: Piazza del Popolo, Giardini Pubblici",
            "Cesena: Piazza del Popolo, Parco della Rimembranza"
        ],
        "link_utili": {
            "Protezione Civile Emilia-Romagna": "https://www.protezionecivile.emilia-romagna.it/",
            "ARPAE Emilia-Romagna": "https://www.arpae.it"
        }
    }
,
    "Basilicata": {
        "criticita": "Zona sismica e rischio idrogeologico elevato nelle zone montuose e lungo i fiumi principali.",
        "punti_raccolta": [
            "Potenza: Piazza Mario Pagano, Parco di Montereale",
            "Matera: Piazza Vittorio Veneto, Parco Giovanni Paolo II"
        ],
        "link_utili": {
            "Protezione Civile Basilicata": "https://protezionecivile.regione.basilicata.it/"
        },
        "rischio_idrogeologico": {
            "descrizione": "Forte rischio idrogeologico per frane e alluvioni lungo i principali corsi d'acqua e nelle aree montuose.",
            "link": "https://rsdi.regione.basilicata.it/#"
        }
    },
    "Calabria": {
        "criticita": "Alta criticità sismica e forte rischio idrogeologico, specie nelle zone costiere e interne collinari.",
        "punti_raccolta": [
            "Catanzaro: Piazza Matteotti, Parco della Biodiversità",
            "Reggio Calabria: Piazza Italia, Lungomare Falcomatà",
            "Cosenza: Piazza Bilotti, Villa Vecchia",
            "Crotone: Piazza Pitagora, Parco delle Rose"
        ],
        "link_utili": {
            "Protezione Civile Calabria": "https://www.protezionecivilecalabria.it/"
        },
        "rischio_idrogeologico": {
            "descrizione": "Criticità idrogeologiche diffuse, specie nelle zone collinari e costiere, rischio frane e alluvioni.",
            "link": "https://protezionecivilecalabria.it/"
        }
    },
    "Lazio": {
        "criticita": "Rischio sismico significativo nelle zone interne, fenomeni di dissesto idrogeologico nelle aree collinari e costiere.",
        "punti_raccolta": [
            "Roma: Piazza del Popolo, Piazza Venezia, Parco della Caffarella",
            "Latina: Piazza del Popolo, Parco Falcone-Borsellino",
            "Frosinone: Piazza della Libertà, Villa Comunale",
            "Rieti: Piazza Vittorio Emanuele II, Parco San Francesco",
            "Viterbo: Piazza del Plebiscito, Parco Prato Giardino"
        ],
        "link_utili": {
            "Protezione Civile Lazio": "https://www.regione.lazio.it/protezionecivile"
        },
        "rischio_idrogeologico": {
            "descrizione": "Rischio frane e alluvioni diffuso in zone interne e lungo la costa laziale.",
            "link": "https://www.regione.lazio.it/protezionecivile/piani-emergenza"
        }
    },
    "Emilia Romagna": {
        "criticita": "Rischio alluvioni frequente, rischio sismico appenninico.",
        "punti_raccolta": [
            "Bologna: Piazza Maggiore, Giardini Margherita",
            "Modena: Piazza Grande, Parco Novi Sad",
            "Parma: Piazza Garibaldi, Parco Ducale",
            "Rimini: Piazzale Fellini, Parco Cervi",
            "Reggio Emilia: Piazza Prampolini, Parco del Popolo",
            "Ferrara: Piazza Castello, Parco Massari",
            "Forlì: Piazza Saffi, Parco della Resistenza",
            "Piacenza: Piazza Cavalli, Parco della Galleana",
            "Ravenna: Piazza del Popolo, Giardini Pubblici",
            "Cesena: Piazza del Popolo, Parco della Rimembranza"
        ],
        "link_utili": {
            "Protezione Civile Emilia-Romagna": "https://www.protezionecivile.emilia-romagna.it/"
        },
        "rischio_idrogeologico": {
            "descrizione": "Frequenti alluvioni nelle aree pianeggianti e costiere, rischio frane nelle zone appenniniche.",
            "link": "https://protezionecivile.regione.emilia-romagna.it/rischio-idrogeologico"
        }
    },
    "Lombardia": {
        "criticita": "Rischio idrogeologico elevato nelle zone montuose e alpine, rischio sismico basso/moderato.",
        "punti_raccolta": [
            "Milano: Piazza Duomo, Parco Sempione",
            "Bergamo: Piazza Vecchia, Parco della Trucca",
            "Brescia: Piazza della Loggia, Parco Tarello",
            "Como: Piazza Cavour, Giardini a Lago"
        ],
        "link_utili": {
            "Protezione Civile Lombardia": "https://www.regione.lombardia.it/wps/portal/istituzionale/HP/servizi-e-informazioni/Cittadini/sicurezza-e-pronto-intervento/protezione-civile"
        },
        "rischio_idrogeologico": {
            "descrizione": "Rischio frane elevato nelle zone montane e prealpine, alluvioni frequenti nelle zone di pianura.",
            "link": "https://www.territorio.regione.lombardia.it/it/difesa-del-suolo"
        }
    },
    "Piemonte": {
        "criticita": "Significativo rischio idrogeologico in aree alpine e collinari, rischio sismico basso.",
        "punti_raccolta": [
            "Torino: Piazza Castello, Parco del Valentino",
            "Novara: Piazza Martiri, Parco Allea",
            "Alessandria: Piazza della Libertà, Parco Carrà",
            "Cuneo: Piazza Galimberti, Parco della Resistenza"
        ],
        "link_utili": {
            "Protezione Civile Piemonte": "https://www.regione.piemonte.it/web/temi/protezione-civile-difesa-suolo-opere-pubbliche"
        },
        "rischio_idrogeologico": {
            "descrizione": "Frane e alluvioni frequenti in ambito alpino e collinare.",
            "link": "https://www.regione.piemonte.it/web/temi/protezione-civile-difesa-suolo-opere-pubbliche/rischio-idrogeologico"
        }
    }

}

def show():
    st.title("🚨 Emergenza Regionale")
    st.write("Informazioni di emergenza, punti di raccolta e contatti utili per ciascuna regione italiana.")
    
    # Contenitore per il filtro di tipo emergenza
    filter_container = st.container()
    
    with filter_container:
        # Menù unificato per tipo emergenza (collegato al modulo principale)
        st.session_state.setdefault('tipo_emergenza_selezionato', '🔴 Tutte le emergenze')
        tipo_emergenza = st.radio(
            "⚠️ Filtra per tipo di emergenza:",
            ["🔴 Tutte le emergenze", "🌋 Terremoto", "🌊 Alluvione", "🔥 Incendio"],
            index=["🔴 Tutte le emergenze", "🌋 Terremoto", "🌊 Alluvione", "🔥 Incendio"].index(st.session_state.tipo_emergenza_selezionato),
            horizontal=True,
            key="tipo_emergenza_radio_asset"
        )
        st.session_state.tipo_emergenza_selezionato = tipo_emergenza
    
    # Selettore regione
    regione_sel = st.selectbox("Seleziona la tua regione", sorted(dati_regioni.keys()), key="regione_selector_asset")
    
    if regione_sel in dati_regioni:
        dati = dati_regioni[regione_sel]
        
        # Organizziamo il layout in due colonne per ottenere una visualizzazione migliore
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("### 🛑 Criticità territoriali")
            st.markdown(dati["criticita"])

            st.markdown("### 📍 Punti di raccolta")
            max_punti = min(5, len(dati["punti_raccolta"]))
            for i, punto in enumerate(dati["punti_raccolta"]):
                if i < max_punti:
                    st.markdown(f"- {punto}")
                else:
                    # Se ci sono più di 5 punti, mostriamo un messaggio
                    if i == max_punti:
                        st.info(f"Altri {len(dati['punti_raccolta']) - max_punti} punti disponibili. Consulta il sito della Protezione Civile regionale.")
                    break

            st.markdown("### 🔗 Link utili")
            for titolo, url in dati["link_utili"].items():
                st.markdown(f"- [{titolo}]({url})")
                
        with col2:
            # Numeri utili in colonna 2
            st.markdown("### ☎️ Numeri utili")
            st.markdown("""
            - **112** - Numero Unico Emergenze
            - **115** - Vigili del Fuoco
            - **118** - Emergenza Sanitaria
            - **1515** - Emergenza Ambientale
            - **1530** - Emergenza in Mare
            """)
            
            # Rischio Idrogeologico
            if "rischio_idrogeologico" in dati:
                st.markdown("### 🌧️ Rischio Idrogeologico")
                st.markdown(dati["rischio_idrogeologico"]["descrizione"])
                st.markdown(f"[Maggiori informazioni]({dati['rischio_idrogeologico']['link']})")
    else:
        st.error(f"Dati non disponibili per la regione {regione_sel}")


dati_regioni.update(dati_regioni_b)
dati_regioni.update(dati_regioni_c)
