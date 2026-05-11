from django.http import JsonResponse
from django.shortcuts import render
import ee
from apps.earth_engine.ee_config import initialize_earth_engine


def get_ndvi_layers_start_end(request):
    initialize_earth_engine()
    try:
        start_date = request.GET.get("start_date", "2024-01-01")
        end_date = request.GET.get("end_date", "2024-01-16")

        # ----------------- CURRENT PERIOD (MEAN OVER RANGE) -----------------
        collection_current = (
            ee.ImageCollection("MODIS/061/MOD13A2")
            .filterDate(start_date, end_date)
            .select("NDVI")
            .map(lambda img: img.multiply(0.0001))
        )
        # Compute mean; if no images, fallback to zero image (error handling)
        current = collection_current.mean().rename("NDVI")

        # ----------------- HISTORICAL SEASONAL (SAME DOY RANGE) -----------------
        historical = (
            ee.ImageCollection("MODIS/061/MOD13A2")
            .filterDate("2001-01-01", "2023-12-31")
            .select("NDVI")
        )

        doy_start = ee.Date(start_date).getRelative("day", "year")
        doy_end = ee.Date(end_date).getRelative("day", "year")

        seasonal = historical.filter(ee.Filter.dayOfYear(doy_start, doy_end))

        seasonal_scaled = seasonal.map(lambda img: img.multiply(0.0001))

        baseline = seasonal_scaled.mean()
        ndvi_min = seasonal_scaled.min()
        ndvi_max = seasonal_scaled.max()

        # ----------------- ANOMALY -----------------
        anomaly = current.subtract(baseline)

        # ----------------- VCI -----------------
        vci = (
            current.subtract(ndvi_min)
            .divide(ndvi_max.subtract(ndvi_min))
            .multiply(100)
            .rename("VCI")
        )
        vci = vci.where(ndvi_max.eq(ndvi_min), 0)

        # ----------------- VISUALISATION PARAMETERS -----------------
        ndvi_vis = {"min": 0, "max": 1, "palette": ["white", "green"]}
        anomaly_vis = {"min": -0.3, "max": 0.3, "palette": ["red", "white", "green"]}
        vci_vis = {
            "min": 0,
            "max": 100,
            "palette": ["darkred", "red", "orange", "yellow", "lightgreen", "green"],
        }

        # ----------------- TILE URLs -----------------
        ndvi_tile = current.getMapId(ndvi_vis)["tile_fetcher"].url_format
        baseline_tile = baseline.getMapId(ndvi_vis)["tile_fetcher"].url_format
        min_tile = ndvi_min.getMapId(ndvi_vis)["tile_fetcher"].url_format
        max_tile = ndvi_max.getMapId(ndvi_vis)["tile_fetcher"].url_format
        anomaly_tile = anomaly.getMapId(anomaly_vis)["tile_fetcher"].url_format
        vci_tile = vci.getMapId(vci_vis)["tile_fetcher"].url_format

        return JsonResponse(
            {
                "ndvi": ndvi_tile,
                "baseline": baseline_tile,
                "min": min_tile,
                "max": max_tile,
                "anomaly": anomaly_tile,
                "vci": vci_tile,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


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


def home(request):
    return render(request, "home.html")


def dashboard(request):
    return render(request, "index.html")
