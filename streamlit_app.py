"""
Emilie's Tank Discount - Streamlit Web-App
Finde die günstigsten Tankstellen überall und auf jedem Gerät
"""

import streamlit as st
import requests
import math
import time
from typing import Optional, List, Dict

# Page Config
st.set_page_config(
    page_title="Emilie's Tank Discount",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Titel
st.title("💰 Emilie's Tank Discount")
st.markdown("*Finde die günstigsten Tankstellen in deiner Nähe*")

# App-Konfiguration
API_BASE_URL = "https://creativecommons.tankerkoenig.de/json/list.php"
API_KEY = "571f061f-8721-47b0-abe6-cd494b68db86"
RADIUS_KM = 5

# Sidebar für Eingaben
st.sidebar.header("🔍 Suche")

postcode = st.sidebar.text_input(
    "Postleitzahl (5-stellig):",
    placeholder="z.B. 10115",
    max_chars=5
)

fuel_type = st.sidebar.selectbox(
    "Treibstofftyp:",
    ["Diesel", "Super E10", "Super E5"],
    index=0
)

search_button = st.sidebar.button(
    "🔍 Suche starten",
    use_container_width=True,
    type="primary"
)

# Häufige deutsche Postleitzahlen (schneller Fallback)
POSTCODE_CACHE = {
    "10115": (52.5200, 13.4050),  # Berlin
    "49377": (52.7414, 8.2855),   # Vechta
    "80331": (48.1351, 11.5820),  # München
    "50667": (50.9418, 6.9483),   # Köln
    "20095": (53.5511, 9.9937),   # Hamburg
    "60311": (50.1109, 8.6821),   # Frankfurt
    "70173": (48.7758, 9.1829),   # Stuttgart
    "30159": (52.3759, 9.7320),   # Hannover
    "28195": (53.0950, 8.8017),   # Bremen
    "28217": (53.0970, 8.7680),   # Bremen-Walle
    "02826": (51.0504, 13.6552),  # Dresden
    "04109": (51.3397, 12.3731),  # Leipzig
    "90402": (49.4521, 11.0767),  # Nürnberg
    "98550": (50.9528, 11.5820),  # Coburg
    "37073": (51.5386, 9.9360),   # Göttingen
    "44135": (51.4556, 7.4116),   # Dortmund
    "64283": (49.8699, 8.6512),   # Darmstadt
    "22305": (53.5850, 10.0167),  # Hamburg-Alsterdorf
}

@st.cache_data(ttl=3600)
def get_coordinates_from_postcode(postcode: str) -> Optional[tuple]:
    """Konvertiert PLZ zu Koordinaten mit Geoapify"""
    try:
        # Nutze Geoapify (kostenlos, kein Rate Limiting!)
        response = requests.get(
            "https://api.geoapify.com/v1/geocode/search",
            params={
                "text": f"{postcode}, Germany",
                "apiKey": "ee04c76f8b354e3fa97f87e7e3a6fa56"
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("features") and len(data["features"]) > 0:
            coords = data["features"][0]["geometry"]["coordinates"]
            return (coords[1], coords[0])  # lat, lon
        
        st.error(f"❌ Postleitzahl '{postcode}' nicht gefunden")
        return None

    except Exception as e:
        st.error(f"❌ Fehler: {str(e)}")
        return None

def get_gas_stations(latitude: float, longitude: float, fuel_type: str) -> Optional[List[Dict]]:
    """Ruft Tankstellen von Tankerkönig API ab"""
    try:
        fuel_map = {
            "diesel": "diesel",
            "super e10": "e10",
            "super e5": "e5"
        }

        params = {
            "lat": latitude,
            "lng": longitude,
            "rad": RADIUS_KM,
            "apikey": API_KEY,
            "type": fuel_map.get(fuel_type.lower(), "diesel"),
            "sort": "price"
        }

        response = requests.get(API_BASE_URL, params=params, timeout=10)
        data = response.json()

        if not data.get("ok"):
            st.error(f"❌ API Fehler: {data.get('message', 'Unbekannter Fehler')}")
            return None

        return data.get("stations", [])

    except Exception as e:
        st.error(f"❌ Fehler beim API-Aufruf: {e}")
        return None


def filter_and_sort_stations(stations: List[Dict],
                            origin_lat: float,
                            origin_lon: float) -> List[Dict]:
    """Filtert und sortiert Tankstellen nach Preis"""
    valid_stations = [
        station for station in stations
        if station.get("price") is not None and station.get("price") != 0
    ]

    # Berechne Distanzen wenn nicht vorhanden
    for station in valid_stations:
        if not station.get("dist"):
            lat1, lon1 = math.radians(origin_lat), math.radians(origin_lon)
            lat2, lon2 = math.radians(station["lat"]), math.radians(station["lng"])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            km = 6371 * c
            station["dist"] = km

    # Sortiere nach Preis
    sorted_stations = sorted(
        valid_stations,
        key=lambda x: (x.get("price", float("inf")), x.get("dist", 0))
    )

    return sorted_stations[:10]


# Hauptlogik
if search_button:
    # Validierung
    if not postcode or len(postcode) != 5 or not postcode.isdigit():
        st.error("❌ Bitte gib eine gültige 5-stellige Postleitzahl ein")
    else:
        with st.spinner(f"⏳ Suche {fuel_type}-Tankstellen für PLZ {postcode}..."):
            # Koordinaten ermitteln
            coords = get_coordinates_from_postcode(postcode)
            if not coords:
                st.error(f"❌ Postleitzahl '{postcode}' nicht gefunden")
            else:
                latitude, longitude = coords
                st.success(f"✅ Koordinaten gefunden!")

                # Tankstellen abrufen
                stations = get_gas_stations(latitude, longitude, fuel_type)
                if not stations:
                    st.warning(f"⚠️ Keine {fuel_type}-Tankstellen in {RADIUS_KM} km Umkreis gefunden")
                else:
                    # Filtern und sortieren
                    cheapest = filter_and_sort_stations(stations, latitude, longitude)

                    if cheapest:
                        st.success(f"✅ {len(cheapest)} Tankstellen gefunden!")
                        st.markdown("---")

                        # Tabelle anzeigen
                        st.subheader("📊 Übersicht")
                        table_data = []
                        for i, station in enumerate(cheapest, 1):
                            table_data.append({
                                "Platz": i,
                                "Name": station.get('name', 'N/A'),
                                "Preis (€)": f"{station.get('price', 0):.3f}",
                                "Entfernung (km)": f"{station.get('dist', 0):.1f}"
                            })
                        st.dataframe(table_data, use_container_width=True)

                        st.markdown("---")
                        st.subheader("📍 Detaillierte Informationen")

                        # Detaillierte Ansicht
                        for i, station in enumerate(cheapest, 1):
                            st.write(f"**#{i} {station.get('name', 'Unbekannt')}**")
                            st.write(f"Marke: {station.get('brand', 'N/A')}")
                            st.write(f"Adresse: {station.get('street', 'N/A')} {station.get('houseNumber', '')}")
                            st.write(f"PLZ/Ort: {station.get('postCode', '')} {station.get('place', '')}")
                            st.write(f"💰 Preis: **€{station.get('price', 0):.3f}** | 📏 Entfernung: **{station.get('dist', 0):.1f} km**")
                            st.divider()
                    else:
                        st.warning("⚠️ Keine Ergebnisse nach Filterung")

# Info-Sektion
st.sidebar.markdown("---")
st.sidebar.markdown("""
### ℹ️ Über diese App

**Emilie's Tank Discount** hilft dir,
die günstigsten Tankstellen zu finden!

- 📍 Suche nach Postleitzahl
- ⛽ 4 Treibstofftypen
- 📊 Top 10 günstigste
- 🌍 Entfernungen berechnet

**API:** Tankerkönig (CC)
**Framework:** Streamlit
**Plattform:** Web (überall!)
""")
