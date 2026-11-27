import io

import pandas as pd
import streamlit as st

from backend import process_ai_question


st.set_page_config(
    page_title="AI Commercial Kitchen Assistant",
    page_icon="🍽️",
    layout="wide"
)


# Session state

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = {}


# Helpers

def is_single_day(result):
    return result.get("start_date") == result.get("end_date")


def format_date(date_value):
    try:
        return pd.to_datetime(date_value).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(date_value)


def to_excel(sheets):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, dataframe in sheets.items():
            dataframe.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False
            )

    output.seek(0)
    return output.getvalue()


def show_result_context(result):
    source = result.get("source")
    start_date = format_date(result.get("start_date"))
    end_date = format_date(result.get("end_date"))

    if start_date == end_date:
        period = start_date
    else:
        period = f"{start_date} to {end_date}"

    if source == "forecast":
        st.info(
            f"Kitchen estimate for {period}"
        )

        st.caption(
            "These quantities are estimated using previous sales. "
            "Actual demand may be different."
        )

    elif source == "historical":
        st.info(
            f"Based on recorded sales for {period}"
        )


def display_preparation(result):
    preparation = result["preparation"].copy()

    preparation["Prepare (kg)"] = (
        preparation["required_grams"] / 1000
    ).round(2)

    display_data = preparation[
        [
            "ingredient",
            "Prepare (kg)"
        ]
    ].rename(
        columns={
            "ingredient": "Ingredient"
        }
    )

    st.subheader(
        "Preparation Requirements"
    )

    if result.get("source") == "forecast":
        st.warning(
            "These preparation quantities are estimates "
            "based on previous sales."
        )

        if is_single_day(result):
            st.caption(
                "Want to check what you need to buy? "
                "Ask for the order for the same day. "
                "You can then update the stock you currently "
                "have in the kitchen."
            )

    if len(display_data) == 1:
        row = display_data.iloc[0]

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Ingredient",
                row["Ingredient"]
            )

        with col2:
            st.metric(
                "Prepare",
                f'{row["Prepare (kg)"]:.2f} kg'
            )

    else:
        st.caption(
            f"{len(display_data)} ingredients are needed."
        )

        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True,
            height=min(
                700,
                38 * len(display_data) + 40
            )
        )

    excel_data = to_excel(
        {
            "Preparation": display_data
        }
    )

    st.download_button(
        "Download preparation list (Excel)",
        data=excel_data,
        file_name="preparation_requirements.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        key=(
            f"prep_download_{result.get('start_date')}_"
            f"{result.get('end_date')}"
        )
    )

    return display_data


def display_ordering(result):
    ordering = result["ordering"].copy()

    ordering["Required (kg)"] = (
        ordering["required_grams"] / 1000
    ).round(3)

    ordering["Available Stock (kg)"] = (
        ordering["stock_grams"] / 1000
    ).round(3)

    ordering["Order (kg)"] = (
        ordering["order_grams"] / 1000
    ).round(3)

    display_data = ordering[
        [
            "ingredient",
            "Required (kg)",
            "Available Stock (kg)",
            "Order (kg)"
        ]
    ].rename(
        columns={
            "ingredient": "Ingredient"
        }
    )

    st.subheader(
        "Ordering Requirements"
    )

    if result.get("warning"):
        if is_single_day(result):
            st.warning(
                result["warning"]
            )
        else:
            st.warning(
                "The stock currently available is not included "
                "for an order covering several days. "
                "This list shows the full amount needed "
                "for the selected period."
            )

    if (
        result.get("source") == "forecast"
        and is_single_day(result)
    ):
        st.warning(
            "Check the stock you actually have before placing "
            "the order. The stock shown below is an estimate."
        )

        st.caption(
            "Change any value in Available Stock (kg). "
            "The amount to buy will update automatically."
        )

        editable_data = display_data[
            [
                "Ingredient",
                "Required (kg)",
                "Available Stock (kg)"
            ]
        ].copy()

        edited_data = st.data_editor(
            editable_data,
            use_container_width=True,
            hide_index=True,
            disabled=[
                "Ingredient",
                "Required (kg)"
            ],
            column_config={
                "Ingredient":
                    st.column_config.TextColumn(
                        "Ingredient"
                    ),

                "Required (kg)":
                    st.column_config.NumberColumn(
                        "Required (kg)",
                        format="%.3f"
                    ),

                "Available Stock (kg)":
                    st.column_config.NumberColumn(
                        "Available Stock (kg)",
                        min_value=0.0,
                        format="%.3f"
                    )
            },
            key=(
                f"inventory_{result.get('start_date')}"
            )
        )

        edited_data["Order (kg)"] = (
            edited_data["Required (kg)"]
            - edited_data["Available Stock (kg)"]
        ).clip(
            lower=0
        ).round(3)

        display_data = edited_data

    if len(display_data) == 1:
        row = display_data.iloc[0]

        st.caption(
            row["Ingredient"]
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Needed",
                f'{row["Required (kg)"]:.3f} kg'
            )

        with col2:
            st.metric(
                "Stock available",
                f'{row["Available Stock (kg)"]:.3f} kg'
            )

        with col3:
            st.metric(
                "Buy",
                f'{row["Order (kg)"]:.3f} kg'
            )

        st.caption(
            "Buy = amount needed minus stock available. "
            "If you already have enough stock, Buy is 0 kg."
        )

    else:
        items_to_order = int(
            (
                display_data["Order (kg)"] > 0
            ).sum()
        )

        st.caption(
            f"{len(display_data)} ingredients checked. "
            f"{items_to_order} need to be ordered."
        )

        view_option = st.radio(
            "What would you like to see?",
            [
                "Only ingredients to buy",
                "All ingredients"
            ],
            horizontal=True,
            key=(
                f"order_filter_{result.get('start_date')}_"
                f"{result.get('end_date')}"
            )
        )

        if (
            view_option
            == "Only ingredients to buy"
        ):
            visible_data = display_data[
                display_data["Order (kg)"] > 0
            ].reset_index(
                drop=True
            )

        else:
            visible_data = display_data

        if visible_data.empty:
            st.success(
                "You already have enough stock "
                "for the ingredients shown."
            )

        else:
            st.dataframe(
                visible_data,
                use_container_width=True,
                hide_index=True,
                height=min(
                    700,
                    38 * len(visible_data) + 40
                )
            )

    excel_data = to_excel(
        {
            "Ordering": display_data
        }
    )

    st.download_button(
        "Download ordering list (Excel)",
        data=excel_data,
        file_name="ordering_requirements.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        key=(
            f"order_download_{result.get('start_date')}_"
            f"{result.get('end_date')}"
        )
    )

    return display_data


