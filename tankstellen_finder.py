#!/usr/bin/env python3
"""
Tankstellen-Finder: Findet die 10 günstigsten Dieseltankstellen im Umkreis
Nutzt die Tankerkönig API
"""

import requests
import json
from typing import List, Dict, Optional
from geopy.geocoders import Nominatim
from geopy.distance import geodesic


class TankstellenFinder:
    """Finder für Dieseltankstellen basierend auf Postleitzahl"""

    API_BASE_URL = "https://creativecommons.tankerkoenig.de/json/list.php"
    API_KEY = "571f061f-8721-47b0-abe6-cd494b68db86"  # Von tankerkoenig.de besorgen
    RADIUS_KM = 5

    def __init__(self, api_key: str):
        """
        Initialisiert den Finder mit API-Key

        Args:
            api_key: API-Key von Tankerkönig
        """
        self.api_key = api_key
        self.geolocator = Nominatim(user_agent="tankstellen_finder")

    def get_coordinates_from_postcode(self, postcode: str) -> Optional[tuple]:
        """
        Konvertiert Postleitzahl zu Koordinaten (lat, lon)

        Args:
            postcode: Deutsche Postleitzahl

        Returns:
            Tuple (latitude, longitude) oder None
        """
        try:
            location = self.geolocator.geocode(f"{postcode}, Germany")
            if location:
                return (location.latitude, location.longitude)
            print(f"Fehler: Postleitzahl '{postcode}' nicht gefunden")
            return None
        except Exception as e:
            print(f"Fehler bei Geocoding: {e}")
            return None

    def get_gas_stations(self, latitude: float, longitude: float) -> Optional[List[Dict]]:
        """
        Ruft Tankstellen von Tankerkönig API ab

        Args:
            latitude: Breitengrad
            longitude: Längengrad

        Returns:
            Liste von Tankstellen oder None
        """
        try:
            params = {
                "lat": latitude,
                "lng": longitude,
                "rad": self.RADIUS_KM,
                "apikey": self.api_key,
                "type": "diesel",
                "sort": "price"
            }

            response = requests.get(self.API_BASE_URL, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                print(f"API Fehler: {data.get('message', 'Unbekannter Fehler')}")
                return None

            return data.get("stations", [])

        except requests.RequestException as e:
            print(f"Fehler beim API-Aufruf: {e}")
            return None

    def filter_and_sort_stations(self, stations: List[Dict],
                                  origin_lat: float,
                                  origin_lon: float) -> List[Dict]:
        """
        Filtert und sortiert Tankstellen nach Preis und Entfernung

        Args:
            stations: Liste von Tankstellen
            origin_lat: Referenz-Latitude
            origin_lon: Referenz-Longitude

        Returns:
            Sortierte Liste (Top 10 günstigste)
        """
        origin_coords = (origin_lat, origin_lon)

        # Filtere nach gültigem Preis
        valid_stations = [
            station for station in stations
            if station.get("price") is not None and station.get("price") != 0
        ]

        # Sortieren: zuerst nach Preis, dann nach Entfernung (dist kommt von API)
        sorted_stations = sorted(
            valid_stations,
            key=lambda x: (x.get("price", float("inf")), x.get("dist", 0))
        )

        return sorted_stations[:10]

    def find_cheapest_stations(self, postcode: str) -> List[Dict]:
        """
        Hauptmethode: Findet die 10 günstigsten Tankstellen

        Args:
            postcode: Deutsche Postleitzahl

        Returns:
            Liste der 10 günstigsten Tankstellen
        """
        print(f"Suche Tankstellen für Postleitzahl {postcode}...")

        # Koordinaten ermitteln
        coords = self.get_coordinates_from_postcode(postcode)
        if not coords:
            return []

        latitude, longitude = coords
        print(f"Koordinaten: {latitude:.4f}, {longitude:.4f}")

        # Tankstellen abrufen
        print(f"Rufe Tankstellen im Umkreis von {self.RADIUS_KM} km ab...")
        stations = self.get_gas_stations(latitude, longitude)

        if not stations:
            print("Keine Tankstellen gefunden")
            return []

        print(f"Gefunden: {len(stations)} Tankstellen")

        # Filtern und sortieren
        cheapest = self.filter_and_sort_stations(stations, latitude, longitude)

        return cheapest

    def display_results(self, stations: List[Dict]) -> None:
        """
        Zeigt die Ergebnisse formatiert an

        Args:
            stations: Liste von Tankstellen
        """
        if not stations:
            print("Keine Ergebnisse")
            return

        print("\n" + "="*80)
        print("DIE 10 GÜNSTIGSTEN DIESELTANKSTELLEN")
        print("="*80 + "\n")

        for i, station in enumerate(stations, 1):
            print(f"{i:2}. {station.get('name', 'Unbekannt'):<40}")
            print(f"    Adresse: {station.get('street', 'N/A')} "
                  f"{station.get('houseNumber', '')}")
            print(f"    PLZ/Ort: {station.get('postCode', '')} "
                  f"{station.get('place', '')}")
            print(f"    Preis: €{station.get('price', 0):.3f} "
                  f"| Entfernung: {station.get('dist', 0):.1f} km")
            print(f"    Marke: {station.get('brand', 'N/A')}")
            print()


def main():
    """Hauptprogramm"""
    print("╔════════════════════════════════════════╗")
    print("║    TANKSTELLEN-FINDER (Diesel)         ║")
    print("║    Powered by Tankerkönig API          ║")
    print("╚════════════════════════════════════════╝\n")

    # API-Key prüfen
    api_key = TankstellenFinder.API_KEY
    if api_key == "YOUR_API_KEY_HERE":
        print("⚠️  FEHLER: API-Key nicht konfiguriert!")
        print("Bitte folge diesen Schritten:")
        print("1. Gehe zu: https://creativecommons.tankerkoenig.de/")
        print("2. Registriere dich kostenlos")
        print("3. Kopiere deinen API-Key")
        print("4. Ersetze 'YOUR_API_KEY_HERE' in diesem Skript\n")
        return

    # Postleitzahl eingeben
    postcode = input("Gib eine deutsche Postleitzahl ein: ").strip()

    if not postcode or len(postcode) != 5 or not postcode.isdigit():
        print("Fehler: Ungültige Postleitzahl (muss 5 Ziffern sein)")
        return

    # Finder initialisieren und starten
    finder = TankstellenFinder(api_key)
    stations = finder.find_cheapest_stations(postcode)

    # Ergebnisse anzeigen
    finder.display_results(stations)


if __name__ == "__main__":
    main()
