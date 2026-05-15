import ee
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from apps.earth_engine.ee_config import initialize_earth_engine


def get_ndvi_layers_start_end(request):

    initialize_earth_engine()

    try:
        start_date = request.GET.get("start_date", "2024-01-01")
        end_date = request.GET.get("end_date", "2024-01-16")

        # =========================================================
        # CLIP OPTION
        # Default = FALSE
        # =========================================================
        clip_param = request.GET.get("clip", "false").lower() == "true"

        # =========================================================
        # ZIMBABWE BOUNDING BOX
        # Used for fast rendering by default
        # =========================================================
        zim_bbox = ee.Geometry.Rectangle([23.30, -22.8, 34.0, -15.0])

        # =========================================================
        # EXACT ZIMBABWE GEOMETRY
        # Used only when clipping is enabled
        # =========================================================
        zim = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(
            ee.Filter.eq("ADM0_NAME", "Zimbabwe")
        )

        zim_geom = zim.geometry()

        # =========================================================
        # HELPER FUNCTION
        # =========================================================
        def prepare_image(img):

            # Always constrain to Zimbabwe extent
            img = img.clip(zim_bbox)

            # Only clip to exact Zimbabwe border if enabled
            if clip_param:
                img = img.clip(zim_geom)

            return img

        # =========================================================
        # CURRENT NDVI
        # =========================================================
        collection_current = (
            ee.ImageCollection("MODIS/061/MOD13A2")
            .filterBounds(zim_bbox)
            .filterDate(start_date, end_date)
            .select("NDVI")
            .map(lambda img: img.multiply(0.0001))
        )

        current = collection_current.mean().rename("NDVI")

        current = prepare_image(current)

        # =========================================================
        # HISTORICAL
        # =========================================================
        historical = (
            ee.ImageCollection("MODIS/061/MOD13A2")
            .filterBounds(zim_bbox)
            .filterDate("2001-01-01", "2023-12-31")
            .select("NDVI")
        )

        doy_start = ee.Date(start_date).getRelative("day", "year")
        doy_end = ee.Date(end_date).getRelative("day", "year")

        seasonal = historical.filter(ee.Filter.dayOfYear(doy_start, doy_end))

        seasonal_scaled = seasonal.map(lambda img: img.multiply(0.0001))

        baseline = prepare_image(seasonal_scaled.mean().rename("Baseline"))

        ndvi_min = prepare_image(seasonal_scaled.min().rename("NDVI_Min"))

        ndvi_max = prepare_image(seasonal_scaled.max().rename("NDVI_Max"))

        # =========================================================
        # ANOMALY
        # =========================================================
        anomaly = prepare_image(current.subtract(baseline).rename("NDVI_Anomaly"))

        # =========================================================
        # VCI
        # =========================================================
        vci = (
            current.subtract(ndvi_min)
            .divide(ndvi_max.subtract(ndvi_min))
            .multiply(100)
            .rename("VCI")
        )

        # Avoid divide-by-zero
        vci = vci.where(ndvi_max.eq(ndvi_min), 0)

        vci = prepare_image(vci)

        # =========================================================
        # VISUALIZATION PARAMETERS
        # =========================================================
        ndvi_vis = {"min": 0, "max": 1, "palette": ["white", "green"]}
        anomaly_vis = {"min": -0.3, "max": 0.3, "palette": ["red", "white", "green"]}
        vci_vis = {
            "min": 0,
            "max": 100,
            "palette": ["darkred", "red", "orange", "yellow", "lightgreen", "green"],
        }

        # =========================================================
        # TILE URLS
        # =========================================================
        ndvi_tile = current.getMapId(ndvi_vis)["tile_fetcher"].url_format

        baseline_tile = baseline.getMapId(ndvi_vis)["tile_fetcher"].url_format

        anomaly_tile = anomaly.getMapId(anomaly_vis)["tile_fetcher"].url_format

        vci_tile = vci.getMapId(vci_vis)["tile_fetcher"].url_format

        return JsonResponse(
            {
                "ndvi": ndvi_tile,
                "baseline": baseline_tile,
                "anomaly": anomaly_tile,
                "vci": vci_tile,
            }
        )

    except Exception as e:

        return JsonResponse({"error": str(e)}, status=500)


# ============================================================================
# DOWNLOAD DISPLAYED MAP AS GEOTIFF
# ============================================================================