def display_combined_download(
    result,
    preparation_data,
    ordering_data
):
    excel_data = to_excel(
        {
            "Preparation": preparation_data,
            "Ordering": ordering_data
        }
    )

    st.download_button(
        "Download preparation and ordering lists (Excel)",
        data=excel_data,
        file_name="kitchen_requirements.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        key=(
            f"combined_download_{result.get('start_date')}_"
            f"{result.get('end_date')}"
        )
    )


def display_result(result):
    if result.get(
        "needs_confirmation"
    ):
        st.warning(
            result.get(
                "message",
                "Please confirm what you mean."
            )
        )

        interpretation = result.get(
            "interpretation",
            {}
        )

        options = interpretation.get(
            "ingredient_options",
            []
        )

        if options:
            st.write(
                "Please choose from these options:"
            )

            for option in options:
                st.write(
                    f"• {option}"
                )

        return

    if result.get("status") == "error":
        st.error(
            result.get(
                "message",
                "I could not complete that request."
            )
        )

        return

    if result.get("valid") is False:
        st.warning(
            result.get(
                "message",
                "I need a little more information."
            )
        )

        return

    has_preparation = (
        "preparation" in result
    )

    has_ordering = (
        "ordering" in result
    )

    if (
        not has_preparation
        and not has_ordering
    ):
        st.error(
            "I could not complete that request. "
            "Try asking what you need to prepare "
            "or buy."
        )

        return

    show_result_context(
        result
    )

    if (
        has_preparation
        and has_ordering
    ):
        preparation_data = display_preparation(
            result
        )

        ordering_data = display_ordering(
            result
        )

    elif has_preparation:
        display_preparation(
            result
        )

    elif has_ordering:
        display_ordering(
            result
        )


def process_question(question):
    try:
        return process_ai_question(
            question,
            conversation_context=st.session_state.conversation_context
        )

    except Exception:
        return {
            "valid": False,
            "message": (
                "I could not process that request right now. "
                "Please try again."
            )
        }


# Header

st.title("AI Commercial Kitchen Assistant")

st.write(
    "Ask what you need to prepare "
    "or buy for the kitchen."
)

st.caption(
    "Available information: recorded sales from 2015 "
    "and kitchen estimates for 2016."
)


# Conversation history

for message in st.session_state.messages:
    with st.chat_message(
        message["role"]
    ):
        st.write(
            message["content"]
        )


# Current result

if (
    st.session_state.last_result
    is not None
):
    with st.chat_message(
        "assistant"
    ):
        display_result(
            st.session_state.last_result
        )


# User input

# Fixed bottom row: chat input and Clear chat side by side.
st.markdown(
    """
    <style>
    .st-key-chat_toolbar {
        position: fixed !important;
        bottom: 0.75rem !important;
        left: 4% !important;
        width: 92% !important;
        z-index: 999 !important;
        background: var(--background-color, white) !important;
        padding: 0.45rem 0.65rem !important;
        border-radius: 0.8rem !important;
    }
    .st-key-chat_toolbar [data-testid="stChatInput"] {
        width: 100% !important;
    }
    .st-key-chat_toolbar [data-testid="stButton"] button {
        width: 100% !important;
        min-height: 2.75rem !important;
        white-space: nowrap !important;
    }
    /* Reserve space so the bottom row does not obscure results. */
    .block-container {
        padding-bottom: 7rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container(key="chat_toolbar"):
    chat_col, clear_col = st.columns([9, 1], gap="small", vertical_alignment="bottom")

    with chat_col:
        question = st.chat_input(
            "Example: What do I need to prepare "
            "and order for 17 June?"
        )

    with clear_col:
        if st.button("Clear chat", key="clear_chat_button"):
            st.session_state.messages = []
            st.session_state.last_result = None
            st.session_state.pending_question = None
            st.session_state.conversation_context = {}
            st.rerun()

if question:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.spinner(
        "Checking kitchen data..."
    ):
        result = process_question(
            question
        )

    if "conversation_context" in result:
        st.session_state.conversation_context = (
            result["conversation_context"]
        )

    st.session_state.last_result = result

    if (
        result.get("needs_confirmation")
        or result.get("valid") is False
    ):
        st.session_state.pending_question = question

    else:
        st.session_state.pending_question = None

    st.rerun()