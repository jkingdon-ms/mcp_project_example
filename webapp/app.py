"""
Streamlit chatbot webapp backed by the MCP client.

Run with:
    streamlit run webapp/app.py [-- --start-api-server]
"""
import argparse
import asyncio

import requests
import streamlit as st

from mcp_client.mcp_client import MCPClient
from shared.api.api_server_manager import ApiServerManager

API_BASE = "http://localhost:8080/v2"

st.set_page_config(page_title="Petstore Assistant", page_icon="🐾")
st.title("🐾 Petstore Assistant")
st.caption("Ask me anything about the Petstore — pets, orders, and users.")


# ── process-scoped init (runs once per server process) ────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-api-server", action="store_true",
                        help="Start the API server automatically")
    args, _ = parser.parse_known_args()
    return args


@st.cache_resource
def _init() -> tuple[MCPClient, asyncio.AbstractEventLoop]:
    args = _parse_args()
    if args.start_api_server:
        ApiServerManager().start()
    loop = asyncio.new_event_loop()
    client = MCPClient()
    loop.run_until_complete(client.__aenter__())
    return client, loop


_mcp_client, _loop = _init()


# ── sidebar data panel ───────────────────────────────────────────────────────

@st.fragment(run_every=5)
def _data_panel() -> None:
    # Pets
    try:
        pets = []
        for status in ("available", "pending", "sold"):
            r = requests.get(f"{API_BASE}/pet/findByStatus",
                             params={"status": status}, timeout=2)
            if r.ok:
                pets.extend(r.json())
        pets.sort(key=lambda p: p["id"])
        st.markdown("**Pets**")
        if pets:
            st.dataframe(
                [{"ID": p["id"], "Name": p["name"],
                  "Category": (p.get("category") or {}).get("name", ""),
                  "Tags": ", ".join(t["name"] for t in (p.get("tags") or [])),
                  "Status": p["status"]} for p in pets],
                width="stretch", hide_index=True,
            )
        else:
            st.caption("No pets found")
    except Exception:
        st.caption("⚠️ Pets unavailable")


with st.sidebar:
    st.header("📋 Store Data")
    _data_panel()


# ── session state ────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    # {"role": "user"|"assistant", "content": str}
    st.session_state.messages = []


# ── helpers ──────────────────────────────────────────────────────────────────

def ask(question: str) -> str:
    result = _loop.run_until_complete(
        _mcp_client.process_question(question)
    )
    return result.nl_answer


# ── render chat history ───────────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── handle new input ──────────────────────────────────────────────────────────

if prompt := st.chat_input("Ask about pets, orders, or users…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                answer = ask(prompt)
            except Exception as e:
                answer = f"⚠️ Error: {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
