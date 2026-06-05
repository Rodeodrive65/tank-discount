"""
Konfigurationsdatei für Tankstellen-Finder
Zentrale Stelle für alle Einstellungen
"""

import os
from typing import Optional

# ==================== API-KONFIGURATION ====================

# Tankerkönig API
TANKERKOENIG_API_KEY: str = os.getenv(
    'TANKERKOENIG_API_KEY',
    'YOUR_API_KEY_HERE'  # Ersetze mit deinem Key
)
TANKERKOENIG_API_URL: str = "https://creativecommons.tankerkoenig.de/json/list.php"

# ==================== SEARCH-PARAMETER ====================

# Suchradius in Kilometern
SEARCH_RADIUS_KM: float = 5.0

# Anzahl der anzuzeigenden Tankstellen
TOP_STATIONS_COUNT: int = 10

# Kraftstofftyp (diesel, e5, e10, lpg)
FUEL_TYPE: str = "diesel"

# ==================== GEOLOCATION ====================

# Nominatim User-Agent für OSM
GEOLOCATION_USER_AGENT: str = "tankstellen_finder_app"

# Timeout für Geocoding-Requests (Sekunden)
GEOCODING_TIMEOUT: int = 10

# ==================== API REQUESTS ====================

# Request Timeout (Sekunden)
API_REQUEST_TIMEOUT: int = 10

# Retry Versuche bei Fehler
API_MAX_RETRIES: int = 3

# ==================== LOGGING ====================

# Log-Level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL: str = "INFO"

# Log-Datei (None = nur Console)
LOG_FILE: Optional[str] = None  # z.B. "tankstellen.log"

# ==================== UI KONFIGURATION ====================

# App-Name
APP_NAME: str = "Tankstellen-Finder"

# App-Version
APP_VERSION: str = "1.0.0"

# ==================== VALIDATION ====================

MIN_POSTCODE_LENGTH: int = 5
MAX_POSTCODE_LENGTH: int = 5

# Gültige Länder für Suche
VALID_COUNTRIES: list = ["Germany", "Deutschland"]

# ==================== CACHE ====================

# Cache für Geocoding Anfragen aktivieren
ENABLE_CACHE: bool = True

# Cache-Verzeichnis
CACHE_DIR: str = ".cache"

# Cache-Ablauf in Sekunden (24h)
CACHE_TTL: int = 86400

# ==================== DATABASE (optional) ====================

# Wenn du Favoriten speichern möchtest:
DB_FILE: Optional[str] = None  # z.B. "favorites.db"

# ==================== MOBILVERSION ====================

# Minimale Android Version
MIN_ANDROID_VERSION: int = 21  # Android 5.0+

# App-ID für Android
ANDROID_APP_ID: str = "de.tankstellen.finder"

# ==================== HELPER FUNKTIONEN ====================

def is_configured() -> bool:
    """Prüft, ob API korrekt konfiguriert ist"""
    return TANKERKOENIG_API_KEY != "YOUR_API_KEY_HERE"


def get_config_status() -> dict:
    """Gibt aktuellen Konfigurationsstatus zurück"""
    return {
        "api_configured": is_configured(),
        "api_key_masked": TANKERKOENIG_API_KEY[:8] + "***" if is_configured() else "NOT SET",
        "search_radius": SEARCH_RADIUS_KM,
        "top_count": TOP_STATIONS_COUNT,
        "fuel_type": FUEL_TYPE,
        "app_version": APP_VERSION,
    }


if __name__ == "__main__":
    # Test-Ausgabe
    print("=" * 50)
    print("TANKSTELLEN-FINDER CONFIGURATION")
    print("=" * 50)
    for key, value in get_config_status().items():
        print(f"{key}: {value}")
    print("=" * 50)
