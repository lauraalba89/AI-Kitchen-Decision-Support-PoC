import calendar
import re
import unicodedata
import os
import json

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import torch

from chronos import BaseChronosPipeline
from dotenv import load_dotenv
from google import genai


from config import (
    SALES_FILE,
    RECIPES_FILE,
    TIME_SERIES_FILE,
    INVENTORY_FILE,
)


sales = pd.read_excel(SALES_FILE)
recipes = pd.read_excel(RECIPES_FILE)
time_series = pd.read_excel(TIME_SERIES_FILE)
inventory = pd.read_excel(INVENTORY_FILE)

inventory["order_date"] = pd.to_datetime(
    inventory["order_date"]
)

# Get the ingredient names available in the recipe data

ingredient_names = sorted(
    recipes["pizza_ingredients"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)

# Load Gemini API configuration

load_dotenv()

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Load Chronos-2

chronos_pipeline = BaseChronosPipeline.from_pretrained(
    "amazon/chronos-2",
    device_map="cpu",
    torch_dtype=torch.float32
)


# Prepare the historical sales data

history = time_series.melt(
    id_vars="order_date",
    var_name="item_id",
    value_name="target"
)

history = history.rename(
    columns={"order_date": "timestamp"}
)

history["timestamp"] = pd.to_datetime(
    history["timestamp"]
)

history = history[
    history["timestamp"].between(
        "2015-01-01",
        "2015-12-31"
    )
].copy()


# Generate the 2016 forecast

forecast_2016 = chronos_pipeline.predict_df(
    history,
    prediction_length=365,
    id_column="item_id",
    timestamp_column="timestamp",
    target="target",
    freq="D",
    batch_size=32
)

forecast_2016["timestamp"] = pd.to_datetime(
    forecast_2016["timestamp"]
)


# Load the simulated 2016 inventory

inventory_2016 = pd.read_excel(
    "7.Simulated_Inventory_2016.xlsx"
)

inventory_2016["order_date"] = pd.to_datetime(
    inventory_2016["order_date"]
)

# Standardise the ingredient name used in the inventory
inventory_2016["ingredient"] = inventory_2016[
    "ingredient"
].replace(
    {"Nduja Salami": "N'duja Salami"}
)


# Keep only forecast dates available in the 2016 inventory

valid_dates_2016 = (
    set(forecast_2016["timestamp"])
    & set(inventory_2016["order_date"])
)

validated_forecast = forecast_2016[
    forecast_2016["timestamp"].isin(
        valid_dates_2016
    )
].copy()


# Convert forecasts into pizza preparation quantities

validated_forecast["prep_quantity"] = np.ceil(
    validated_forecast["predictions"].clip(
        lower=0
    )
).astype(int)


# Convert the pizza forecast into ingredient requirements

validated_details = validated_forecast[
    [
        "item_id",
        "timestamp",
        "prep_quantity"
    ]
].merge(
    recipes[
        [
            "pizza_name_id",
            "pizza_ingredients",
            "Items_Qty_In_Grams"
        ]
    ],
    left_on="item_id",
    right_on="pizza_name_id",
    how="left",
    validate="many_to_many"
)

missing_recipes_2016 = validated_details.loc[
    validated_details["pizza_ingredients"].isna(),
    "item_id"
].unique()

if len(missing_recipes_2016) > 0:
    raise ValueError(
        f"Missing recipes: {missing_recipes_2016}"
    )

validated_details["required_grams"] = (
    validated_details["prep_quantity"]
    * validated_details["Items_Qty_In_Grams"]
)

validated_preparation = (
    validated_details.groupby(
        [
            "timestamp",
            "pizza_ingredients"
        ],
        as_index=False
    )["required_grams"]
    .sum()
    .rename(
        columns={
            "pizza_ingredients": "ingredient"
        }
    )
)


# Prepare the 2015 historical data

historical_2015 = history.copy()

historical_2015["actual_quantity"] = (
    historical_2015["target"]
)


# Convert historical sales into ingredient requirements

historical_details = historical_2015[
    [
        "item_id",
        "timestamp",
        "actual_quantity"
    ]
].merge(
    recipes[
        [
            "pizza_name_id",
            "pizza_ingredients",
            "Items_Qty_In_Grams"
        ]
    ],
    left_on="item_id",
    right_on="pizza_name_id",
    how="left",
    validate="many_to_many"
)

missing_recipes_2015 = historical_details.loc[
    historical_details["pizza_ingredients"].isna(),
    "item_id"
].unique()

if len(missing_recipes_2015) > 0:
    raise ValueError(
        f"Missing recipes: {missing_recipes_2015}"
    )

historical_details["required_grams"] = (
    historical_details["actual_quantity"]
    * historical_details["Items_Qty_In_Grams"]
)

historical_preparation = (
    historical_details.groupby(
        [
            "timestamp",
            "pizza_ingredients"
        ],
        as_index=False
    )["required_grams"]
    .sum()
    .rename(
        columns={
            "pizza_ingredients": "ingredient"
        }
    )
)


# Prepare the 2015 inventory

inventory_2015 = inventory.copy()

inventory_2015["ingredient"] = inventory_2015[
    "ingredient"
].replace(
    {"Nduja Salami": "N'duja Salami"}
)


# Return preparation requirements for a date or period

def get_preparation(start_date, end_date=None):

    start_date = pd.Timestamp(start_date)

    if end_date is None:
        end_date = start_date
    else:
        end_date = pd.Timestamp(end_date)

    if end_date < start_date:
        return {
            "status": "error",
            "message": (
                "End date cannot be earlier "
                "than start date."
            )
        }

    if start_date.year != end_date.year:
        return {
            "status": "error",
            "message": (
                "The requested period cannot cross "
                "between 2015 and 2016."
            )
        }

    if start_date.year == 2015:
        source_data = historical_preparation
        source_label = "historical"

    elif start_date.year == 2016:
        source_data = validated_preparation
        source_label = "forecast"

    else:
        return {
            "status": "error",
            "message": (
                "Only 2015 historical data and "
                "2016 forecast data are available."
            )
        }

    period_data = source_data.loc[
        source_data["timestamp"].between(
            start_date,
            end_date
        )
    ].copy()

    available_dates = set(
        period_data["timestamp"]
    )

    if not available_dates:
        return {
            "status": "error",
            "message": (
                "No data are available for the "
                "requested date or period."
            )
        }

    expected_dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D"
    )

    missing_dates = [
        date.strftime("%Y-%m-%d")
        for date in expected_dates
        if date not in available_dates
    ]

    if missing_dates:
        return {
            "status": "error",
            "message": (
                "Some requested dates are outside "
                "the available data."
            ),
            "missing_dates": missing_dates
        }

    preparation = (
        period_data.groupby(
            "ingredient",
            as_index=False
        )["required_grams"]
        .sum()
        .sort_values("ingredient")
        .reset_index(drop=True)
    )

    preparation["required_kg"] = (
        preparation["required_grams"] / 1000
    )

    return {
        "status": "ok",
        "source": source_label,
        "start_date": start_date.strftime(
            "%Y-%m-%d"
        ),
        "end_date": end_date.strftime(
            "%Y-%m-%d"
        ),
        "days": len(available_dates),
        "preparation": preparation
    }


