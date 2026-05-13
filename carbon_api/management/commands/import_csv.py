"""
Management command: python manage.py import_csv
Reads master_template.csv, splits into 6 topic CSVs, saves them,
then imports each into its respective SQLite table.
"""
import csv
import os
from pathlib import Path

from django.core.management.base import BaseCommand

from carbon_api.models import (
    CarbonBudget,
    Emissions,
    Interventions,
    Overview,
    Scenarios,
    Sequestration,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MASTER_CSV = BASE_DIR / "master_template.csv"
CSV_OUT_DIR = BASE_DIR / "split_csvs"


def safe_float(val):
    try:
        v = str(val).strip()
        return float(v) if v not in ("", "None", "nan") else None
    except (ValueError, TypeError):
        return None


COLUMN_MAPS = {
    "overview": [
        "vlcode",
        "village_name",
        "district",
        "state",
        "total_population",
        "total_area_ha",
        "builtup_area_ha",
        "agricultural_area_ha",
        "water_bodies_area_ha",
        "total_households",
        "total_livestock",
        "total_vehicles",
    ],
    "emissions": [
        "vlcode",
        "Agriculture_Rice (Kharif)",
        "Agriculture_Wheat (Rabi)",
        "Energy_Electricity",
        "Residential_Firewood",
        "Residential_LPG",
        "Transport_Petrol Vehicles",
        "waste_solid_waste",
        "Livestock_Enteric Fermentation",
        "Waste_Solid Waste",
    ],
    "sequestration": [
        "vlcode",
        "before_total_sequestration",
        "after_total_sequestration_increase",
        "before_forest",
        "after_plantation",
    ],
    "interventions": [
        "vlcode",
        "Cooking_LPG_Efficiency_(10%)",
        "Energy_Solar_Rooftop_(500_M",
        "Transport_EV_Adoption_(20%)",
        "composting/pit_(20%)",
        "biomass_improved_cookstove_(10%)",
        "agriculture_rice_methane_reduction_(15%)",
        "solid_waste_solid",
    ],
    "carbon_budget": [
        "vlcode",
        "before_net_emission",
        "before_net_monthly_emission",
        "before_per_capita_emission",
        "before_total_emission",
        "after_new_net_emission",
        "after_previous_net_emission",
        "after_total_emission_reduction",
        "after_total_impact_reduction_+_sequestration",
    ],
    "scenarios": [
        "vlcode",
        "BAU_2023",
        "BAU_2025",
        "BAU_2030",
        "BAU_2035",
        "LOS_2023",
        "LOS_2025",
        "LOS_2030",
        "LOS_2035",
        "ACC_2023",
        "ACC_2025",
        "ACC_2030",
        "ACC_2035",
    ],
}

# Maps CSV column name -> model field name for non-trivial mappings
FIELD_NAME_MAP = {
    "Agriculture_Rice (Kharif)": "agriculture_rice_kharif",
    "Agriculture_Wheat (Rabi)": "agriculture_wheat_rabi",
    "Energy_Electricity": "energy_electricity",
    "Residential_Firewood": "residential_firewood",
    "Residential_LPG": "residential_lpg",
    "Transport_Petrol Vehicles": "transport_petrol_vehicles",
    "waste_solid_waste": "waste_solid_waste",
    "Livestock_Enteric Fermentation": "livestock_enteric_fermentation",
    "Waste_Solid Waste": "waste_solid_waste_2",
    "Cooking_LPG_Efficiency_(10%)": "cooking_lpg_efficiency_10pct",
    "Energy_Solar_Rooftop_(500_M": "energy_solar_rooftop_500m",
    "Transport_EV_Adoption_(20%)": "transport_ev_adoption_20pct",
    "composting/pit_(20%)": "composting_pit_20pct",
    "biomass_improved_cookstove_(10%)": "biomass_improved_cookstove_10pct",
    "agriculture_rice_methane_reduction_(15%)": "agriculture_rice_methane_reduction_15pct",
    "solid_waste_solid": "solid_waste_solid",
    "after_total_impact_reduction_+_sequestration": "after_total_impact_reduction_plus_sequestration",
    "BAU_2023": "bau_2023",
    "BAU_2025": "bau_2025",
    "BAU_2030": "bau_2030",
    "BAU_2035": "bau_2035",
    "LOS_2023": "los_2023",
    "LOS_2025": "los_2025",
    "LOS_2030": "los_2030",
    "LOS_2035": "los_2035",
    "ACC_2023": "acc_2023",
    "ACC_2025": "acc_2025",
    "ACC_2030": "acc_2030",
    "ACC_2035": "acc_2035",
}

MODEL_MAP = {
    "overview": Overview,
    "emissions": Emissions,
    "sequestration": Sequestration,
    "interventions": Interventions,
    "carbon_budget": CarbonBudget,
    "scenarios": Scenarios,
}

STRING_FIELDS = {"overview": {"village_name", "district", "state"}}


class Command(BaseCommand):
    help = "Split master_template.csv into 6 topic CSVs and import into SQLite"

    def handle(self, *args, **options):
        CSV_OUT_DIR.mkdir(exist_ok=True)

        with open(MASTER_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.stdout.write(f"Read {len(rows)} rows from master_template.csv")

        # Write split CSVs
        split_data = {}
        for topic, cols in COLUMN_MAPS.items():
            available = [c for c in cols if c in rows[0]] if rows else cols
            split_rows = [{c: row.get(c, "") for c in available} for row in rows]
            split_data[topic] = split_rows
            out_path = CSV_OUT_DIR / f"{topic}.csv"
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=available)
                writer.writeheader()
                writer.writerows(split_rows)
            self.stdout.write(f"  Wrote {out_path.name} ({len(split_rows)} rows, {len(available)} cols)")

        # Import into DB
        for topic, csv_rows in split_data.items():
            Model = MODEL_MAP[topic]
            string_fields = STRING_FIELDS.get(topic, set())
            created = updated = 0
            for row in csv_rows:
                vlcode_raw = row.get("vlcode", "").strip()
                if not vlcode_raw:
                    continue
                try:
                    vlcode = int(float(vlcode_raw))
                except ValueError:
                    continue

                kwargs = {"vlcode": vlcode}
                for csv_col, val in row.items():
                    if csv_col == "vlcode":
                        continue
                    field = FIELD_NAME_MAP.get(csv_col, csv_col)
                    if field in string_fields:
                        kwargs[field] = str(val).strip() or None
                    else:
                        kwargs[field] = safe_float(val)

                obj, is_new = Model.objects.update_or_create(
                    vlcode=vlcode, defaults={k: v for k, v in kwargs.items() if k != "vlcode"}
                )
                if is_new:
                    created += 1
                else:
                    updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"  {topic}: {created} created, {updated} updated"
                )
            )

        self.stdout.write(self.style.SUCCESS("Import complete."))
