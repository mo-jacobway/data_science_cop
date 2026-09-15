"""ClimateZones Data Exploration - Environment Validation Test

This script's workflow content originated from the ClimateZones Data Exploration
tutorial notebook and was reduced to provide a representative environment-
validation workflow.

The workflow content below remains substantially derived from that reduced
workflow and is executed within the environment-validation framework.

Test framework functionality including validation reporting, exception handling,
provenance capture and artefact retention is provided separately by
test_framework_utils.py.

* Author: Stephen Haddad and Kate Brown; Environment-validation test wrapper and workflow reduction: Jacob Way;
* Affiliation: UK Met Office
* History: 1.0
* Last update: 2026-09-15
* (c) British Crown Copyright 2017-2026, Met Office. Please see LICENSE.md for license details.

Running this test
-----------------
This script forms part of an environment-validation framework and contains
the workflow-specific implementation of the ClimateZones Data Exploration
validation test.

It is intended to be executed via:

    run_test.sh --test climatezones_data_exploration [--module <module>] [--retention] [--log-level <level>]

which loads the environment under test and invokes this workflow through
the framework.

Data statement
--------------
This script is an environment-validation implementation based on the original
ClimateZones Data Exploration tutorial workflow.

The underlying data referenced by the workflow is the Koppen-Geiger Climate
Classification dataset created by GloH2O.

References
----------
- Climate Zones Dataset:
  https://www.gloh2o.org/koppen/#:~:text=The%20K%C3%B6ppen%2DGeiger%20climate%20classification%20maps%20are%20high%2Dresolution,Climate%20Sensitivity%20(ECS)%2C%20and%20historical%20warming%20trend
"""

import pathlib
import os
import json

import matplotlib.pyplot
import cartopy.crs

import xarray
import pandas

import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
import test_framework_utils as test_framework

# ---------------------------------------------------------------------
# Notebook workflow helpers
# ---------------------------------------------------------------------

def get_platform_dir(select_platform, config):
    """Resolve the ClimateZones data location for the selected execution platform."""
    try:
        root_path = pathlib.Path(config['default_dirs'][select_platform]) / 'climate_zones'
    except KeyError:
        root_path = pathlib.Path(os.environ['HOME']) / 'climate_zones'
    return root_path

def get_data_path(root_dir, time_period, scenario_id, prefix, resolution_str, suffix, config):
    """
    Construct a ClimateZones dataset path for the validation workflow.

    Derived from the original tutorial notebook. The notebook implementation
    accepted root_dir and suffix arguments but relied on enclosing-scope values
    instead. This implementation uses the explicit arguments directly while
    preserving the resulting workflow paths.
    """
    time_dir_template = config['time_dir_template']
    fname_template = config['fname_template']

    start_year = time_period[0]
    end_year = time_period[1]
    if scenario_id == 'historic':
        data_dir = root_dir / time_dir_template.format(start_year=start_year, end_year=end_year)
    else:
        data_dir = root_dir / time_dir_template.format(start_year=start_year, end_year=end_year) / scenario_id
    data_fname = fname_template.format(prefix=prefix,
                                        res=resolution_str,
                                        suffix=suffix)
    return data_dir / data_fname

def create_climate_zone_diff_plot(historic_climate_zone_ds, future_climate_zone_ds, select_historic, select_future):
    """Generate the climate-zone change map used by the validation workflow."""
    fig1 = matplotlib.pyplot.figure(figsize=(16, 8))

    ax1 = fig1.add_subplot(1, 1, 1, projection=cartopy.crs.PlateCarree(),)
    diff_arr = (future_climate_zone_ds["kg_class"]!=historic_climate_zone_ds["kg_class"])
    diff_arr.plot.contourf(ax=ax1, transform=cartopy.crs.PlateCarree(), cbar_kwargs={"location": "bottom"},)

    ax1.coastlines()
    ax1.set_title(f"KG Climate Zones diff {select_future} compared to {select_historic}")

    fig1.canvas.draw()
    return fig1

def create_january_temperature_plot(historic_climate_mean_ds,):
    """Generate the January air-temperature map used by the validation workflow."""
    january_air_temperature = (historic_climate_mean_ds.loc[{"time": 1}]["air_temperature"])
    fig1 = matplotlib.pyplot.figure(figsize=(10, 5))

    ax1 = fig1.add_subplot(1, 1, 1,projection=cartopy.crs.PlateCarree(),)
    january_air_temperature.plot.contourf(ax=ax1,transform=cartopy.crs.PlateCarree(),)

    ax1.coastlines()
    ax1.set_title("January Air Temperature")

    fig1.canvas.draw()
    return fig1