# Return ordering requirements for a date or period

def get_ordering(
    start_date,
    end_date=None,
    stock_adjustments=None
):

    start_date = pd.Timestamp(start_date)

    if end_date is None:
        end_date = start_date
    else:
        end_date = pd.Timestamp(end_date)

    prep_result = get_preparation(
        start_date,
        end_date
    )

    if prep_result["status"] != "ok":
        return prep_result

    preparation = prep_result[
        "preparation"
    ].copy()

    # For more than one day, use zero available inventory
    if start_date != end_date:

        order = preparation.copy()

        order["stock_grams"] = 0

        order["order_grams"] = (
            order["required_grams"]
        )

        order["order_kg"] = (
            order["order_grams"] / 1000
        )

        return {
            "status": "ok",
            "source": prep_result["source"],
            "start_date": prep_result[
                "start_date"
            ],
            "end_date": prep_result[
                "end_date"
            ],
            "days": prep_result["days"],
            "inventory_assumption": "zero",
            "warning": (
                "This order assumes zero "
                "available inventory."
            ),
            "ordering": order
        }

    # For one day, use the inventory for that date
    if start_date.year == 2015:
        inventory_source = inventory_2015

    elif start_date.year == 2016:
        inventory_source = inventory_2016

    else:
        return {
            "status": "error",
            "message": (
                "Inventory is not available "
                "for the requested year."
            )
        }

    daily_stock = inventory_source.loc[
        inventory_source["order_date"]
        == start_date,
        [
            "ingredient",
            "stock_grams"
        ]
    ].copy()

    order = preparation.merge(
        daily_stock,
        on="ingredient",
        how="left",
        validate="one_to_one"
    )

    if order["stock_grams"].isna().any():
        return {
            "status": "error",
            "message": (
                "Inventory data are incomplete "
                "for the requested date."
            )
        }

    # Apply stock changes only to this calculation
    if stock_adjustments:

        for ingredient, new_stock in (
            stock_adjustments.items()
        ):

            if ingredient in order[
                "ingredient"
            ].values:

                order.loc[
                    order["ingredient"]
                    == ingredient,
                    "stock_grams"
                ] = float(new_stock)

    order["order_grams"] = (
        order["required_grams"]
        - order["stock_grams"]
    ).clip(lower=0)

    order["order_kg"] = (
        order["order_grams"] / 1000
    )

    return {
        "status": "ok",
        "source": prep_result["source"],
        "start_date": prep_result[
            "start_date"
        ],
        "end_date": prep_result[
            "end_date"
        ],
        "days": 1,
        "inventory_assumption": (
            "daily_inventory"
        ),
        "ordering": order
    }


