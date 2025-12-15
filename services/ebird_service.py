from dotenv import load_dotenv
load_dotenv()

import os
import requests

EBIRD_API_KEY = os.getenv("EBIRD_API_KEY")

# Regions per species (biologically reasonable defaults)
SPECIES_REGIONS = {
    "harpy1": [
        # Sul
        "BR-PR", "BR-RS", "BR-SC",
        # Sudeste
        "BR-ES", "BR-MG", "BR-RJ", "BR-SP",
        # Nordeste
        "BR-BA", "BR-SE", "BR-AL", "BR-PE", "BR-PB",
        # Centro-Oeste
        "BR-MS", "BR-GO", "BR-DF",
    ],
    "creag1": [
        "BR-PR", "BR-RS", "BR-SC",
        "BR-ES", "BR-MG", "BR-RJ", "BR-SP",
        "BR-BA", "BR-SE", "BR-AL", "BR-PE", "BR-PB",
        "BR-MS", "BR-GO", "BR-DF",
    ],
    "orheag1": [
        "BR-PR", "BR-RS", "BR-SC",
        "BR-ES", "BR-MG", "BR-RJ", "BR-SP",
        "BR-BA", "BR-SE", "BR-AL", "BR-PE", "BR-PB",
        "BR-MS", "BR-GO", "BR-DF",
    ],
    "blheag1": [
        "BR-PR", "BR-RS", "BR-SC",
        "BR-ES", "BR-MG", "BR-RJ", "BR-SP",
        "BR-BA", "BR-SE", "BR-AL", "BR-PE", "BR-PB",
        "BR-MS", "BR-GO", "BR-DF",
    ],
    "bawhae1": [
        "BR-PR", "BR-RS", "BR-SC",
        "BR-ES", "BR-MG", "BR-RJ", "BR-SP",
        "BR-BA", "BR-SE", "BR-AL", "BR-PE", "BR-PB",
        "BR-MS", "BR-GO", "BR-DF",
    ],
}


def get_species_observations(species_code, back=30, limit=230):
    """
    Always returns a list.
    Zero observations is a valid result.
    """

    regions = SPECIES_REGIONS.get(species_code, [])
    all_observations = []

    headers = {
        "X-eBirdApiToken": EBIRD_API_KEY
    }

    params = {
        "back": back,
        "maxResults": limit
    }

    for region in regions:
        url = f"https://api.ebird.org/v2/data/obs/{region}/recent/{species_code}"

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=3
            )

            # 400 = species never recorded in this region
            if response.status_code == 400:
                continue

            response.raise_for_status()
            all_observations.extend(response.json())

        except requests.RequestException as e:
            # Never crash the app because of eBird
            print(f"eBird error for {species_code} in {region}: {e}")
            continue

    return all_observations