def download_ndvi_geotiff(request):

    initialize_earth_engine()

    try:
        start_date = request.GET.get("start_date", "2024-01-01")
        end_date = request.GET.get("end_date", "2024-01-16")

        layer = request.GET.get("layer", "NDVI")

        # =========================================================
        # CLIP OPTION
        # =========================================================
        clip_param = request.GET.get("clip", "false").lower() == "true"

        # =========================================================
        # ZIMBABWE BOUNDING BOX
        # =========================================================
        zim_bbox = ee.Geometry.Rectangle([23.30, -22.8, 34.0, -15.0])

        # =========================================================
        # EXACT ZIMBABWE GEOMETRY
        # =========================================================
        zim = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(
            ee.Filter.eq("ADM0_NAME", "Zimbabwe")
        )

        zim_geom = zim.geometry()

        # =========================================================
        # HELPER FUNCTION
        # =========================================================
        def prepare_image(img):

            # Always constrain to Zimbabwe extent
            img = img.clip(zim_bbox)

            # Optional exact clipping
            if clip_param:
                img = img.clip(zim_geom)

            return img

        # =========================================================
        # CURRENT NDVI
        # =========================================================
        collection_current = (
            ee.ImageCollection("MODIS/061/MOD13A2")
            .filterBounds(zim_bbox)
            .filterDate(start_date, end_date)
            .select("NDVI")
            .map(lambda img: img.multiply(0.0001))
        )

        current = collection_current.mean().rename("NDVI")

        current = prepare_image(current)

        # =========================================================
        # HISTORICAL
        # =========================================================
        historical = (
            ee.ImageCollection("MODIS/061/MOD13A2")
            .filterBounds(zim_bbox)
            .filterDate("2001-01-01", "2023-12-31")
            .select("NDVI")
        )

        doy_start = ee.Date(start_date).getRelative("day", "year")
        doy_end = ee.Date(end_date).getRelative("day", "year")

        seasonal = historical.filter(ee.Filter.dayOfYear(doy_start, doy_end))

        seasonal_scaled = seasonal.map(lambda img: img.multiply(0.0001))

        baseline = prepare_image(seasonal_scaled.mean().rename("Baseline"))

        ndvi_min = prepare_image(seasonal_scaled.min().rename("NDVI_Min"))

        ndvi_max = prepare_image(seasonal_scaled.max().rename("NDVI_Max"))

        # =========================================================
        # ANOMALY
        # =========================================================
        anomaly = prepare_image(current.subtract(baseline).rename("NDVI_Anomaly"))

        # =========================================================
        # VCI
        # =========================================================
        vci = (
            current.subtract(ndvi_min)
            .divide(ndvi_max.subtract(ndvi_min))
            .multiply(100)
            .rename("VCI")
        )

        # Avoid divide-by-zero
        vci = vci.where(ndvi_max.eq(ndvi_min), 0)

        vci = prepare_image(vci)

        # =========================================================
        # SELECT EXPORT IMAGE
        # =========================================================
        if layer == "NDVI":

            export_image = current

        elif layer == "Baseline":

            export_image = baseline

        elif layer == "Anomaly":

            export_image = anomaly

        elif layer == "VCI":

            export_image = vci

        else:

            return JsonResponse({"error": "Invalid layer"}, status=400)

        # =========================================================
        # EXPORT REGION
        # =========================================================
        export_region = (
            zim_geom.coordinates().getInfo()
            if clip_param
            else zim_bbox.coordinates().getInfo()
        )

        # =========================================================
        # CREATE DOWNLOAD URL
        # =========================================================
        download_url = export_image.getDownloadURL(
            {
                "region": export_region,
                "scale": 1000,
                "crs": "EPSG:4326",
                "format": "GEO_TIFF",
                "filePerBand": False,
            }
        )

        return JsonResponse({"download_url": download_url})

    except Exception as e:

        return JsonResponse({"error": str(e)}, status=500)


############################### Get time series of NDVI anomaly for a point ############################


