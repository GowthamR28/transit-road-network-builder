import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
from shapely.geometry import Point
import folium

# =========================
# Step 1. Load bus stops
# =========================
stops = pd.read_csv("stops.csv")  # CSV must have Stop lat, Stop lon
stops_gdf = gpd.GeoDataFrame(
    stops,
    geometry=gpd.points_from_xy(stops["Stop lon"], stops["Stop lat"]),
    crs="EPSG:4326"
)

# =========================
# Step 2. Main roads network
# =========================
main_roads = '["highway"~"motorway|trunk|primary|secondary|tertiary"]'
convex = stops_gdf.union_all().convex_hull.buffer(0.02)  # ~2 km buffer
G_main = ox.graph_from_polygon(convex, network_type="drive", custom_filter=main_roads)

# =========================
# Step 3. Snap stops to main roads
# =========================
xs, ys = stops_gdf.geometry.x.values, stops_gdf.geometry.y.values
stops_gdf["nearest_node"] = ox.distance.nearest_nodes(G_main, X=xs, Y=ys)

# Calculate distances
distances = []
for idx, row in stops_gdf.iterrows():
    node = row["nearest_node"]
    dist = ox.distance.great_circle(
        row.geometry.y, row.geometry.x,
        G_main.nodes[node]["y"], G_main.nodes[node]["x"]
    )
    distances.append(dist)
stops_gdf["snap_dist_m"] = distances

# =========================
# Step 4. Identify far stops
# =========================
far_stops = stops_gdf[stops_gdf["snap_dist_m"] > 200]  # threshold in meters
print(f"Far stops: {len(far_stops)}")

# =========================
# Step 5. Add local roads around far stops
# =========================
if len(far_stops) > 0:
    convex_far = far_stops.union_all().convex_hull.buffer(0.06)  # ~5 km buffer
    local_roads = '["highway"~"residential|unclassified|service|living_street|track|path"]'
    G_local = ox.graph_from_polygon(convex_far, network_type="drive", custom_filter=local_roads)
    G_main = nx.compose(G_main, G_local)
    print("Local roads merged into main graph.")

# =========================
# Step 6. Re-snap all stops
# =========================
stops_gdf["nearest_node"] = ox.distance.nearest_nodes(G_main, X=xs, Y=ys)
distances = []
for idx, row in stops_gdf.iterrows():
    node = row["nearest_node"]
    dist = ox.distance.great_circle(
        row.geometry.y, row.geometry.x,
        G_main.nodes[node]["y"], G_main.nodes[node]["x"]
    )
    distances.append(dist)
stops_gdf["snap_dist_m"] = distances
print("Final max snap distance:", stops_gdf["snap_dist_m"].max())

# =========================
# Step 7. Export interactive folium map
# =========================
nodes, edges = ox.graph_to_gdfs(G_main)

m = folium.Map(location=[stops_gdf.geometry.y.mean(), stops_gdf.geometry.x.mean()],
               zoom_start=12)

# Add road edges
for _, row in edges.iterrows():
    coords = [(y, x) for x, y in row.geometry.coords]
    folium.PolyLine(coords, color="blue", weight=1, opacity=0.6).add_to(m)

# Add stops (color-coded by snap distance)
for _, row in stops_gdf.iterrows():
    color = "green" if row["snap_dist_m"] <= 200 else "red"
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=3, color=color, fill=True, fill_opacity=0.8,
        popup=f"{row['Stop Name']} ({row['snap_dist_m']} m)"
    ).add_to(m)

m.save("network_with_stops.html")
print("✅ Map saved as network_with_stops.html")


# =========================
# Step 7.1. Clean stops columns for shapefile export
# =========================
stops_clean = stops_gdf.rename(columns={
    "Stop Name": "stop_name",      # shapefile field names must be <= 10 chars
    "nearest_node": "near_node",
    "snap_dist_m": "snap_dist"
})

# =========================
# Step 8. Export shapefiles for transport modeling
# =========================
import os
os.makedirs("outputs", exist_ok=True)

# Shapefile exports (creates .shp, .shx, .dbf, .prj, etc.)
nodes.to_file("outputs/nodes.shp", driver="ESRI Shapefile")
edges.to_file("outputs/links.shp", driver="ESRI Shapefile")
stops_clean.to_file("outputs/stops.shp", driver="ESRI Shapefile")

print("✅ Shapefiles exported to /outputs (nodes, links, stops).")

# Extra: GeoPackage export (no truncation, modern format)
edges.to_file("outputs/network.gpkg", layer="links", driver="GPKG")
nodes.to_file("outputs/network.gpkg", layer="nodes", driver="GPKG")
stops_clean.to_file("outputs/network.gpkg", layer="stops", driver="GPKG")

print("✅ GeoPackage exported to /outputs/network.gpkg (links, nodes, stops).")
