import xml.etree.ElementTree as ET

import numpy as np
from skimage.draw import polygon


def osm_to_grid(file_path):
    # Load OSM file
    with open(file_path, "r", encoding="utf-8") as f:
        osm_data = f.read()

    # Parse XML
    root = ET.fromstring(osm_data)

    # Get map bounds
    bounds = root.find("bounds")
    minlat = float(bounds.attrib["minlat"])
    minlon = float(bounds.attrib["minlon"])
    maxlat = float(bounds.attrib["maxlat"])
    maxlon = float(bounds.attrib["maxlon"])

    # Grid size
    grid_width, grid_height = 100, 100
    grid = np.zeros(
        (grid_height, grid_width), dtype=np.uint8
    )  # all free space initially

    # Convert lat/lon to pixel coordinates
    def latlon_to_pixel(lat, lon):
        x = int((lon - minlon) / (maxlon - minlon) * (grid_width - 1))
        y = int(
            (1 - (lat - minlat) / (maxlat - minlat)) * (grid_height - 1)
        )  # flip y axis
        return x, y

    # Store nodes in a dictionary: node_id -> (lat, lon)
    nodes = {}
    for node in root.findall("node"):
        node_id = node.attrib["id"]
        lat = float(node.attrib["lat"])
        lon = float(node.attrib["lon"])
        nodes[node_id] = (lat, lon)

    def draw_polygon_on_grid(way, value):
        node_ids = [nd.attrib["ref"] for nd in way.findall("nd")]
        poly_x = []
        poly_y = []
        for nid in node_ids:
            if nid in nodes:
                lat, lon = nodes[nid]
                x, y = latlon_to_pixel(lat, lon)
                poly_x.append(x)
                poly_y.append(y)
        if len(poly_x) > 2:
            rr, cc = polygon(poly_y, poly_x, grid.shape)
            grid[rr, cc] = value

    # Draw buildings (1)
    for way in root.findall("way"):
        tags = {tag.attrib["k"]: tag.attrib["v"] for tag in way.findall("tag")}
        if "building" in tags:
            draw_polygon_on_grid(way, value=1)

    # Draw parks/green spaces (2)
    for way in root.findall("way"):
        tags = {tag.attrib["k"]: tag.attrib["v"] for tag in way.findall("tag")}
        if tags.get("leisure") == "park" or tags.get("landuse") in [
            "grass",
            "forest",
            "meadow",
            "recreation_ground",
        ]:
            draw_polygon_on_grid(way, value=3)

    return grid