def get_ndvi_anomaly_timeseries(request):
    try:
        lat = float(request.GET.get("lat"))
        lon = float(request.GET.get("lon"))
        start_date = request.GET.get("start_date", "2024-01-01")
        end_date = request.GET.get("end_date", "2024-03-01")

        point = ee.Geometry.Point([lon, lat])

        # ---------------- CURRENT NDVI ----------------
        collection = (
            ee.ImageCollection("MODIS/061/MOD13A2")
            .filterDate(start_date, end_date)
            .select("NDVI")
        )

        # ---------------- HISTORICAL ----------------
        historical = (
            ee.ImageCollection("MODIS/061/MOD13A2")
            .filterDate("2001-01-01", "2023-12-31")
            .select("NDVI")
        )

        # ---------------- FUNCTION ----------------
        def extract_values(image):

            date = image.date()
            doy = date.getRelative("day", "year")

            # ✅ STRICT 16-DAY MATCH (NO SMOOTHING)
            seasonal = historical.filter(ee.Filter.dayOfYear(doy, doy.add(15)))

            # ---------------- CLIMATOLOGY ----------------
            baseline_img = seasonal.mean()
            min_img = seasonal.min()
            max_img = seasonal.max()

            # ---------------- REDUCE ----------------
            ndvi_val = image.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=point, scale=1000, bestEffort=True
            ).get("NDVI")

            baseline_val = baseline_img.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=point, scale=1000, bestEffort=True
            ).get("NDVI")

            min_val = min_img.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=point, scale=1000, bestEffort=True
            ).get("NDVI")

            max_val = max_img.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=point, scale=1000, bestEffort=True
            ).get("NDVI")

            # ---------------- ANOMALY ----------------
            anomaly = ee.Number(ndvi_val).subtract(baseline_val)

            return ee.Feature(
                None,
                {
                    "date": date.format("YYYY-MM-dd"),
                    "ndvi": ndvi_val,
                    "baseline": baseline_val,
                    "min": min_val,
                    "max": max_val,
                    "anomaly": anomaly,
                },
            )

        features = collection.map(extract_values).getInfo()

        # ---------------- FORMAT ----------------
        data = []
        for f in features["features"]:
            p = f["properties"]

            data.append(
                {
                    "date": p["date"],
                    "ndvi": (p["ndvi"] or 0) * 0.0001,
                    "baseline": (p["baseline"] or 0) * 0.0001,
                    "min": (p["min"] or 0) * 0.0001,
                    "max": (p["max"] or 0) * 0.0001,
                    "anomaly": (p["anomaly"] or 0) * 0.0001,
                }
            )

        return JsonResponse({"data": data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    #


########################### get NDVI ZONAL STATS ############################

import ee
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta


@csrf_exempt
def get_ndvi_zonal_timeseries(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
        geometry_geojson = data.get("geometry")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Convert GeoJSON to ee.Geometry
        geom_type = geometry_geojson.get("type")

        if geom_type == "Polygon":
            ee_geom = ee.Geometry.Polygon(geometry_geojson["coordinates"])

        elif geom_type == "MultiPolygon":
            ee_geom = ee.Geometry.MultiPolygon(geometry_geojson["coordinates"])

        else:
            return JsonResponse(
                {"error": f"Unsupported geometry type: {geom_type}"}, status=400
            )

        # simplify complex district boundaries
        ee_geom = ee_geom.simplify(1000)

        # 1. Current NDVI time series (MODIS 16-day)
        collection = (
            ee.ImageCollection("MODIS/061/MOD13A2")
            .filterDate(start_date, end_date)
            .select("NDVI")
            .map(
                lambda img: img.multiply(0.0001).copyProperties(
                    img, img.propertyNames()
                )
            )
        )

        # 2. Baseline: long-term mean per day-of-year (2000-2020)
        baseline_coll = (
            ee.ImageCollection("MODIS/061/MOD13A2")
            .filterDate("2000-01-01", "2020-12-31")
            .select("NDVI")
        )

        def get_doy_mean(doy):
            return (
                baseline_coll.filter(ee.Filter.calendarRange(doy, doy, "day_of_year"))
                .mean()
                .multiply(0.0001)
            )

        dates = []
        ndvi_vals = []
        baseline_vals = []
        anomaly_vals = []

        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            doy = int(current.strftime("%j"))
            next_date = (current + timedelta(days=16)).strftime("%Y-%m-%d")

            # Get image for this period
            img = collection.filterDate(date_str, next_date).first()
            if img is not None:
                ndvi_val = img.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=ee_geom,
                    scale=1000,
                    bestEffort=True,
                ).get("NDVI")
                ndvi = ndvi_val.getInfo()
            else:
                ndvi = None

            # Baseline
            baseline_img = get_doy_mean(doy)
            baseline_val = baseline_img.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=ee_geom, scale=1000, bestEffort=True
            ).get("NDVI")
            baseline = baseline_val.getInfo()

            if ndvi is not None and baseline is not None:
                ndvi_vals.append(round(ndvi, 3))
                baseline_vals.append(round(baseline, 3))
                anomaly_vals.append(round(ndvi - baseline, 3))
                dates.append(date_str)

            current += timedelta(days=16)

        return JsonResponse(
            {
                "data": [
                    {"date": d, "ndvi": n, "baseline": b, "anomaly": a}
                    for d, n, b, a in zip(dates, ndvi_vals, baseline_vals, anomaly_vals)
                ]
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def home(request):
    return render(request, "home.html")


def dashboard(request):
    return render(request, "index.html")
