"""Streamlit chatbot component for conversational invoice querying."""

import streamlit as st
import httpx
from typing import List, Dict
from uuid import UUID

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

# API base URL
API_BASE_URL = "http://localhost:8000/api/v1"


def render_chatbot_tab() -> None:
    """Render the chatbot tab in Streamlit dashboard."""
    st.header("💬 Chat with Invoices")
    st.markdown(
        "Ask questions about your invoices using natural language. "
        "For example: 'How many images did you train from dataset jimeng folder, and list the total cost?'"
    )

    # Initialize session state
    if "chatbot_session_id" not in st.session_state:
        # Create new session via API
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(f"{API_BASE_URL}/chatbot/sessions")
                if response.status_code == 201:
                    data = response.json()
                    st.session_state.chatbot_session_id = data["session_id"]
                else:
                    st.error("Failed to create chat session. Please refresh the page.")
                    return
        except Exception as e:
            st.error(f"Failed to connect to API: {str(e)}")
            st.info("Make sure the FastAPI server is running on port 8000")
            return

    if "chatbot_messages" not in st.session_state:
        st.session_state.chatbot_messages: List[Dict[str, str]] = []

    # Display chat history
    for message in st.session_state.chatbot_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            # Show invoice count if available
            if message.get("invoice_count", 0) > 0:
                st.caption(f"Found {message['invoice_count']} invoice(s)")

    # Chat input
    if prompt := st.chat_input("Ask a question about your invoices..."):
        # Add user message to history
        st.session_state.chatbot_messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Get response from API
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    with httpx.Client(timeout=30.0) as client:
                        response = client.post(
                            f"{API_BASE_URL}/chatbot/chat",
                            json={
                                "message": prompt,
                                "session_id": st.session_state.chatbot_session_id,
                                "language": "en",
                            },
                        )

                        if response.status_code == 200:
                            data = response.json()
                            st.write(data["message"])

                            # Add assistant message to history
                            st.session_state.chatbot_messages.append(
                                {
                                    "role": "assistant",
                                    "content": data["message"],
                                    "invoice_count": data.get("invoice_count", 0),
                                    "invoice_ids": data.get("invoice_ids", []),
                                }
                            )

                            # Show invoice details if available
                            if data.get("invoice_count", 0) > 0:
                                st.caption(f"Found {data['invoice_count']} invoice(s)")
                                if data.get("has_more", False):
                                    st.info("More results available. Try refining your query.")

                        elif response.status_code == 429:
                            error_data = response.json()
                            retry_after = response.headers.get("Retry-After", "60")
                            st.error(
                                f"Rate limit exceeded. Please wait {retry_after} seconds before asking more questions."
                            )

                        elif response.status_code == 400:
                            error_data = response.json()
                            st.error(f"Invalid request: {error_data.get('detail', 'Unknown error')}")

                        else:
                            st.error("Failed to get response. Please try again.")
                            logger.error(
                                "Chatbot API error",
                                status_code=response.status_code,
                                response=response.text,
                            )

                except httpx.TimeoutException:
                    st.error("Request timed out. The server may be processing a complex query. Please try again.")
                except httpx.ConnectError:
                    st.error("Failed to connect to API. Make sure the FastAPI server is running.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    logger.error("Chatbot error", error=str(e))