# Months used when reading dates from questions

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12
}


# Convert a written or numeric date into the format used by the backend

def parse_date(text, default_year=2016):

    text = unicodedata.normalize(
        "NFKC",
        text.lower().strip()
    )

    normalized = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    month_pattern = "|".join(MONTHS)

    match = re.fullmatch(
        rf"(\d{{1,2}})\s+"
        rf"({month_pattern})"
        rf"(?:\s+(\d{{2}}|\d{{4}}))?",
        normalized
    )

    if match:

        day, month, year = match.groups()
        month = MONTHS[month]

    else:

        match = re.fullmatch(
            rf"({month_pattern})\s+"
            rf"(\d{{1,2}})"
            rf"(?:\s+(\d{{2}}|\d{{4}}))?",
            normalized
        )

        if match:

            month, day, year = match.groups()
            month = MONTHS[month]

        else:

            match = re.fullmatch(
                r"(\d{1,2})[/-](\d{1,2})"
                r"(?:[/-](\d{2}|\d{4}))?",
                normalized
            )

            if match:
                day, month, year = match.groups()

            elif re.fullmatch(
                r"\d{4}",
                normalized
            ):
                day = normalized[:2]
                month = normalized[2:]
                year = None

            elif re.fullmatch(
                r"\d{8}",
                normalized
            ):
                day = normalized[:2]
                month = normalized[2:4]
                year = normalized[4:]

            else:
                return None

    year = (
        int(year)
        if year
        else default_year
    )

    if year < 100:
        year += 2000

    try:
        return datetime(
            year,
            int(month),
            int(day)
        ).strftime("%Y-%m-%d")

    except ValueError:
        return None


# Find a specific date inside a question

def extract_date_from_question(question):

    month_pattern = "|".join(MONTHS)

    patterns = [
        (
            rf"\b\d{{1,2}}\s+"
            rf"(?:{month_pattern})"
            rf"(?:\s+\d{{2,4}})?\b"
        ),
        (
            rf"\b(?:{month_pattern})\s+"
            rf"\d{{1,2}}"
            rf"(?:\s*,?\s*\d{{4}})?\b"
        ),
        (
            r"\b\d{1,2}[/-]\d{1,2}"
            r"(?:[/-]\d{2,4})?\b"
        ),
        r"\b(?:\d{8}|\d{4})\b"
    ]

    text = question.lower()

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:

            date_text = (
                match.group()
                .replace(",", " ")
            )

            return parse_date(
                date_text
            )

    return None


# Interpret relative dates using a simulation reference date

def parse_relative_date(
    text,
    reference_date=None
):

    text = text.lower().strip()

    relative_terms = {
        "today",
        "tomorrow",
        "next week",
        "this weekend"
    }

    if text not in relative_terms:
        return None

    if reference_date is None:
        return "Reference date required"

    reference = pd.Timestamp(
        reference_date
    )

    if text == "today":

        start = reference
        end = reference

    elif text == "tomorrow":

        start = (
            reference
            + timedelta(days=1)
        )
        end = start

    elif text == "next week":

        start = (
            reference
            + timedelta(
                days=7 - reference.weekday()
            )
        )

        end = (
            start
            + timedelta(days=6)
        )

    else:

        start = (
            reference
            + timedelta(
                days=(
                    5 - reference.weekday()
                ) % 7
            )
        )

        end = (
            start
            + timedelta(days=1)
        )

    return (
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d")
    )


# Find a date range inside a question

