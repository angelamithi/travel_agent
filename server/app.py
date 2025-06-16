# === File: generated_travel_agent/backend/app.py ===
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import openai
from utils.tools import search_flights, search_hotels, recommend_destinations,calculate_travel_budget,recommend_tours
from flask_cors import CORS,cross_origin



def create_app():
    app = Flask(__name__)

    load_dotenv()

  
    openai.api_key = os.getenv("OPENAI_API_KEY")
    CORS(app, resources={r"/*": {"origins": "*"}})  # Allow cross-origin requests

    @app.route("/chat", methods=["POST"])
    def chat():
        user_input = request.json.get("message")
        chat_history = request.json.get("history", [])
        user_location = request.json.get("location")
        last_known_city = request.json.get("lastKnownCity")

        messages = [{"role": "system", "content": "You are a helpful travel assistant."}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            func_name = tool_call.function.name
            args = eval(tool_call.function.arguments)

            if func_name == "search_flights":
                result = search_flights(**args)
            elif func_name == "search_hotels":
                result = search_hotels(**args)
            elif func_name == "recommend_destinations":
                result = recommend_destinations(**args)
            elif func_name == "calculate_travel_budget":
                result = calculate_travel_budget(**args)
            elif func_name == "recommend_tours":
                # Inject fallback city logic
                if "city" not in args or not args["city"]:
                    if last_known_city:
                        args["city"] = last_known_city
                    elif user_location:
                        args["user_location"] = user_location

                result = recommend_tours(**args)
                tool_output = {
                    "activities": result.get("activities", []),
                    "city": result.get("city")
                }
            else:
                result = {"error": "Unknown tool"}
                tool_output = result

            followup = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful travel assistant."},
                    {"role": "user", "content": user_input},
                    message,
                    {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": str(tool_output)}
                ]
            )
            final = followup.choices[0].message["content"]

            return jsonify({
                "response": final,
                "city": result.get("city") if func_name == "recommend_tours" else None
            })

        return jsonify({"response": message["content"]})



    # === File: generated_travel_agent/backend/tool_schemas.py ===
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

    return app



app = create_app()