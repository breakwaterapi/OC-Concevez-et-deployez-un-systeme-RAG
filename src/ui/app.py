import re

import httpx
import streamlit as st

from ui.config import get_ui_settings


def _to_md(text: str) -> str:
    """Force line breaks on single newlines (Markdown ignores them otherwise)."""
    return re.sub(r"\n(?!\n)", "  \n", text)


def _get_event_title(text: str) -> str:
    first_line = text.split("\n")[0].strip()
    return first_line[2:] if first_line.startswith("# ") else first_line


def _fetch_health(base_url: str, timeout: int) -> dict | None:
    try:
        with httpx.Client() as client:
            r = client.get(f"{base_url}/health", timeout=timeout)
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


def _fetch_metadata(base_url: str, timeout: int) -> dict | None:
    try:
        with httpx.Client() as client:
            r = client.get(f"{base_url}/metadata", timeout=timeout)
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


def _fetch_answer(base_url: str, timeout: int, question: str) -> dict | None:
    try:
        with httpx.Client() as client:
            r = client.post(
                f"{base_url}/ask",
                json={"question": question},
                timeout=timeout,
            )
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


def _fetch_document(base_url: str, timeout: int, uid: str) -> dict | None:
    try:
        with httpx.Client() as client:
            r = client.get(f"{base_url}/documents/{uid}", timeout=timeout)
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


def _rebuild_index(base_url: str, api_key: str) -> dict | None:
    try:
        with httpx.Client() as client:
            r = client.post(
                f"{base_url}/rebuild",
                headers={"X-API-Key": api_key},
                timeout=300,
            )
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


@st.dialog("Détail de l'événement", width="large")
def _show_source_dialog(source: dict) -> None:
    st.markdown(_to_md(source["text"]))


def _render_sources(msg_idx: int, sources: list[dict]) -> None:
    if not sources:
        return
    st.caption("Sources :")
    cols = st.columns(min(len(sources), 4))
    for i, source in enumerate(sources):
        title = _get_event_title(source["text"])
        label = title[:30] + ("…" if len(title) > 30 else "")
        with cols[i % len(cols)]:
            if st.button(label, key=f"src_{msg_idx}_{i}", help=title, use_container_width=True):
                _show_source_dialog(source)


def _render_sidebar(base_url: str, timeout: int, rebuild_api_key: str) -> None:
    with st.sidebar:
        st.header("Santé de l'API")

        health = st.session_state.health
        metadata = st.session_state.metadata
        if health is None:
            st.error("API indisponible")
            st.caption("Lancez : `uvicorn api.main:app --reload --port 8001`")
        else:
            status = health.get("status", "error")
            store_ready = health.get("store_ready", False)
            model_ready = health.get("model_ready", False)
            n_events = metadata.get("n_events", 0) if metadata else 0

            if status == "ok" and store_ready and model_ready:
                st.success(f"Opérationnel · {n_events} documents indexés")
            else:
                parts = []
                if not store_ready:
                    parts.append("index non prêt")
                if not model_ready:
                    parts.append("modèle non prêt")
                detail = " · ".join(parts) if parts else "statut dégradé"
                st.warning(f"Dégradé · {detail}")

        if st.button("Rafraîchir", key="refresh_health"):
            st.session_state.health = _fetch_health(base_url, timeout)
            st.session_state.metadata = _fetch_metadata(base_url, timeout)
            if st.session_state.health is None:
                st.toast("API indisponible", icon="🔴")
            st.rerun()

        st.divider()
        st.caption("Base vectorielle")
        if st.button("Reconstruire l'index", key="rebuild_index", use_container_width=True):
            with st.spinner("Reconstruction de l'index en cours…"):
                result = _rebuild_index(base_url, rebuild_api_key)
            if result is None:
                st.toast("Échec de la reconstruction de l'index", icon="🔴")
            else:
                st.toast(result.get("message", "Index reconstruit."), icon="✅")
                st.session_state.health = _fetch_health(base_url, timeout)
                st.session_state.metadata = _fetch_metadata(base_url, timeout)
            st.rerun()


def main() -> None:
    cfg = get_ui_settings()

    st.set_page_config(
        page_title="Événements culturels Île-de-France",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "health" not in st.session_state:
        st.session_state.health = _fetch_health(cfg.api_base_url, cfg.api_timeout)
        st.session_state.metadata = _fetch_metadata(cfg.api_base_url, cfg.api_timeout)
        if st.session_state.health is None:
            st.toast(
                "API indisponible — lancez uvicorn api.main:app --reload --port 8001", icon="🔴"
            )

    _render_sidebar(cfg.api_base_url, cfg.api_timeout, cfg.rebuild_api_key)

    st.title("Événements culturels en Île-de-France")
    st.caption("Posez une question sur les événements culturels de la région.")

    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                _render_sources(idx, msg.get("sources", []))

    if prompt := st.chat_input("Votre question…", max_chars=500):
        st.session_state.messages.append({"role": "user", "content": prompt, "sources": []})

        with st.spinner("Recherche en cours…"):
            result = _fetch_answer(cfg.api_base_url, cfg.api_timeout, prompt)

        if result is None:
            content = "L'API est indisponible. Lancez `uvicorn api.main:app --reload --port 8001`."
            sources: list[dict] = []
        else:
            content = result.get("answer") or "Aucune réponse disponible."
            sources = [
                doc
                for ref in (result.get("sources") or [])
                if (doc := _fetch_document(cfg.api_base_url, cfg.api_timeout, ref["uid"]))
            ]

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": content,
                "sources": sources,
            }
        )
        st.rerun()


if __name__ == "__main__":
    main()