def extract_date_range(question):

    text = question.lower()
    month_pattern = "|".join(MONTHS)

    pattern = (
        rf"\b(?:from\s+)?"
        rf"(\d{{1,2}})\s*"
        rf"(?:to|-)\s*"
        rf"(\d{{1,2}})\s+"
        rf"({month_pattern})"
        rf"(?:\s+(\d{{4}}))?\b"
    )

    match = re.search(
        pattern,
        text
    )

    if not match:
        return None

    start_day, end_day, month, year = (
        match.groups()
    )

    year = year or "2016"

    start = parse_date(
        f"{start_day} {month} {year}"
    )

    end = parse_date(
        f"{end_day} {month} {year}"
    )

    if start is None or end is None:
        return None

    if start > end:
        return None

    return start, end


# Find ranges between months or requests for a complete month

def extract_extended_date_range(question):

    text = question.lower().strip()
    month_pattern = "|".join(MONTHS)

    cross_month_pattern = (
        rf"\b(?:from\s+)?"
        rf"(\d{{1,2}})\s+"
        rf"({month_pattern})"
        rf"\s+(?:to|-)\s+"
        rf"(\d{{1,2}})\s+"
        rf"({month_pattern})"
        rf"(?:\s+(\d{{4}}))?\b"
    )

    match = re.search(
        cross_month_pattern,
        text
    )

    if match:

        day1, month1, day2, month2, year = (
            match.groups()
        )

        year = year or "2016"

        start = parse_date(
            f"{day1} {month1} {year}"
        )

        end = parse_date(
            f"{day2} {month2} {year}"
        )

        if (
            start is None
            or end is None
            or start > end
        ):
            return None

        return start, end

    if re.search(
        r"\bfrom\s+\d{1,2}\b",
        text
    ):
        return None

    month_pattern_full = (
        rf"\b({month_pattern})"
        rf"(?:\s+(\d{{4}}))?\b"
    )

    match = re.search(
        month_pattern_full,
        text
    )

    if not match:
        return None

    month_name, year = match.groups()

    month = MONTHS[month_name]

    year = (
        int(year)
        if year
        else 2016
    )

    last_day = calendar.monthrange(
        year,
        month
    )[1]

    start = (
        f"{year:04d}-"
        f"{month:02d}-01"
    )

    end = (
        f"{year:04d}-"
        f"{month:02d}-"
        f"{last_day:02d}"
    )

    return start, end


# Normalise text before reading a question

def normalize_text(text):

    text = str(
        text
    ).lower().strip()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        char
        for char in text
        if unicodedata.category(
            char
        ) != "Mn"
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# Connect a user question to preparation or ordering

def process_question(
    question,
    reference_date=None
):

    text = normalize_text(
        question
    )

    preparation_words = [
        "prepare",
        "preparation",
        "prep"
    ]

    ordering_words = [
        "order",
        "ordering"
    ]

    if any(
        word in text
        for word in ordering_words
    ):
        intent = "ordering"

    elif any(
        word in text
        for word in preparation_words
    ):
        intent = "preparation"

    else:
        return {
            "status": "clarification",
            "message": (
                "Please specify whether you want "
                "preparation or ordering information."
            )
        }

    relative_terms = [
        "today",
        "tomorrow",
        "next week",
        "this weekend"
    ]

    relative_match = None

    for term in relative_terms:

        if term in text:
            relative_match = term
            break

    if relative_match is not None:

        relative_result = parse_relative_date(
            relative_match,
            reference_date=reference_date
        )

        if (
            relative_result
            == "Reference date required"
        ):
            return {
                "status": "clarification",
                "message": (
                    "A simulation reference date "
                    "is required for relative dates."
                )
            }

        if relative_result is None:
            return {
                "status": "clarification",
                "message": (
                    "I could not understand "
                    "the relative date."
                )
            }

        start_date, end_date = (
            relative_result
        )

    else:

        start_date = None
        end_date = None

        range_markers = [
            " from ",
            " to ",
            "whole month"
        ]

        padded_text = f" {text} "

        has_range_marker = any(
            marker in padded_text
            for marker in range_markers
        )

        if has_range_marker:

            date_range = (
                extract_extended_date_range(
                    question
                )
            )

            if date_range is None:

                date_range = (
                    extract_date_range(
                        question
                    )
                )

            if date_range is not None:

                start_date, end_date = (
                    date_range
                )

        if start_date is None:

            specific_date = (
                extract_date_from_question(
                    question
                )
            )

            if specific_date is not None:

                start_date = specific_date
                end_date = specific_date

        if start_date is None:

            month_range = (
                extract_extended_date_range(
                    question
                )
            )

            if month_range is not None:

                start_date, end_date = (
                    month_range
                )

        if start_date is None:

            return {
                "status": "clarification",
                "message": (
                    "Please specify the date or "
                    "period you want to use."
                )
            }

    if intent == "preparation":

        result = get_preparation(
            start_date,
            end_date
        )

    else:

        result = get_ordering(
            start_date,
            end_date
        )

    result["intent"] = intent
    result["question"] = question

    return result

