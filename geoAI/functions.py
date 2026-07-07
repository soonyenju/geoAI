import numpy as np
import pandas as pd
import geopandas as gpd
from matplotlib import pyplot as plt
from shapely.ops import nearest_points
from shapely.geometry import LineString, Point


def show_city_boundary(shp, country, buffer = 0.1, fc = '#ff7f0e'):
    shp.plot()
    ax = plt.gca()
    country.plot(ax = ax, fc = '#1f77b4', alpha = 0.2)
    ax.set_xlim(shp.bounds.minx.item() - buffer, shp.bounds.maxx.item() + buffer)
    ax.set_ylim(shp.bounds.miny.item() - buffer, shp.bounds.maxy.item() + buffer)
    return ax
    

def midpoint_and_perpendicular(line):
    # 1. Get midpoint
    midpoint = line.interpolate(0.5, normalized=True)

    # 2. Get direction vector (dx, dy)
    x0, y0 = line.coords[0]
    x1, y1 = line.coords[-1]
    dx, dy = x1 - x0, y1 - y0

    # 3. Get perpendicular vector (-dy, dx) and normalize
    perp_dx, perp_dy = -dy, dx
    length = np.hypot(perp_dx, perp_dy)
    unit_dx, unit_dy = perp_dx / length, perp_dy / length

    # 4. Define length of perpendicular line (adjust as needed)
    perp_length = line.length / 2  # units (meters, degrees, etc. depending on CRS)

    # 5. Create endpoints of perpendicular line centered at midpoint
    x_mid, y_mid = midpoint.x, midpoint.y
    point1 = Point(x_mid + unit_dx * perp_length / 2, y_mid + unit_dy * perp_length / 2)
    point2 = Point(x_mid - unit_dx * perp_length / 2, y_mid - unit_dy * perp_length / 2)

    perp_line = LineString([point1, point2])

    # 6. Wrap in GeoDataFrames for plotting
    line_gdf = gpd.GeoDataFrame(geometry=[line])
    perp_gdf = gpd.GeoDataFrame(geometry=[perp_line])
    midpoint_gdf = gpd.GeoDataFrame(geometry=[midpoint])

    # # 7. Plot
    # ax = line_gdf.plot(color='blue', linewidth=2)
    # perp_gdf.plot(ax=ax, color='red', linewidth=2, linestyle='--')
    # midpoint_gdf.plot(ax=ax, color='black', markersize=50)

    return midpoint_gdf, perp_gdf 


def closest_point2line(point, curves):
    # 1. Find the closest curves
    closest_line = curves.loc[curves.distance(point).idxmin()]
    closest_geom = closest_line.geometry

    # 2. Get nearest point *on* the curves to Exeter
    nearest_on_line, _ = nearest_points(closest_geom, point)

    # 3. Create direct connecting LineString
    direct_line = LineString([point, nearest_on_line])

    # 4. Wrap into GeoDataFrames for plotting
    closest_line_gdf = gpd.GeoDataFrame(geometry=[closest_geom], index = ['closest'], crs=curves.crs)
    # exeter_gdf = gpd.GeoDataFrame(geometry=[point], crs=curves.crs)
    direct_line_gdf = gpd.GeoDataFrame(geometry=[direct_line], index = ['direct'], crs=curves.crs)

    return pd.concat([closest_line_gdf, direct_line_gdf], axis = 0)



from geoxai.geo.meteo import saturation_vapor_pressure, specific_humidity2vapor_pressure
from geoxai.utils import *
from geoxai.geo.geoface import load_tif

def load_era5(p_ERA5):
    era5 = load_tif(p_ERA5, band_names = [
        'dewpoint_temperature_2m', 'temperature_2m', 'soil_temperature_level_1', 'snow_cover',
        'volumetric_soil_water_layer_1', 'forecast_albedo', 'surface_latent_heat_flux_sum', 'surface_sensible_heat_flux_sum',
        'surface_solar_radiation_downwards_sum', 'surface_thermal_radiation_downwards_sum',
        'surface_net_solar_radiation_sum', 'surface_net_thermal_radiation_sum',
        'evaporation_from_the_top_of_canopy_sum', 'surface_pressure', 'total_precipitation_sum',
        'temperature_2m_min', 'temperature_2m_max', 'u_component_of_wind_10m', 'v_component_of_wind_10m',
    ])
    era5 = era5.where(era5 != 0)
    data_vars = era5.data_vars
    for v in ['dewpoint_temperature_2m', 'temperature_2m', 'soil_temperature_level_1', 'temperature_2m_min', 'temperature_2m_max']:
        if v in data_vars:
            era5[v] -= 273.15
    for v in [
        'surface_latent_heat_flux_sum', 'surface_sensible_heat_flux_sum', 'surface_solar_radiation_downwards_sum',
        'surface_thermal_radiation_downwards_sum', 'surface_net_solar_radiation_sum', 'surface_net_thermal_radiation_sum'
        ]:
        if v in data_vars:
            era5[v] /= 86400

    if 'surface_pressure' in data_vars:
        era5['surface_pressure'] /= 100

    era5['VPD'] = saturation_vapor_pressure(era5['temperature_2m']) - saturation_vapor_pressure(era5['dewpoint_temperature_2m'])
    if ('surface_net_solar_radiation_sum' in data_vars) and ('surface_net_thermal_radiation_sum' in data_vars):
        era5['surface_net_radiation_sum'] = era5['surface_net_solar_radiation_sum'] + era5['surface_net_thermal_radiation_sum']
        era5 = era5.drop_vars(['surface_net_solar_radiation_sum', 'surface_net_thermal_radiation_sum'])
    era5 = era5.drop_vars('dewpoint_temperature_2m')
    # era5 = era5.drop_vars('spatial_ref')
    era5 = era5.drop_vars([
        'forecast_albedo', 'surface_latent_heat_flux_sum', 'surface_sensible_heat_flux_sum',
        'evaporation_from_the_top_of_canopy_sum', 'temperature_2m_min', 'temperature_2m_max',
        'u_component_of_wind_10m', 'v_component_of_wind_10m', 'snow_cover'
    ])
    return era5