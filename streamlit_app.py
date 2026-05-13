#!/usr/bin/env python3
import os
import re
from pathlib import Path
import streamlit as st
from streamlit.components.v1 import html as components_html


def inline_frontend():
    # Prefer the frontend folder by default; fall back to backend static.
    repo_root = Path(__file__).parent
    candidates = [repo_root / "frontend", repo_root / "backend" / "app" / "static"]
    base = next((p for p in candidates if p.exists()), candidates[0])
    index = base / "index.html"
    if not index.exists():
        st.error(f"index.html not found in {base}")
        return ""
    html = index.read_text(encoding="utf-8")

    def read_file(rel_path: str) -> str:
        # Normalize paths: strip query string and leading slash/static prefix
        rel = rel_path.split("?")[0]
        rel = rel.lstrip("/")
        if rel.startswith("static/"):
            rel = rel[len("static/"):]
        p = base / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    # Inline CSS files referenced with <link rel="stylesheet" href="...">
    html = re.sub(
        r'<link\s+rel=["\']stylesheet["\']\s+href=["\'](?P<h>[^"\']+)["\']\s*/?>',
        lambda m: f"<style>{read_file(m.group('h'))}</style>",
        html,
    )

    # Inline JS files referenced with <script src="..."></script>
    html = re.sub(
        r'<script\s+src=["\'](?P<s>[^"\']+)["\']\s*>\s*</script>',
        lambda m: f"<script>{read_file(m.group('s'))}</script>",
        html,
    )

    return html


def main():
    st.set_page_config(page_title="Startup Pitch Evaluation", layout="wide")
    st.sidebar.title("Startup Pitch Evaluation")
    st.sidebar.markdown("This Streamlit wrapper serves the existing frontend or backend static site.")
    st.sidebar.caption("Default: serving `frontend/` if present.")
    html_content = inline_frontend()

    # Allow configuring the backend API root via env var or Streamlit secrets.
    api_url = os.getenv("STREAMLIT_API_URL", "") or st.secrets.get("api_url", "")

    # If an API URL is provided, inject a small JS shim that prefixes relative
    # fetch calls (like "/evaluate") with the configured API root. This lets
    # the frontend continue using relative paths while Streamlit proxies them
    # to the real backend.
    if html_content:
        if api_url:
            shim_template = """
<script>
(function(){
    const API_URL = "__API_URL__";
    if(API_URL){
        const orig = window.fetch.bind(window);
        window.fetch = function(input, init){
            try {
                if(typeof input === 'string' && input.startsWith('/')) {
                    input = API_URL.replace(/\/$/, '') + input;
                } else if (input instanceof Request) {
                    const url = new URL(input.url);
                    if(url.origin === window.location.origin && url.pathname.startsWith('/')) {
                        input = new Request(API_URL.replace(/\/$/, '') + url.pathname + url.search, input);
                    }
                }
            } catch(e){}
            return orig(input, init);
        };
    }
})();
</script>
"""
            shim = shim_template.replace("__API_URL__", api_url)
            # insert shim before closing </head> if present, otherwise prepend
            if re.search(r'</head>', html_content, flags=re.IGNORECASE):
                html_content = re.sub(r'</head>', shim + '\n</head>', html_content, flags=re.IGNORECASE)
            else:
                html_content = shim + html_content

        components_html(html_content, height=900, scrolling=True)


if __name__ == "__main__":
    main()
