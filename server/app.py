from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from openai import OpenAI
from utils.tools import search_flights, search_hotels, recommend_destinations, calculate_travel_budget, recommend_tours, get_iata_code
from tool_schemas import tools
from flask_cors import CORS
from dateparser import parse as parse_date
from datetime import datetime

# Load environment and OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def is_greeting(message):
    message = message.lower().strip()
    return message in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']

def parse_and_validate_date(raw_date):
    today = datetime.now()
    parsed = parse_date(raw_date, settings={"PREFER_DAY_OF_MONTH": "first"})

    if not parsed:
        return None, "unrecognized"

    # If the year wasn't specified, or it's being misinferred
    inferred_year = parsed.year if parsed.year != 1900 else None
    month_day = parsed.strftime("%m-%d")

    # Try assuming current year if date is ambiguous or past
    assumed_date = datetime.strptime(f"{today.year}-{month_day}", "%Y-%m-%d")

    if assumed_date.date() < today.date():
        # If user said "this year" explicitly, try forcing it
        if "this year" in raw_date.lower():
            return assumed_date, "past"
        # Otherwise prompt for clarification
        return None, "past"

    return assumed_date, "ok"


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    @app.route("/chat", methods=["POST"])
    def chat():
        user_input = request.json.get("message", "").strip()
        chat_history = request.json.get("history", [])
        user_location = request.json.get("location")
        last_known_city = request.json.get("lastKnownCity")

        if is_greeting(user_input):
            return jsonify({
                "response": "Hi! How can I assist you with your travel plans today?"
            })

        # Build conversation history
        messages = [{"role": "system", "content": "You are a helpful travel assistant."}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
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
                print(f"[DEBUG] Calling {func_name} with arguments:", args)
                required = ['origin', 'destination', 'departure_date']
                if not all(arg in args and args[arg] for arg in required):
                    return jsonify({"response": "Missing required flight search parameters."})

                raw_date = args["departure_date"]
                parsed_date, status = parse_and_validate_date(raw_date)

                if status == "unrecognized":
                    return jsonify({"response": f"I couldn't understand the date '{raw_date}'. Please provide a valid travel date."})

                # inside search_flights handling block
                if status == "past":
                    # Store the last attempted date
                    request.session = {
                        "last_date_prompt": raw_date
                    }
                    return jsonify({
                        "response": f"The date '{raw_date}' seems to be in the past. Did you mean this year or next year?"
                    })


                args["departure_date"] = parsed_date.strftime("%Y-%m-%d")
                origin_name = args["origin"]
                destination_name = args["destination"]

                origin_code = get_iata_code(origin_name)
                destination_code = get_iata_code(destination_name)

                if not origin_code or not destination_code:
                    return jsonify({
                        "response": f"Could not find IATA codes for '{origin_name}' or '{destination_name}'."
                    })

                args["origin"] = origin_code
                args["destination"] = destination_code
                result = search_flights(**args)
                tool_output = result

            elif func_name == "search_hotels":
                result = search_hotels(**args)
                tool_output = result

            elif func_name == "recommend_destinations":
                result = recommend_destinations(**args)
                tool_output = result

            elif func_name == "calculate_travel_budget":
                result = calculate_travel_budget(**args)
                tool_output = result

            elif func_name == "recommend_tours":
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
                tool_output = {"error": "Unknown tool"}

            # Follow-up response using tool result
            followup = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful travel assistant."},
                    *chat_history,
                    {"role": "user", "content": user_input},
                    message,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": str(tool_output)
                    }
                ]
            )

            final = followup.choices[0].message.content
            return jsonify({
                "response": final,
                "city": result.get("city") if func_name == "recommend_tours" else None
            })

        # No tools triggered, return raw content
        return jsonify({"response": message.content})

    return app

app = create_app()
