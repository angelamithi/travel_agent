import os
from dotenv import load_dotenv
import requests
from amadeus import Client, ResponseError
from dateparser import parse as parse_date
from datetime import datetime

# Load environment variables first!
load_dotenv()

amadeus = Client(
    client_id=os.getenv("AMADEUS_API_KEY"),
    client_secret=os.getenv("AMADEUS_API_SECRET")
)



def parse_and_validate_date(raw_date):
    today = datetime.now()
    current_year = today.year
    next_year = current_year + 1
    lower_date = raw_date.lower().strip()

    if lower_date == "this year":
        return datetime(current_year, 1, 1), "ok"
    elif lower_date == "next year":
        return datetime(next_year, 1, 1), "ok"

    parsed = parse_date(
        raw_date,
        settings={
            "PREFER_DAY_OF_MONTH": "first",
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": today
        }
    )

    if not parsed:
        return None, "unrecognized"

    if parsed.month < today.month or (parsed.month == today.month and parsed.day < today.day):
        parsed = parsed.replace(year=next_year)
    else:
        parsed = parsed.replace(year=current_year)

    if parsed.date() < today.date():
        return None, "past"

    return parsed, "ok"

def search_flights(origin, destination, departure_date):
    parsed_date, status = parse_and_validate_date(departure_date)
    if status == "unrecognized":
        return {"error": f"I couldn't understand the date '{departure_date}'. Please provide a valid travel date."}
    if status == "past":
        return {"error": f"The date '{departure_date}' seems to be in the past. Did you mean this year or next year?"}

    readable_date = parsed_date.strftime("%A, %B %d, %Y")
    confirmed_msg = f"Got it! You want to search for flights on **{readable_date}**. Let me check..."

    origin_code = get_iata_code(origin)
    destination_code = get_iata_code(destination)

    if not origin_code or not destination_code:
        return {"error": f"Could not find IATA codes for '{origin}' or '{destination}'."}

    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin_code,
            destinationLocationCode=destination_code,
            departureDate=parsed_date.strftime("%Y-%m-%d"),
            adults=1
        )
        data = response.data

        return {
            "confirm_msg": confirmed_msg,
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

    except ResponseError as e:
        print("Amadeus API error:", e.response.status_code, e.response.body)
        return {"error": "Failed to fetch flights. Please check your input parameters."}


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
    
def get_iata_code(city_name):
    # If already 3 uppercase letters, assume it's a valid IATA code
    if isinstance(city_name, str) and len(city_name) == 3 and city_name.isalpha() and city_name.isupper():
        return city_name

    try:
        response = amadeus.reference_data.locations.get(
            keyword=city_name,
            subType="CITY"
        )
        if response.data:
            return response.data[0]["iataCode"]
        return None
    except Exception as e:
        print("IATA lookup failed:", e)
        return None
