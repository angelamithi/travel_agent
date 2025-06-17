tools = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search for flights using Amadeus API",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "departure_date": {"type": "string", "format": "date"}
                },
                "required": ["origin", "destination", "departure_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": "Search for hotels using Amadeus API",
            "parameters": {
                "type": "object",
                "properties": {
                    "city_code": {"type": "string"},
                    "checkin_date": {"type": "string", "format": "date"},
                    "checkout_date": {"type": "string", "format": "date"}
                },
                "required": ["city_code", "checkin_date", "checkout_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_destinations",
            "description": "Recommend destinations using Amadeus API based on travel purpose and budget",
            "parameters": {
                "type": "object",
                "properties": {
                    "purpose": {"type": "string"},
                    "budget": {"type": "string"}
                },
                "required": ["purpose", "budget"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_travel_budget",
            "description": "Estimate total travel cost for a given trip plan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_cost": {"type": "number"},
                    "hotel_cost": {"type": "number"},
                    "nights": {"type": "number"},
                    "activities_cost": {"type": "number"}
                },
                "required": ["flight_cost", "hotel_cost", "nights", "activities_cost"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_tours",
            "description": "Recommend tours based on city, category, and dates. Will auto-detect city from user location if city is missing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "category": {"type": "string"},
                    "user_location": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"}
                        }
                    }
                },
                "required": ["start_date", "end_date"]
            }
        }
    }
]
