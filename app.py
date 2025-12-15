from flask import Flask, render_template, request
from datetime import datetime
import csv
import os

app = Flask(__name__)

# -----------------------------
# CSV configuration
# -----------------------------
CSV_PATH = "data/observations.csv"


def load_observations_from_csv():
    observations = []

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            observations.append({
                "species": row["species"],
                "comName": row["comName"],
                "locName": row["locName"],
                "lat": float(row["lat"]),
                "lng": float(row["lng"]),
                "obsDt": row["obsDt"],
            })

    return observations


def get_last_updated_time():
    timestamp = os.path.getmtime(CSV_PATH)
    return datetime.fromtimestamp(timestamp)


# -----------------------------
# Species metadata
# -----------------------------
SPECIES = {
    "hareag1": {
        "pt": "Gavião-real",
        "en": "Harpy Eagle",
        "sci": "Harpia harpyja",
    },
    "creeag1": {
        "pt": "Uiraçu",
        "en": "Crested Eagle",
        "sci": "Morphnus guianensis",
    },
    "orheag1": {
        "pt": "Gavião-de-penacho",
        "en": "Ornate Hawk-Eagle",
        "sci": "Spizaetus ornatus",
    },
    "blheag1": {
        "pt": "Gavião-pega-macaco",
        "en": "Black Hawk-Eagle",
        "sci": "Spizaetus tyrannus",
    },
    "bawhae1": {
        "pt": "Gavião-pato",
        "en": "Black-and-white Hawk-Eagle",
        "sci": "Spizaetus melanoleucus",
    },
}

DEFAULT_SPECIES = "hareag1"
DEFAULT_NAME_MODE = "pt"  # pt | en | sci


# -----------------------------
# Main route
# -----------------------------
@app.route("/")
def dashboard():
    species_code = request.args.get("species", DEFAULT_SPECIES)
    name_mode = request.args.get("name", DEFAULT_NAME_MODE)

    if species_code not in SPECIES:
        species_code = DEFAULT_SPECIES

    if name_mode not in ("pt", "en", "sci"):
        name_mode = DEFAULT_NAME_MODE

    # 🔹 Load CSV (single source of truth)
    csv_observations = load_observations_from_csv()

    # 🔹 Last updated (CSV file timestamp)
    last_updated = get_last_updated_time()
    last_updated_display = last_updated.strftime("%d/%m/%Y %H:%M")

    # 🔹 Selected species only
    observations = [
        o for o in csv_observations
        if o["species"] == species_code
    ]

    # 🔹 Sort by date (newest first)
    observations.sort(
        key=lambda o: o.get("obsDt", ""),
        reverse=True,
    )

    # 🔹 Format observations for display
    for obs in observations:
        obs["displayName"] = SPECIES[species_code][name_mode]
        obs["obsDt_display"] = "—"

        raw = obs.get("obsDt")
        if raw:
            raw = raw.replace("T", " ")
            date_part = raw.split(" ")[0]
            try:
                y, m, d = date_part.split("-")
                obs["obsDt_display"] = f"{d}/{m}/{y}"
            except ValueError:
                pass

    # 🔹 Totals (CSV-based)
    totals_by_species = {
        code: sum(1 for o in csv_observations if o["species"] == code)
        for code in SPECIES.keys()
    }
    total_all = sum(totals_by_species.values())

    return render_template(
        "index.html",
        species=species_code,
        species_name=SPECIES[species_code],
        species_list=SPECIES,
        observations=observations,
        name_mode=name_mode,
        totals_by_species=totals_by_species,
        total_all=total_all,
        last_updated=last_updated_display,
        SPECIES=SPECIES,
    )


# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)