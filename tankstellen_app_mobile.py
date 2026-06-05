"""
Emilie's Tank Discount - Finde die günstigsten Tankstellen
Native Desktop-App mit BeeWare/Toga
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from threading import Thread
import requests
from typing import List, Dict, Optional
import math

# Versuche geopy zu laden, fallback für Android
try:
    from geopy.geocoders import Nominatim
    from geopy.distance import geodesic
    HAS_GEOPY = True
except ImportError:
    HAS_GEOPY = False
    Nominatim = None
    geodesic = None


class TankstellenFinderApp(toga.App):
    """Emilie's Tank Discount - App für Tankstellen-Suche"""

    API_BASE_URL = "https://creativecommons.tankerkoenig.de/json/list.php"
    API_KEY = "571f061f-8721-47b0-abe6-cd494b68db86"
    RADIUS_KM = 5

    def startup(self):
        """Konstruiert die Benutzeroberfläche"""
        main_box = toga.Box(style=Pack(
            direction=COLUMN,
            padding=10,
            background_color='#f5f5f5'
        ))

        # Titel
        title_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        title = toga.Label(
            "Emilie's Tank Discount",
            style=Pack(
                padding=5,
                font_size=18,
                font_weight='bold',
                color='#333333'
            )
        )
        subtitle = toga.Label(
            'Finde die günstigsten Tankstellen in deiner Nähe',
            style=Pack(padding=5, font_size=12, color='#666666')
        )
        title_box.add(title)
        title_box.add(subtitle)

        # Input-Bereich
        input_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        postcode_label = toga.Label(
            'Postleitzahl (5-stellig):',
            style=Pack(padding=5)
        )
        self.postcode_input = toga.TextInput(
            placeholder='z.B. 10115',
            style=Pack(
                flex=1,
                padding=5,
                font_size=14,
                height=40
            )
        )

        # Treibstoff-Auswahl
        fuel_label = toga.Label(
            'Treibstofftyp:',
            style=Pack(padding=5, font_weight='bold')
        )

        fuel_box = toga.Box(style=Pack(direction=ROW, padding=5))
        self.fuel_type = toga.Selection(
            items=['Diesel', 'Super E10', 'Super E5', 'LPG'],
            value='Diesel',
            style=Pack(flex=1, padding=5)
        )
        fuel_box.add(self.fuel_type)

        # Button-Box
        button_box = toga.Box(style=Pack(direction=ROW, padding=5))
        self.search_button = toga.Button(
            'Suche starten',
            on_press=self.search_stations,
            style=Pack(
                flex=1,
                padding=5,
                background_color='#007AFF',
                color='#FFFFFF'
            )
        )
        self.clear_button = toga.Button(
            'Löschen',
            on_press=self.clear_results,
            style=Pack(flex=1, padding=5)
        )
        button_box.add(self.search_button)
        button_box.add(self.clear_button)

        input_box.add(postcode_label)
        input_box.add(self.postcode_input)
        input_box.add(fuel_label)
        input_box.add(fuel_box)
        input_box.add(button_box)

        # Results-Bereich
        results_label = toga.Label(
            'Ergebnisse:',
            style=Pack(padding=5, font_weight='bold')
        )

        self.results_container = toga.Box(
            style=Pack(direction=COLUMN, padding=5)
        )

        scroll_box = toga.ScrollContainer(
            content=self.results_container,
            style=Pack(
                flex=1,
                padding=10,
                background_color='#FFFFFF'
            )
        )

        # Status-Label
        self.status_label = toga.Label(
            'Bereit',
            style=Pack(
                padding=10,
                color='#666666',
                font_size=11
            )
        )

        # Alles zusammenfügen
        main_box.add(title_box)
        main_box.add(input_box)
        main_box.add(results_label)
        main_box.add(scroll_box)
        main_box.add(self.status_label)

        # App konfigurieren
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    def search_stations(self, widget):
        """Startet die Suche"""
        postcode = self.postcode_input.value.strip()
        fuel_type = self.fuel_type.value.lower().replace(' ', '')

        if not postcode or len(postcode) != 5 or not postcode.isdigit():
            self.status_label.text = '❌ Ungültige Postleitzahl (5 Ziffern erforderlich)'
            return

        if self.API_KEY == "YOUR_API_KEY_HERE":
            self.status_label.text = '❌ API-Key nicht konfiguriert'
            return

        self.search_button.enabled = False
        self.status_label.text = '⏳ Suche läuft...'
        self.results_container.clear()

        try:
            self.status_label.text = '⏳ Bestimme Koordinaten...'
            coords = self._get_coordinates_from_postcode(postcode)
            if not coords:
                self.status_label.text = f'❌ Postleitzahl "{postcode}" nicht gefunden'
                self.search_button.enabled = True
                return

            latitude, longitude = coords

            self.status_label.text = f'⏳ Lade {self.fuel_type.value}-Tankstellen im Umkreis von {self.RADIUS_KM} km...'
            stations = self._get_gas_stations(latitude, longitude, fuel_type)
            if not stations:
                self.status_label.text = '❌ Keine Tankstellen gefunden'
                self.search_button.enabled = True
                return

            cheapest = self._filter_and_sort_stations(stations, latitude, longitude, fuel_type)
            self._display_results(cheapest)

        except Exception as e:
            print(f"Fehler: {e}")
            self.status_label.text = f'❌ Fehler: {str(e)}'
        finally:
            self.search_button.enabled = True

    def _get_coordinates_from_postcode(self, postcode: str) -> Optional[tuple]:
        """Konvertiert PLZ zu Koordinaten"""
        if HAS_GEOPY:
            try:
                geolocator = Nominatim(user_agent="tankstellen_finder_app")
                location = geolocator.geocode(f"{postcode}, Germany", timeout=10)
                if location:
                    return (location.latitude, location.longitude)
            except Exception:
                pass

        try:
            response = requests.get(
                f"https://nominatim.openstreetmap.org/search",
                params={"q": f"{postcode}, Germany", "format": "json"},
                timeout=10
            )
            data = response.json()
            if data:
                return (float(data[0]["lat"]), float(data[0]["lon"]))
        except Exception:
            pass

        return None

    def _get_gas_stations(self, latitude: float, longitude: float, fuel_type: str = "diesel") -> Optional[List[Dict]]:
        """Ruft Tankstellen von API ab"""
        try:
            params = {
                "lat": latitude,
                "lng": longitude,
                "rad": self.RADIUS_KM,
                "apikey": self.API_KEY,
                "type": fuel_type,
                "sort": "price"
            }

            response = requests.get(self.API_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                return None

            return data.get("stations", [])

        except Exception:
            return None

    def _filter_and_sort_stations(self, stations: List[Dict],
                                   origin_lat: float,
                                   origin_lon: float,
                                   fuel_type: str = "diesel") -> List[Dict]:
        """Filtert und sortiert Tankstellen"""
        valid_stations = [
            station for station in stations
            if station.get("price") is not None and station.get("price") != 0
        ]

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

        sorted_stations = sorted(
            valid_stations,
            key=lambda x: (x.get("price", float("inf")), x.get("dist", 0))
        )

        return sorted_stations[:10]

    def _display_results(self, stations: List[Dict]):
        """Zeigt Ergebnisse in der GUI an"""
        self.results_container.clear()

        if not stations:
            label = toga.Label('Keine Ergebnisse', style=Pack(padding=5))
            self.results_container.add(label)
            self.status_label.text = f'❌ Keine Ergebnisse gefunden'
            return

        for i, station in enumerate(stations, 1):
            station_box = toga.Box(style=Pack(
                direction=COLUMN,
                padding=10,
                background_color='#E8F4F8'
            ))

            header_box = toga.Box(style=Pack(direction=ROW, padding=5))
            rank = toga.Label(
                f'#{i}',
                style=Pack(
                    padding=5,
                    font_size=16,
                    font_weight='bold',
                    color='#007AFF'
                )
            )
            name = toga.Label(
                station.get('name', 'Unbekannt')[:40],
                style=Pack(flex=1, padding=5, font_weight='bold')
            )
            header_box.add(rank)
            header_box.add(name)

            address = toga.Label(
                f"{station.get('street', '')} {station.get('houseNumber', '')}",
                style=Pack(padding=5, font_size=11, color='#555555')
            )

            city = toga.Label(
                f"{station.get('postCode', '')} {station.get('place', '')}",
                style=Pack(padding=5, font_size=11, color='#555555')
            )

            price_distance_box = toga.Box(style=Pack(direction=ROW, padding=5))
            price = toga.Label(
                f"💰 €{station.get('price', 0):.3f}",
                style=Pack(
                    flex=1,
                    padding=5,
                    font_size=13,
                    font_weight='bold',
                    color='#28A745'
                )
            )
            distance = toga.Label(
                f"📍 {station.get('dist', 0):.1f} km",
                style=Pack(flex=1, padding=5, font_size=12, color='#666666')
            )
            price_distance_box.add(price)
            price_distance_box.add(distance)

            station_box.add(header_box)
            station_box.add(address)
            station_box.add(city)
            station_box.add(price_distance_box)

            separator = toga.Divider(style=Pack(
                padding=5,
                color='#CCCCCC'
            ))

            self.results_container.add(station_box)
            self.results_container.add(separator)

        self.status_label.text = f'✅ {len(stations)} Tankstellen gefunden'

    def clear_results(self, widget):
        """Löscht Eingabe und Ergebnisse"""
        self.postcode_input.value = ''
        self.results_container.clear()
        self.status_label.text = 'Bereit'


def main():
    return TankstellenFinderApp(
        "Emilie's Tank Discount",
        'de.emilie.tankdiscount'
    )


if __name__ == '__main__':
    app = main()
    app.main_loop()
