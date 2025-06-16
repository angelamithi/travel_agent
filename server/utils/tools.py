import os
from dotenv import load_dotenv
import requests
from amadeus import Client, ResponseError

# Load environment variables first!
load_dotenv()

amadeus = Client(
    client_id=os.getenv("AMADEUS_API_KEY"),
    client_secret=os.getenv("AMADEUS_API_SECRET")
)

def search_flights(origin, destination, departure_date):
    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode=origin,
        destinationLocationCode=destination,
        departureDate=departure_date,
        adults=1
    )
    data = response.data

    return {
        "flights": [
            {
                "airline": offer['validatingAirlineCodes'][0],
                "price": offer['price']['total'],
                "departure": offer['itineraries'][0]['segments'][0]['departure'],
                "arrival": offer['itineraries'][0]['segments'][-1]['arrival']
            }
            for offer in data[:3]
        ]
    }

def search_hotels(city_code, checkin_date, checkout_date):
    response = amadeus.shopping.hotel_offers.get(
        cityCode=city_code,
        checkInDate=checkin_date,
        checkOutDate=checkout_date,
        adults=1
    )
    data = response.data

    return {
        "hotels": [
            {
                "name": hotel["hotel"]["name"],
                "price": hotel["offers"][0]["price"]["total"],
                "checkIn": hotel["offers"][0]["checkInDate"],
                "checkOut": hotel["offers"][0]["checkOutDate"]
            }
            for hotel in data[:3]
        ]
    }

def recommend_destinations(purpose, budget):
    # For demo, map purpose to hardcoded destinations or use Amadeus if you want real analytics.
    recommendations = {
        "relaxation": "Bali",
        "adventure": "Cape Town",
        "romantic": "Paris",
        "budget": "Bangkok",
        "luxury": "Dubai"
    }

    destination = recommendations.get(purpose.lower(), "Barcelona")
    return {
        "recommendations": [
            {
                "place": destination,
                "reason": f"Great for {purpose.lower()} trips",
                "estimated_budget": budget
            }
        ]
    }

def calculate_travel_budget(flight_cost, hotel_cost, nights, activities_cost):
    total = flight_cost + (hotel_cost * nights) + activities_cost
    return {"total_estimate": total}


def get_coordinates(city_name):
    try:
        response = amadeus.reference_data.locations.get(
            keyword=city_name,
            subType="CITY"
        )
        if response.data:
            geo = response.data[0]["geoCode"]
            return geo["latitude"], geo["longitude"]
        else:
            return None, None
    except ResponseError as e:
        return None, None
def recommend_tours(city=None, start_date=None, end_date=None, category=None, user_location=None):
    if not city and user_location:
        lat = user_location.get("latitude")
        lon = user_location.get("longitude")
        if lat and lon:
            city = reverse_geocode(lat, lon)

    if not city:
        return {"error": "City is required and could not be inferred from location."}

    latitude, longitude = get_coordinates(city)
    if not latitude or not longitude:
        return {"error": f"Could not find coordinates for {city}"}

    try:
        response = amadeus.shopping.activities.get(
            latitude=latitude,
            longitude=longitude,
            startDate=start_date,
            endDate=end_date
        )
        data = response.data

        filtered = []
        for activity in data:
            name = activity.get("name", "").lower()
            desc = activity.get("shortDescription", "").lower()
            if not category or category.lower() in name or category.lower() in desc:
                filtered.append({
                    "name": activity["name"],
                    "shortDescription": activity.get("shortDescription", "No description"),
                    "price": activity["price"]["amount"],
                    "currency": activity["price"]["currencyCode"],
                    "bookingLink": activity["bookingLink"]
                })
            if len(filtered) >= 5:
                break

        return {
    "activities": filtered or [{"message": "No matching activities found."}],
    "city": city
}

    except Exception as e:
        return {"error": str(e)}

def reverse_geocode(lat, lon):
    try:
        response = amadeus.reference_data.locations.reverse_geocoding.get(
            latitude=lat,
            longitude=lon
        )
        if response.data:
            return response.data[0]["address"]["cityName"]
        return None
    except Exception as e:
        return None