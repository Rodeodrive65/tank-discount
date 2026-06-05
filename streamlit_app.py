"""
Emilie's Tank Discount - Streamlit Web-App
Finde die günstigsten Tankstellen überall und auf jedem Gerät
"""

import streamlit as st
import requests
import math
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
    ["Diesel", "Super E10", "Super E5", "LPG"],
    index=0
)

search_button = st.sidebar.button(
    "🔍 Suche starten",
    use_container_width=True,
    type="primary"
)

# Hilfsfunktionen
def get_coordinates_from_postcode(postcode: str) -> Optional[tuple]:
    """Konvertiert PLZ zu Koordinaten (OpenStreetMap)"""
    try:
        # Versuche Nominatim mit besseren Parametern
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{postcode}, Germany",
                "format": "json",
                "limit": 1
            },
            timeout=15,
            headers={"User-Agent": "EmiliesTankDiscount/1.0"},
            allow_redirects=True
        )
        response.raise_for_status()

        # Überprüfe, ob die Antwort gültig ist
        if response.status_code == 200 and response.text:
            data = response.json()
            if data and len(data) > 0:
                return (float(data[0]["lat"]), float(data[0]["lon"]))

        st.error(f"❌ Postleitzahl '{postcode}' konnte nicht gefunden werden")
        return None

    except requests.exceptions.Timeout:
        st.error("❌ Timeout: API antwortet zu langsam. Versuche es später nochmal.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Verbindungsfehler: Prüfe deine Internetverbindung.")
        return None
    except ValueError as e:
        st.error(f"❌ Fehler beim Parsen der API-Antwort. Versuche es in ein paar Sekunden nochmal.")
        return None
    except Exception as e:
        st.error(f"❌ Unerwarteter Fehler: {str(e)}")
        return None


def get_gas_stations(latitude: float, longitude: float, fuel_type: str) -> Optional[List[Dict]]:
    """Ruft Tankstellen von Tankerkönig API ab"""
    try:
        fuel_map = {
            "diesel": "diesel",
            "super e10": "e10",
            "super e5": "e5",
            "lpg": "lpg"
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
