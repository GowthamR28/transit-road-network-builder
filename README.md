
# Transit Road Network Builder 🚍

Builds a **road network for transit modelling** (Cube, Visum, AequilibraE, etc.) from **bus stop lat–longs** using OpenStreetMap.  
It downloads arterials first, then pulls local streets **only where stops are far**, snaps stops to the network, and exports an **interactive Folium map**.

---

## ✨ What it does
- Downloads arterial roads: `motorway|trunk|primary|secondary|tertiary`
- Detects stops far from arterials and fetches **local roads** around them
- Snaps each stop to the **nearest node** and computes **snap distance (m)**
- Exports an interactive map to review coverage

---

## 📸 Example Output
**Interactive map preview (screenshot):**

![Transit Network Example](docs/images/output_2.png)
![Transit Network Example](docs/images/output_2.png)


---

## ⚙️ Install
```bash
pip install -r requirements.txt

Tested with:
osmnx==2.0.5,geopandas, pandas, shapely, networkx, folium


## ▶️ Run
By default the script reads stops.csv in the project root.


## Output:
network_with_stops.html — interactive map (open in a browser)


## 🧾 Input format
CSV with these columns:

Stop_ID,Stop_Name,Stop lat,Stop lon
1,Sample Stop,12.9716,77.5946


Stop_ID,Stop_Name,Stop lat,Stop lon
1,Sample Stop,12.9716,77.5946
=======
