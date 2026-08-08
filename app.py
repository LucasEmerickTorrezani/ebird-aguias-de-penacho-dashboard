from flask import Flask, render_template, request
from datetime import datetime
import csv
import os

# static_url_path="" serves public/ at the site root (e.g. public/css/style.css
# -> /css/style.css). Vercel's convention is to CDN-serve a top-level public/
# directory directly, bypassing the Python function; this config makes local
# dev and Render serve the exact same URLs via Flask's own static handling.
app = Flask(__name__, static_folder="public", static_url_path="")

# -----------------------------
# CSV configuration
# -----------------------------
# Absolute, based on this file's location rather than the process's current
# working directory — relative paths aren't reliable in serverless runtimes.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "observations.csv")
LAST_UPDATED_PATH = os.path.join(BASE_DIR, "data", "last_updated.txt")


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
    # The update workflow stamps this file with the run time in UTC. Prefer
    # it over the CSV's filesystem mtime, which gets reset to build/deploy
    # time on platforms that repackage files (e.g. Vercel).
    if os.path.exists(LAST_UPDATED_PATH):
        with open(LAST_UPDATED_PATH, encoding="utf-8") as f:
            raw = f.read().strip()
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            pass

    timestamp = os.path.getmtime(CSV_PATH)
    return datetime.fromtimestamp(timestamp)


# -----------------------------
# Species metadata
#
# To add a new species: add one entry here (with a "color") and drop a
# matching "<code>.jpg" image into static/images/. Nothing else in the
# app needs to change — the map, legend, cards and totals all read from
# this dict.
# -----------------------------
SPECIES = {
    "hareag1": {
        "pt": "Gavião-real",
        "en": "Harpy Eagle",
        "sci": "Harpia harpyja",
        "color": "#00e08a",
    },
    "creeag1": {
        "pt": "Uiraçu",
        "en": "Crested Eagle",
        "sci": "Morphnus guianensis",
        "color": "#ffcc33",
    },
    "orheag1": {
        "pt": "Gavião-de-penacho",
        "en": "Ornate Hawk-Eagle",
        "sci": "Spizaetus ornatus",
        "color": "#ff6b4a",
    },
    "blheag1": {
        "pt": "Gavião-pega-macaco",
        "en": "Black Hawk-Eagle",
        "sci": "Spizaetus tyrannus",
        "color": "#4fb6ff",
    },
    "bawhae1": {
        "pt": "Gavião-pato",
        "en": "Black-and-white Hawk-Eagle",
        "sci": "Spizaetus melanoleucus",
        "color": "#b388ff",
    },
}

DEFAULT_SPECIES = "hareag1"
DEFAULT_NAME_MODE = "pt"  # pt | en | sci

# Colors handed to species added without an explicit "color", so the app
# never breaks if one is forgotten.
FALLBACK_PALETTE = [
    "#00e08a", "#ffcc33", "#ff6b4a", "#4fb6ff",
    "#f2f2f2", "#b388ff", "#ff8fab", "#7cffc4",
]


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def _mix(rgb_a, rgb_b, t):
    return tuple(rgb_a[i] + (rgb_b[i] - rgb_a[i]) * t for i in range(3))


def build_species_styles(species_dict):
    """Derives marker + heatmap colors for every species from a single
    base color, so adding a species only means picking one hex value."""
    white = (255, 255, 255)
    black = (0, 0, 0)
    styles = {}

    for i, (code, info) in enumerate(species_dict.items()):
        base_hex = info.get("color") or FALLBACK_PALETTE[i % len(FALLBACK_PALETTE)]
        base = _hex_to_rgb(base_hex)

        # Low density fades toward black so it blends into the dark satellite
        # basemap; high density glows toward white so hotspots actually pop,
        # instead of the reverse (which made "hot" areas look muddy/dark).
        styles[code] = {
            "marker": base_hex,
            "heat": {
                "0.2": _rgb_to_hex(_mix(black, base, 0.35)),
                "0.4": _rgb_to_hex(_mix(black, base, 0.7)),
                "0.6": _rgb_to_hex(base),
                "0.8": _rgb_to_hex(_mix(base, white, 0.45)),
                "1.0": _rgb_to_hex(_mix(base, white, 0.85)),
            },
        }

    return styles


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

    # 🔹 Format every row for display — done once, up front, so both the
    # per-species table and the "all species" map view can use the same
    # enriched data.
    for obs in csv_observations:
        obs_species = SPECIES.get(obs["species"], {})
        obs["displayName"] = obs_species.get(name_mode, obs["species"])
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

    # 🔹 Selected species only, newest first
    observations = [
        o for o in csv_observations
        if o["species"] == species_code
    ]
    observations.sort(
        key=lambda o: o.get("obsDt", ""),
        reverse=True,
    )

    # 🔹 Totals (CSV-based)
    totals_by_species = {
        code: sum(1 for o in csv_observations if o["species"] == code)
        for code in SPECIES.keys()
    }
    total_all = sum(totals_by_species.values())

    species_styles = build_species_styles(SPECIES)

    return render_template(
        "index.html",
        species=species_code,
        species_name=SPECIES[species_code],
        species_list=SPECIES,
        observations=observations,
        all_observations=csv_observations,
        name_mode=name_mode,
        totals_by_species=totals_by_species,
        total_all=total_all,
        last_updated=last_updated_display,
        SPECIES=SPECIES,
        species_styles=species_styles,
    )


# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)