from django.shortcuts import render


# Create your views here.
def auth(request):
    # This is a placeholder function.
    data = {
        "ndvi": 0.75,
        "evi": 0.65,
        "savi": 0.70,
    }
    return render(request, "vegetation_data.html", {"data": data})
