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
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'hi there', 'howdy', 'greetings']
    return any(greet in message.lower() for greet in greetings)


def parse_and_validate_date(raw_date, previous_date_str=None):
    today = datetime.now()
    current_year = today.year
    next_year = current_year + 1
    lower_date = raw_date.lower().strip()

    # Handle "this year" or "next year" explicitly
    if lower_date == "this year":
        return datetime(today.year, 1, 1), "ok"
    elif lower_date == "next year":
        return datetime(today.year + 1, 1, 1), "ok"

    # Parse the natural language date
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

    # Check if it's a partial date (e.g. "24th May") that could refer to a past month
    if parsed.month < today.month or (parsed.month == today.month and parsed.day < today.day):
        # The user probably meant next year
        parsed = parsed.replace(year=next_year)
    else:
        # If still ambiguous (e.g., "25 July" and today is before that), stick to this year
        parsed = parsed.replace(year=current_year)

    if parsed.date() < today.date():
        return None, "past"

    return parsed, "ok"




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
        
        # ✳️ Guardrail: Check if input is travel-related
        classification_prompt = f"""
        Classify the following message. Is the user asking about travel (flights, hotels, destinations, tours, budget, cities, dates)? 
        Answer only 'yes' or 'no'.

        Message: \"{user_input}\"
        """

        classification_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a classifier that answers with only 'yes' or 'no'."},
                {"role": "user", "content": classification_prompt}
            ]
        )

        is_travel_related = classification_response.choices[0].message.content.strip().lower()

        if is_travel_related != "yes":
            return jsonify({
                "response": "I'm a travel planner here to help with your travel plans. Could you please rephrase your question in that context?"
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

                result = search_flights(**args)

                if "error" in result:
                    return jsonify({"response": result["error"]})

                confirm_msg = result.get("confirm_msg", "")
                tool_output = {"flights": result.get("flights", [])}


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

            final = f"{confirm_msg}\n\n{followup.choices[0].message.content}"


            return jsonify({
                "response": final,
                "city": result.get("city") if func_name == "recommend_tours" else None
            })


        # No tools triggered, return raw content
        return jsonify({"response": message.content})

    return app

app = create_app()