"""Offline terrain research. Does not modify the Blender model or published world.

Fetch the documented Open-Meteo /v1/elevation endpoint only with --fetch.
The source is Copernicus GLO-90 DSM (90 m); these are surface samples, not
surveyed ground heights. Re-run without --fetch to analyse the saved responses.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge/sources/arboretum/terrain-analysis-2026-10-03"
ORIGIN = (35.00648, 126.8256689)
METRES_PER_LON = 111320 * math.cos(math.radians(ORIGIN[0]))
ENDPOINT = "https://api.open-meteo.com/v1/elevation"
IMAGERY = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer"


def point(label: str, x: float, z: float, **extra) -> dict:
    return {"label": label, "x": x, "z": z,
            "latitude": round(ORIGIN[0] - z / 111320, 7),
            "longitude": round(ORIGIN[1] + x / METRES_PER_LON, 7), **extra}


def grid(xs, zs):
    return [point(f"grid-{row}-{col}", x, z, row=row, col=col)
            for row, z in enumerate(zs) for col, x in enumerate(xs)]


def save(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch(name: str, samples: list[dict], enabled: bool) -> dict:
    path = OUT / f"{name}.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if [{k: s[k] for k in ("label", "x", "z")} for s in data["samples"]] != [
                {k: s[k] for k in ("label", "x", "z")} for s in samples]:
            raise ValueError(f"Saved sample locations differ: {path}")
        return data
    if not enabled:
        raise RuntimeError(f"Missing {path}; use --fetch to request the public API")
    if not 0 < len(samples) <= 100:
        raise ValueError("The API supports at most 100 coordinates per request")
    params = {axis: ",".join(str(s[axis]) for s in samples)
              for axis in ("latitude", "longitude")}
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "NajuArboretumTerrainResearch/1.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        raw = response.read()
        status = response.status
    payload = json.loads(raw)
    heights = payload.get("elevation", [])
    if status != 200 or len(heights) != len(samples) or any(
            not isinstance(h, (float, int)) or not math.isfinite(h) for h in heights):
        raise ValueError("Invalid elevation response")
    data = {
        "retrievedAtUTC": datetime.now(timezone.utc).isoformat(),
        "requestUrl": url,
        "responseSHA256": hashlib.sha256(raw).hexdigest(),
        "dataset": "Copernicus DEM 2021 release GLO-90 via Open-Meteo",
        "nativeResolutionMetres": 90,
        "measurement": "DSM surface elevations; vegetation and buildings may affect heights",
        "units": "metres reported by API; not a local ground survey",
        "originWGS84": list(ORIGIN),
        "coordinateConvention": "project x=east, z=south; local equirectangular conversion",
        "rawResponse": payload,
        "samples": [dict(s, elevationMetres=h) for s, h in zip(samples, heights)],
        "attribution": "Copernicus programme and Open-Meteo; https://doi.org/10.5270/ESA-c5d3d65",
    }
    save(path, data)
    return data


def fetch_satellite(enabled: bool):
    """Research image only, with returned extent and credits retained."""
    path = OUT / "regional-satellite.json"
    image_path = OUT / "regional-satellite.jpg"
    if path.exists() and image_path.exists():
        return
    if not enabled:
        raise RuntimeError("Use --fetch --satellite to save the regional reference image")
    def mercator(x, z):
        lat = ORIGIN[0] - z/111320
        lon = ORIGIN[1] + x/METRES_PER_LON
        return (6378137*math.radians(lon),
                6378137*math.log(math.tan(math.pi/4+math.radians(lat)/2)))
    west, south = mercator(-750, 500)
    east, north = mercator(1750, -1500)
    params = {"bbox": f"{west},{south},{east},{north}", "bboxSR": "3857",
              "imageSR": "3857", "size": "1600,1280", "format": "jpg", "f": "json"}
    url = IMAGERY + "/export?" + urllib.parse.urlencode(params)
    def read(remote):
        request = urllib.request.Request(remote, headers={"User-Agent": "NajuArboretumTerrainResearch/1.0"})
        with urllib.request.urlopen(request, timeout=25) as response:
            return response.read()
    result = json.loads(read(url))
    if "href" not in result or "extent" not in result:
        raise ValueError("Imagery service did not return an image and extent")
    credits = json.loads(read(IMAGERY + "?f=pjson")).get("copyrightText", "Esri World Imagery")
    raw_image = read(result["href"])
    if not raw_image.startswith(b"\xff\xd8"):
        raise ValueError("Expected a JPEG research image")
    image_path.write_bytes(raw_image)
    save(path, {"retrievedAtUTC": datetime.now(timezone.utc).isoformat(),
        "requestUrl": url, "service": IMAGERY,
        "imageSHA256": hashlib.sha256(raw_image).hexdigest(),
        "copyrightText": credits, "imageryAcquisitionDate": "unverified",
        "usage": "offline terrain research reference, not a runtime texture",
        "response": result})


def inside(x: float, z: float, polygon) -> bool:
    result = False
    for (ax, az), (bx, bz) in zip(polygon, polygon[1:] + polygon[:1]):
        if (az > z) != (bz > z) and x < (bx-ax) * (z-az) / (bz-az) + ax:
            result = not result
    return result


def summary(samples):
    low = min(samples, key=lambda s: s["elevationMetres"])
    high = max(samples, key=lambda s: s["elevationMetres"])
    return {"sampleCount": len(samples), "minimumMetres": low["elevationMetres"],
            "maximumMetres": high["elevationMetres"],
            "sampledRangeMetres": round(high["elevationMetres"]-low["elevationMetres"], 2),
            "lowestSample": low, "highestSample": high}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--satellite", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.satellite:
        fetch_satellite(args.fetch)
    world_path = ROOT / "public/naju-arboretum-world.json"
    world = json.loads(world_path.read_text(encoding="utf-8"))
    campus = next(s["footprint"] for s in world["solids"] if s["name"] == "ground_campus_osm")
    regional_xs = list(range(-750, 1751, 250))
    regional_zs = list(range(-1500, 501, 250))
    regional = fetch("regional-glo90", grid(regional_xs, regional_zs), args.fetch)
    campus_xs = list(range(-525, 196, 90))
    campus_zs = list(range(-300, 241, 90))
    samples = grid(campus_xs, campus_zs)
    samples.append(point("spawn", world["spawn"]["x"], world["spawn"]["z"]))
    for place in world["places"]:
        x, z = place.get("arrival", place["position"])
        samples.append(point(place["id"], x, z))
    for i in range(11):
        distance = i * 43
        samples.append(point(f"avenue-profile-{i}", -475+distance*.98, -50+distance*.2,
                             avenueParameter=distance))
    refined = fetch("campus-glo90", samples, args.fetch)
    campus_samples = [s for s in refined["samples"] if "row" in s and inside(s["x"], s["z"], campus)]
    profile = [s for s in refined["samples"] if "avenueParameter" in s]
    horizontal = math.hypot(profile[-1]["x"]-profile[0]["x"], profile[-1]["z"]-profile[0]["z"])
    rise = profile[-1]["elevationMetres"]-profile[0]["elevationMetres"]
    result = {
        "scope": "Preliminary map and DSM analysis, not verified ground geometry",
        "worldSHA256": hashlib.sha256(world_path.read_bytes()).hexdigest(),
        "campusPolygon": campus,
        "currentWorldBounds": world["bounds"],
        "regionalGrid": {"xs": regional_xs, "zs": regional_zs, "spacingMetres": 250},
        "campusGrid": {"xs": campus_xs, "zs": campus_zs, "spacingMetres": 90},
        "regionalSurfaceSummary": summary(regional["samples"]),
        "insideCampusSurfaceSummary": summary(campus_samples),
        "landmarkSurfaceSamples": [s for s in refined["samples"] if "row" not in s and "avenueParameter" not in s],
        "avenueSurfaceProfile": {"samples": profile,
            "horizontalLengthMetres": round(horizontal, 2), "endpointRiseMetres": round(rise, 2),
            "endpointAverageSurfaceGradePercent": round(rise/horizontal*100, 2),
            "caveat": "DSM profile only; not a path survey and not the final slope to implement"},
        "cautions": ["GLO-90 surface values can include tree canopy and roofs.",
            "250 m regional spacing may miss a summit or local ridgeline.",
            "A denser Blender mesh is interpolation, not higher source accuracy.",
            "The official visitor diagram is not georeferenced; do not treat diagram-up as north."]
    }
    save(OUT / "analysis.json", result)
    print(json.dumps({"regional": result["regionalSurfaceSummary"],
        "insideCampus": result["insideCampusSurfaceSummary"],
        "landmarks": result["landmarkSurfaceSamples"],
        "avenueProfile": {k:v for k,v in result["avenueSurfaceProfile"].items() if k != "samples"}},
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
