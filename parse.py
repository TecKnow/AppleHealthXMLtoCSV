import gpxpy
import geopy.distance
from pathlib import Path
from typing import Final
from csv import DictWriter
from time import perf_counter_ns

DEFAULT_DATA_DIRECTORY: Final = "./apple_health_export"
DATA_PATH: Final = Path(DEFAULT_DATA_DIRECTORY).joinpath("workout-routes")
distance_units = "meters"
OUTPUT_FILENAME: Final = "routes_data.csv"
if not hasattr(geopy.distance.distance, distance_units):
    raise ValueError(f"Unknown distance units: {distance_units}")


def point_gpx_to_geopy(gpx_point: gpxpy.gpx.GPXTrackPoint) -> tuple[float, float]:
    return gpx_point.latitude, gpx_point.longitude


def get_geopy_distance(gpx_point_one: gpxpy.gpx.GPXTrackPoint, gpx_point_two: gpxpy.gpx.GPXTrackPoint,
                       units: str = distance_units) -> float:
    geopy_point_one, geopy_point_two = point_gpx_to_geopy(gpx_point_one), point_gpx_to_geopy(gpx_point_two)
    geopy_distance = geopy.distance.distance(geopy_point_one, geopy_point_two)
    unit_results = getattr(geopy_distance, units)
    return unit_results


def geopy_sequence_distance(gpx_points: list[gpxpy.gpx.GPXTrackPoint], units: str = distance_units) -> float:
    previous_point = None
    total_distance = 0
    for point in gpx_points:
        if previous_point is None:
            previous_point = point
        else:
            total_distance += get_geopy_distance(previous_point, point, units)
            previous_point = point
    return total_distance


if __name__ == "__main__":
    start_time = perf_counter_ns()
    if not DATA_PATH.is_dir():
        print("Data path does not point to a directory.")
    routes_writer = DictWriter(open(OUTPUT_FILENAME, "w", newline=''),
                               fieldnames=(
                                   "Track name", "Segment", "Points", "GeoPy distance", "GeoPy closing distance",
                                   "GPX 2d distance", "GPX 3d distance", "GeoPy - GPX 3d"),
                               restval="??")
    routes_writer.writeheader()
    for route_file_path in DATA_PATH.iterdir():
        gpx = gpxpy.parse(route_file_path.open())
        for track in gpx.tracks:
            for segment_number, segment in enumerate(track.segments, start=1):
                row_data = {"Track name": track.name,
                            "Segment": segment_number,
                            "Points": len(segment.points),
                            "GeoPy distance": geopy_sequence_distance(segment.points),
                            "GeoPy closing distance": get_geopy_distance(segment.points[0], segment.points[-1]) if len(
                                segment.points) > 0 else 0,
                            "GPX 2d distance": segment.length_2d(),
                            "GPX 3d distance": segment.length_3d(),
                            }
                row_data["GeoPy - GPX 3d"] = row_data["GeoPy distance"] - row_data["GPX 3d distance"]
                routes_writer.writerow(row_data)
    end_time = perf_counter_ns()
    print(f"Runtime: {end_time - start_time}ns")