def interpret_user_question(question, reference_date=None, conversation_context=None):
    ingredient_list = ", ".join(ingredient_names)

    context = conversation_context or {}

    context_json = json.dumps(
        context,
        ensure_ascii=False
    )

    prompt = f"""
You interpret natural-language requests for a commercial kitchen assistant.

Your task is to identify what the chef wants.
Do not calculate quantities or invent data.

Available ingredients:
{ingredient_list}

Previous conversation context:
{context_json}

Simulation reference date:
{reference_date}

Rules:
1. Intent can be "preparation", "ordering", "both", or null.
2. If the chef asks for both preparation and ordering, use "both".
2a. If the chef replies "both", interpret the intent as "both".
2b. If the chef replies "prep" or "preparation", use "preparation".
2c. If the chef replies "order" or "ordering", use "ordering".
2d. A short reply to a clarification question is a valid request.
    Preserve the previous date or date range when it is not repeated.
3. If the current message is a follow-up, use the previous context to
   complete the request.
4. A new explicit request overrides conflicting previous information.
5. Never invent a missing intent or date.
6. The available years are 2015 and 2016.
7. For a new request without a year, use 2016.
8. Interpret numeric dates using New Zealand format DD/MM/YYYY.
9. Return dates in DD/MM/YYYY format.
10. If only one date is requested, use it for both start_date and end_date.
11. If the chef specifies an exact available ingredient, use its exact name.
12. If an ingredient contains a likely typo, suggest the closest available
    ingredient and request confirmation.
13. If several ingredients match, provide ingredient_options and request
    confirmation. Do not choose without confirmation.
14. If the chef selects an ingredient from a previous clarification,
    preserve the previous intent and dates.
15. Understand replies such as "the first one", "the second one",
    or an exact ingredient name using the previous ingredient_options.
16. If no ingredient is requested, ingredient_candidate may be null.
16a. If the chef does not mention a specific ingredient, include all ingredients.
16b. Do not ask which ingredient the chef wants unless the chef explicitly
     requested an ingredient that needs clarification.
16c. When no ingredient is specified, set ingredient_candidate to null
     and needs_confirmation to false.
17. Never invent an ingredient.
18. Relative dates such as today, tomorrow, yesterday, next week, and
    this weekend require a simulation reference date.
19. If a relative date is used without a reference date, ask for it.
20. If required information is missing, request clarification.
21. Return valid JSON only.

Return exactly these fields:

intent
start_date
end_date
ingredient_text
ingredient_candidate
ingredient_options
needs_confirmation
clarification_message

User message:
{question}
"""

    response = gemini_client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    response_text = response.text.strip()

    if response_text.startswith("```json"):
        response_text = response_text[7:]

    if response_text.endswith("```"):
        response_text = response_text[:-3]

    return json.loads(response_text.strip())

