import json
from datetime import datetime

import numpy as np
import requests
from scipy.spatial import Voronoi

json_fn = "./geojson.json"


def segment_to_geojson(segment):
    """(lng, lat)
    """
    p1 = segment[0]
    p2 = segment[1]
    return {
        "type": "Feature",
        "properties": {},
        "geometry": {"type": "LineString", "coordinates": [[p1[0], p1[1]], [p2[0], p2[1]]]},
    }


def point_to_geojson(point):
    """(lng, lat)
    """
    return {
        "type": "Feature",
        "properties": {},
        "geometry": {"type": "Point", "coordinates": [point[0], point[1]]},
    }


def vor_plot(finite_segments, infinite_segments, points):
    geojson = {"type": "FeatureCollection", "features": []}

    for p in points:
        geojson["features"].append(point_to_geojson(p))
    for seg in finite_segments:
        geojson["features"].append(segment_to_geojson(seg))
    for seg in infinite_segments:
        geojson["features"].append(segment_to_geojson(seg))

    json.dump(geojson, open(json_fn, "w"), ensure_ascii=False)


def get_elemets_for_plot(vor):
    center = vor.points.mean(axis=0)
    ptp_bound = vor.points.ptp(axis=0)

    ptp_bound_max = ptp_bound.max()

    finite_segments = []
    infinite_segments = []

    for pointidx, simplex in zip(vor.ridge_points, vor.ridge_vertices):
        simplex = np.asarray(simplex)
        if np.all(simplex >= 0):
            finite_segments.append(vor.vertices[simplex])
            continue

        # finite end Voronoi vertex
        i = simplex[simplex >= 0][0]

        # tangent
        t = vor.points[pointidx[1]] - vor.points[pointidx[0]]
        t /= np.linalg.norm(t)

        n = np.array([-t[1], t[0]])

        midpoint = vor.points[pointidx].mean(axis=0)
        direction = n
        if np.dot(midpoint - center, n) < 0:
            direction = -n

        far_point = vor.vertices[i] + direction * ptp_bound_max

        infinite_segments.append([vor.vertices[i], far_point])

    return finite_segments, infinite_segments, vor.points


ts = int(datetime.now().timestamp() * 1000)

url = "http://map.amap.com/service/subway?_{}&srhdata=1100_drw_beijing.json".format(ts)

data = requests.get(url).json()

stations = dict()
for line in data["l"]:
    line_name = line["ln"]

    line_station = []
    for station in line["st"]:
        station_name = station["n"]
        station_coord_str_list = station["sl"].strip().split(",")
        station_coord = (float(station_coord_str_list[0]), float(station_coord_str_list[1]))
        stations[station_name] = station_coord

vor = Voronoi(list(stations.values()))

result = get_elemets_for_plot(vor)
vor_plot(*result)
