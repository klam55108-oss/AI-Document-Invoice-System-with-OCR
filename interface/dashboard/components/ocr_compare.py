"""OCR provider comparison UI."""
from __future__ import annotations

import httpx
import streamlit as st


def render_ocr_compare_tab(api_base_url: str) -> None:
    """Render OCR comparison tab."""
    st.subheader("OCR Provider Comparison")
    st.caption("Run OCR with a selected provider or compare two providers side-by-side.")

    input_id = st.text_input("Input file (relative to data/)", value="sample.png")
    providers = _fetch_providers(api_base_url)

    if not providers:
        st.warning("No OCR providers available.")
        return

    provider_ids = [item["provider_id"] for item in providers]
    default_provider = next(
        (item["provider_id"] for item in providers if item.get("is_default")), provider_ids[0]
    )

    col_run, col_compare = st.columns(2)
    with col_run:
        selected_provider = st.selectbox("Provider", provider_ids, index=provider_ids.index(default_provider))
        if st.button("Run OCR"):
            _run_ocr(api_base_url, input_id, selected_provider)

    with col_compare:
        provider_a = st.selectbox("Provider A", provider_ids, index=0, key="provider_a")
        provider_b = st.selectbox("Provider B", provider_ids, index=1 if len(provider_ids) > 1 else 0, key="provider_b")
        if st.button("Compare"):
            _compare_ocr(api_base_url, input_id, provider_a, provider_b)


def _fetch_providers(api_base_url: str) -> list[dict]:
    try:
        response = httpx.get(f"{api_base_url}/api/v1/ocr/providers", timeout=10)
        response.raise_for_status()
        payload = response.json()
        return payload.get("data", [])
    except Exception as exc:
        st.error(f"Failed to load providers: {exc}")
        return []


def _run_ocr(api_base_url: str, input_id: str, provider_id: str) -> None:
    try:
        response = httpx.post(
            f"{api_base_url}/api/v1/ocr/run",
            json={"input_id": input_id, "provider_id": provider_id},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()["data"]
        st.success(f"OCR completed: {payload['provider_id']}")
        st.text_area("Extracted text", payload.get("extracted_text", ""), height=200)
        st.json(payload.get("extracted_fields", {}))
    except Exception as exc:
        st.error(f"OCR failed: {exc}")


def _compare_ocr(api_base_url: str, input_id: str, provider_a: str, provider_b: str) -> None:
    try:
        response = httpx.post(
            f"{api_base_url}/api/v1/ocr/compare",
            json={
                "input_id": input_id,
                "provider_a_id": provider_a,
                "provider_b_id": provider_b,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()["data"]
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**{provider_a}**")
            if data.get("provider_a_result"):
                st.text_area("Text", data["provider_a_result"].get("extracted_text", ""), height=200, key="text_a")
                st.json(data["provider_a_result"].get("extracted_fields", {}))
            else:
                st.info("No result for provider A.")
        with col_b:
            st.markdown(f"**{provider_b}**")
            if data.get("provider_b_result"):
                st.text_area("Text", data["provider_b_result"].get("extracted_text", ""), height=200, key="text_b")
                st.json(data["provider_b_result"].get("extracted_fields", {}))
            else:
                st.info("No result for provider B.")
    except Exception as exc:
        st.error(f"Comparison failed: {exc}")