def validate_ai_interpretation(result):
    intent = result.get("intent")

    if intent not in ["preparation", "ordering", "both"]:
        return {
            "valid": False,
            "needs_clarification": True,
            "message": (
                "Would you like to check preparation, "
                "ordering, or both?"
            ),
            "interpretation": result
        }

    start_date_text = result.get("start_date")
    end_date_text = result.get("end_date")

    if not start_date_text:
        return {
            "valid": False,
            "needs_clarification": True,
            "message": result.get("clarification_message")
            or "Which date would you like to check?",
            "interpretation": result
        }

    if not end_date_text:
        end_date_text = start_date_text

    try:
        start_date = pd.to_datetime(
            start_date_text,
            format="%d/%m/%Y"
        )

        end_date = pd.to_datetime(
            end_date_text,
            format="%d/%m/%Y"
        )

    except (ValueError, TypeError):
        return {
            "valid": False,
            "needs_clarification": True,
            "message": (
                "I couldn't understand that date. "
                "Could you write it as 8 April or 08/04/2016?"
            ),
            "interpretation": result
        }

    if start_date.year not in [2015, 2016] or end_date.year not in [2015, 2016]:
        return {
            "valid": False,
            "message": (
                "I have recorded sales for 2015 and "
                "estimated kitchen requirements for 2016."
            ),
            "interpretation": result
        }

    if start_date.year != end_date.year:
        return {
            "valid": False,
            "message": (
                "Please choose dates within the same year."
            ),
            "interpretation": result
        }

    if end_date < start_date:
        return {
            "valid": False,
            "message": (
                "The end date must be after the start date."
            ),
            "interpretation": result
        }

    result["start_date"] = start_date.strftime("%Y-%m-%d")
    result["end_date"] = end_date.strftime("%Y-%m-%d")

    candidate = result.get("ingredient_candidate")

    if candidate and candidate not in ingredient_names:
        return {
            "valid": False,
            "message": (
                "I couldn't find that ingredient in the kitchen data."
            ),
            "interpretation": result
        }

    if result.get("needs_confirmation"):
        return {
            "valid": False,
            "needs_confirmation": True,
            "message": result.get("clarification_message")
            or "Which ingredient did you mean?",
            "interpretation": result
        }

    return {
        "valid": True,
        "interpretation": result
    }


def process_ai_question(question, reference_date=None, conversation_context=None):
    context = conversation_context or {}

    interpretation = interpret_user_question(
        question,
        reference_date=reference_date,
        conversation_context=context
    )





    print("GEMINI INTERPRETATION:", interpretation)
    validation = validate_ai_interpretation(interpretation)

    # Preserve the interpreted request, even when clarification is needed.
    if not validation.get("valid"):
        updated_context = dict(context)



        for field in (
            "intent",
            "start_date",
            "end_date",
            "ingredient_text",
            "ingredient_candidate",
            "ingredient_options",
        ):
            value = interpretation.get(field)

            if value is not None:
                updated_context[field] = value

        validation["conversation_context"] = updated_context
        return validation

    interpretation = validation["interpretation"]

    intent = interpretation["intent"]
    start_date = interpretation["start_date"]
    end_date = interpretation["end_date"]
    ingredient = interpretation.get("ingredient_candidate")

    updated_context = {
        "intent": intent,
        "start_date": start_date,
        "end_date": end_date,
        "ingredient_text": interpretation.get("ingredient_text"),
        "ingredient_candidate": ingredient,
        "ingredient_options": [],
    }

    if intent == "preparation":
        result = get_preparation(
            start_date,
            end_date
        )

        if result.get("status") != "ok":
            result["conversation_context"] = updated_context
            return result

        if ingredient:
            preparation = result["preparation"]
            result["preparation"] = preparation[
                preparation["ingredient"] == ingredient
            ].reset_index(drop=True)

        result["conversation_context"] = updated_context
        return result

    if intent == "ordering":
        result = get_ordering(
            start_date,
            end_date
        )

        if result.get("status") != "ok":
            result["conversation_context"] = updated_context
            return result

        if ingredient:
            ordering = result["ordering"]
            result["ordering"] = ordering[
                ordering["ingredient"] == ingredient
            ].reset_index(drop=True)

        result["conversation_context"] = updated_context
        return result

    if intent == "both":
        preparation_result = get_preparation(
            start_date,
            end_date
        )

        if preparation_result.get("status") != "ok":
            preparation_result["conversation_context"] = updated_context
            return preparation_result

        ordering_result = get_ordering(
            start_date,
            end_date
        )

        if ordering_result.get("status") != "ok":
            ordering_result["conversation_context"] = updated_context
            return ordering_result

        if ingredient:
            preparation = preparation_result["preparation"]
            preparation_result["preparation"] = preparation[
                preparation["ingredient"] == ingredient
            ].reset_index(drop=True)

            ordering = ordering_result["ordering"]
            ordering_result["ordering"] = ordering[
                ordering["ingredient"] == ingredient
            ].reset_index(drop=True)

        return {
            "status": "ok",
            "source": preparation_result["source"],
            "start_date": preparation_result["start_date"],
            "end_date": preparation_result["end_date"],
            "days": preparation_result["days"],
            "preparation": preparation_result["preparation"],
            "ordering": ordering_result["ordering"],
            "warning": ordering_result.get("warning"),
            "conversation_context": updated_context,
        }

    return {
        "valid": False,
        "message": "The request could not be processed.",
        "conversation_context": updated_context,
    }
