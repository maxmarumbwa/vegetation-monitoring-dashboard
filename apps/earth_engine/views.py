import ee
from django.shortcuts import render

from apps.earth_engine.ee_config import initialize_earth_engine


def chirps_map(request):
    initialize_earth_engine()  # ensure always ready

    rainfall = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterDate("2025-01-01", "2025-01-31")
        .sum()
    )

    # Visualization parameters
    vis_params = {
        "min": 0,
        "max": 300,
        "palette": ["white", "blue", "green", "yellow", "red"],
    }

    # Generate map tile URL
    map_id = rainfall.getMapId(vis_params)

    context = {"tile_url": map_id["tile_fetcher"].url_format}

    return render(request, "chirps_map.html", context)


def home(request):
    return render(request, "home.html")


def get_rainfall_tile(request):
    try:
        date = request.GET.get("date", "2024-01-01")
        zimbabwe = (
            ee.FeatureCollection("FAO/GAUL/2015/level0")
            .filter(ee.Filter.eq("ADM0_NAME", "Zimbabwe"))
            .geometry()
        )
        image = (
            ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
            .filterDate(date, ee.Date(date).advance(1, "day"))
            .first()
            .select("precipitation")
        )
        image = image.clip(zimbabwe)
        vis_params = {
            "min": 0,
            "max": 50,
            "palette": ["white", "blue", "green", "yellow", "red"],
        }

        map_id = image.getMapId(vis_params)

        return JsonResponse({"tile_url": map_id["tile_fetcher"].url_format})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
