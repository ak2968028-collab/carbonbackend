from django.db import models


class Overview(models.Model):
    vlcode = models.IntegerField(unique=True, primary_key=True)
    village_name = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    total_population = models.FloatField(blank=True, null=True)
    total_area_ha = models.FloatField(blank=True, null=True)
    builtup_area_ha = models.FloatField(blank=True, null=True)
    agricultural_area_ha = models.FloatField(blank=True, null=True)
    water_bodies_area_ha = models.FloatField(blank=True, null=True)
    total_households = models.FloatField(blank=True, null=True)
    total_livestock = models.FloatField(blank=True, null=True)
    total_vehicles = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "overview"

    def __str__(self):
        return f"{self.vlcode} - {self.village_name}"


class Emissions(models.Model):
    vlcode = models.IntegerField(unique=True, primary_key=True)
    agriculture_rice_kharif = models.FloatField(blank=True, null=True)
    agriculture_wheat_rabi = models.FloatField(blank=True, null=True)
    energy_electricity = models.FloatField(blank=True, null=True)
    residential_firewood = models.FloatField(blank=True, null=True)
    residential_lpg = models.FloatField(blank=True, null=True)
    transport_petrol_vehicles = models.FloatField(blank=True, null=True)
    waste_solid_waste = models.FloatField(blank=True, null=True)
    livestock_enteric_fermentation = models.FloatField(blank=True, null=True)
    waste_solid_waste_2 = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "emissions"

    def __str__(self):
        return f"Emissions vlcode={self.vlcode}"


class Sequestration(models.Model):
    vlcode = models.IntegerField(unique=True, primary_key=True)
    before_total_sequestration = models.FloatField(blank=True, null=True)
    after_total_sequestration_increase = models.FloatField(blank=True, null=True)
    before_forest = models.FloatField(blank=True, null=True)
    after_plantation = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "sequestration"

    def __str__(self):
        return f"Sequestration vlcode={self.vlcode}"


class Interventions(models.Model):
    vlcode = models.IntegerField(unique=True, primary_key=True)
    cooking_lpg_efficiency_10pct = models.FloatField(blank=True, null=True)
    energy_solar_rooftop_500m = models.FloatField(blank=True, null=True)
    transport_ev_adoption_20pct = models.FloatField(blank=True, null=True)
    composting_pit_20pct = models.FloatField(blank=True, null=True)
    biomass_improved_cookstove_10pct = models.FloatField(blank=True, null=True)
    agriculture_rice_methane_reduction_15pct = models.FloatField(blank=True, null=True)
    solid_waste_solid = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "interventions"

    def __str__(self):
        return f"Interventions vlcode={self.vlcode}"


class CarbonBudget(models.Model):
    vlcode = models.IntegerField(unique=True, primary_key=True)
    before_net_emission = models.FloatField(blank=True, null=True)
    before_net_monthly_emission = models.FloatField(blank=True, null=True)
    before_per_capita_emission = models.FloatField(blank=True, null=True)
    before_total_emission = models.FloatField(blank=True, null=True)
    after_new_net_emission = models.FloatField(blank=True, null=True)
    after_previous_net_emission = models.FloatField(blank=True, null=True)
    after_total_emission_reduction = models.FloatField(blank=True, null=True)
    after_total_impact_reduction_plus_sequestration = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "carbon_budget"

    def __str__(self):
        return f"CarbonBudget vlcode={self.vlcode}"


class Scenarios(models.Model):
    vlcode = models.IntegerField(unique=True, primary_key=True)
    bau_2023 = models.FloatField(blank=True, null=True)
    bau_2025 = models.FloatField(blank=True, null=True)
    bau_2030 = models.FloatField(blank=True, null=True)
    bau_2035 = models.FloatField(blank=True, null=True)
    los_2023 = models.FloatField(blank=True, null=True)
    los_2025 = models.FloatField(blank=True, null=True)
    los_2030 = models.FloatField(blank=True, null=True)
    los_2035 = models.FloatField(blank=True, null=True)
    acc_2023 = models.FloatField(blank=True, null=True)
    acc_2025 = models.FloatField(blank=True, null=True)
    acc_2030 = models.FloatField(blank=True, null=True)
    acc_2035 = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "scenarios"

    def __str__(self):
        return f"Scenarios vlcode={self.vlcode}"