def create_climate_subgroup_bar_plot(zones_df,):
    """Generate a climate-subgroup distribution plot from the workflow dataset."""
    bar_fig = matplotlib.pyplot.figure(figsize=(8, 5))
    zones_df['climate_subgroup'].value_counts().plot.bar()

    bar_fig.canvas.draw()
    return bar_fig

def create_zone_a_temp_histogram(zones_df,):
    """Generate the Zone A January-temperature histogram."""
    fig1 = matplotlib.pyplot.figure(figsize=(8, 5))
    ax1 = fig1.add_subplot(1, 1, 1, title="distribution of January Air Temperature - Zone A")
    zones_df[zones_df["climate_group"] == "A"]["air_temperature_1.0_mean"].hist()
    ax1.set_xlim(-30, 40)

    fig1.canvas.draw()
    return fig1

# ---------------------------------------------------------------------
# Notebook derived workflow
# ---------------------------------------------------------------------

def run_notebook_derived_workflow():
        CONFIG_PATH = (test_framework.DATA_SCIENCE_COP_ROOT/"ml_examples"/"climate_zones"/"config.json")

        with open(CONFIG_PATH, "r") as tutorial_config_file:
            tutorial_config = json.load(tutorial_config_file)

        # Config retrievals
        resolutions_dict = {float(k1): v1 for k1, v1 in tutorial_config['resolutions_names'].items()}
        dataset_prefix_dict = tutorial_config['dataset_prefix']
        ml_ready_fname_template = tutorial_config['csv_out_template']
        current_platform = tutorial_config['platform']

        # Data locations
        root_data_dir = get_platform_dir(current_platform, tutorial_config)
        ml_ready_dir = root_data_dir / 'ml_ready'

        # Workflow parameters
        format_str = 'nc'
        current_res = 1.0
        select_historic = (1901, 1930)
        select_future = (2071, 2099)
        select_future_scenario = "ssp370"

        historic_climate_zone_path = get_data_path(root_dir=root_data_dir, time_period=select_historic, scenario_id='historic', prefix=dataset_prefix_dict["climate_zone"],
                                                   resolution_str=resolutions_dict[current_res], suffix=format_str, config=tutorial_config,)

        future_climate_zone_path = get_data_path(root_dir=root_data_dir, time_period=select_future, scenario_id=select_future_scenario, prefix=dataset_prefix_dict["climate_zone"],
                                                 resolution_str=resolutions_dict[current_res], suffix=format_str, config=tutorial_config,)

        historic_climate_mean_path = get_data_path(root_dir=root_data_dir, time_period=select_historic, scenario_id='historic', prefix=dataset_prefix_dict["climate_mean"],
                                                   resolution_str=resolutions_dict[current_res], suffix=format_str, config=tutorial_config,)

        historic_climate_zone_ds = xarray.open_dataset(historic_climate_zone_path)
        future_climate_zone_ds = xarray.open_dataset(future_climate_zone_path)
        historic_climate_mean_ds = xarray.open_dataset(historic_climate_mean_path)

        fig1 = create_climate_zone_diff_plot(historic_climate_zone_ds, future_climate_zone_ds, select_historic, select_future)
        test_framework.handle_figure_retention(fig1, "01_climate_zone_diff_map.png")

        fig2 = create_january_temperature_plot(historic_climate_mean_ds,)
        test_framework.handle_figure_retention(fig2, "02_january_air_temperature_map.png")

        mlready_data_path = ml_ready_dir / ml_ready_fname_template.format(resolution=resolutions_dict[current_res])
        zones_df = pandas.read_csv(mlready_data_path, nrows=25000)

        fig3 = create_climate_subgroup_bar_plot(zones_df)
        test_framework.handle_figure_retention(fig3, "03_climate_subgroup_bar.png")

        fig4 = create_zone_a_temp_histogram(zones_df,)
        test_framework.handle_figure_retention(fig4, "04_zone_a_january_temp_hist.png")

if __name__ == "__main__":
    sys.exit(test_framework.execute_workflow(run_notebook_derived_workflow))
