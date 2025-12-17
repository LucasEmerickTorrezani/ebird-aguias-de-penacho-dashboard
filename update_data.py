import csv
import os
from services.ebird_service import get_species_observations
from datetime import datetime


print("🚀 update_data.py started")

CSV_PATH = "data/observations.csv"

SPECIES = [
    "hareag1",
    "creeag1",
    "orheag1",
    "blheag1",
    "bawhae1",
]

# -----------------------------
# Load existing observations
# -----------------------------
existing_keys = set()

if os.path.exists(CSV_PATH):
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (
                row["species"],
                row["lat"],
                row["lng"],
                row["obsDt"],
                row["locName"],
            )
            existing_keys.add(key)

# -----------------------------
# Fetch new observations
# -----------------------------
rows_to_add = []

for species in SPECIES:
    observations = get_species_observations(species)

    for obs in observations:
        lat = obs.get("lat")
        lng = obs.get("lng")
        obs_dt = obs.get("obsDt")
        loc = obs.get("locName")

        if lat is None or lng is None or not obs_dt or not loc:
            continue

        key = (
            species,
            str(lat),
            str(lng),
            obs_dt,
            loc,
        )

        if key in existing_keys:
            continue

        rows_to_add.append({
            "species": species,
            "comName": obs.get("comName"),
            "locName": loc,
            "lat": lat,
            "lng": lng,
            "obsDt": obs_dt,
            "fetched_at": datetime.utcnow().isoformat(),

        })

# -----------------------------
# Append to CSV
# -----------------------------
file_exists = os.path.exists(CSV_PATH)

with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "species",
            "comName",
            "locName",
            "lat",
            "lng",
            "obsDt",
            "fetched_at"
        ],
    )

    if not file_exists:
        writer.writeheader()

    writer.writerows(rows_to_add)

print(f"✅ Added {len(rows_to_add)} new observations")
