#!/usr/bin/env python3
"""Streamlit Cloud Dashboard for Edge AI Pitch Evaluation System.

This dashboard reads evaluated pitch results from Firebase and displays them
in real-time. It does NOT call the local backend directly, making it suitable
for Streamlit Cloud deployment while the backend runs on a local edge device.

The edge device processes videos locally and uploads results to Firebase,
which this dashboard then visualizes.
"""

import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_firebase():
    """Initialize Firebase connection from Streamlit secrets."""
    try:
        if not firebase_admin._apps:
            firebase_config = dict(st.secrets.get("firebase", {}))
            if not firebase_config:
                logger.error("Firebase configuration not found in secrets")
                return None
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized from Streamlit secrets")
        return firestore.client()
    except Exception:
        logger.exception("Firebase initialization failed")
        st.error("Firebase Error: initialization failed")
        return None


def load_results(db, limit: int = 50) -> pd.DataFrame:
    """Load recent pitch evaluations from Firebase.
    
    Args:
        db: Firestore database client
        limit: Maximum number of results to retrieve
    
    Returns:
        DataFrame with evaluation results
    """
    try:
        docs = (
            db.collection("pitch_evaluations")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )

        rows = []
        for doc in docs:
            data = doc.to_dict()
            result = data.get("result", {})
            summary = result.get("summary", {})
            dashboard = result.get("dashboard", {})

            rows.append({
                "timestamp": data.get("timestamp", "N/A"),
                "video_title": data.get("video_title") or result.get("request_id", "N/A"),
                "overall_score": summary.get("overall_score", 0),
                "confidence_score": summary.get("confidence_score", 0),
                "investment_band": summary.get("investment_band", "Unknown"),
                "language_detected": summary.get("language_detected", "N/A"),
                "scoring_mode": summary.get("scoring_mode", "N/A"),
                "strengths": ", ".join(summary.get("strengths", [])) or "None",
                "weaknesses": ", ".join(summary.get("weaknesses", [])) or "None",
                "suggestions": ", ".join(summary.get("suggestions", [])) or "None",
                "quantitative_scores": dashboard.get("quantitative_scores", []),
                "modality_weights": dashboard.get("modality_weights", []),
                "risk_distribution": dashboard.get("risk_distribution", []),
                "request_id": result.get("request_id", "N/A"),
            })

        return pd.DataFrame(rows)

    except Exception:
        logger.exception("Failed to load results")
        return pd.DataFrame()


def create_score_chart(scores_list: list) -> dict:
    """Convert Pydantic score list to chart format.
    
    Args:
        scores_list: List of DashboardSeriesPoint objects
    
    Returns:
        Dictionary for st.bar_chart
    """
    if isinstance(scores_list, list) and len(scores_list) > 0:
        if isinstance(scores_list[0], dict):
            return {item.get("label", "N/A"): item.get("value", 0) for item in scores_list}
        else:
            return {item.label: item.value for item in scores_list}
    return {}


def format_investment_band(band: str) -> tuple:
    """Format investment band with color and emoji.
    
    Args:
        band: Investment band string (e.g., "high-potential")
    
    Returns:
        Tuple of (label, color)
    """
    band_map = {
        "high-potential": ("🟢 High Potential", "#2ECC71"),
        "medium-potential": ("🟡 Medium Potential", "#F39C12"),
        "low-potential": ("🔴 Low Potential", "#E74C3C"),
        "not-suitable": ("⚠️ Not Suitable", "#C0392B"),
    }
    return band_map.get(band.lower() if isinstance(band, str) else "", ("❓ Unknown", "#95A5A6"))


def inject_styles():
    """Inject dashboard-specific styling."""
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.25rem;
                padding-bottom: 2rem;
                max-width: 1280px;
            }

            .hero-shell {
                padding: 1.2rem 1.5rem 1rem;
                border-radius: 14px;
                background: linear-gradient(90deg, #0b2545 0%, #153f7a 100%);
                color: #ffffff;
                border: 1px solid rgba(255,255,255,0.06);
                box-shadow: 0 10px 30px rgba(2,6,23,0.6);
                margin-bottom: 1rem;
            }

            .hero-title {
                margin: 0;
                font-size: 2.15rem;
                line-height: 1.05;
                letter-spacing: -0.03em;
                font-weight: 800;
            }

            .hero-subtitle {
                margin-top: 0.45rem;
                font-size: 0.98rem;
                color: rgba(226, 232, 240, 0.92);
            }

            .hero-meta {
                display: flex;
                flex-wrap: wrap;
                gap: 0.55rem;
                margin-top: 0.9rem;
            }

            .pill {
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                padding: 0.35rem 0.7rem;
                border-radius: 999px;
                font-size: 0.82rem;
                font-weight: 600;
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.06);
                color: #e6eef8;
            }

            .metric-card {
                padding: 0.9rem 1rem 0.9rem;
                border-radius: 12px;
                background: rgba(7,10,14,0.55); /* translucent dark panel */
                border: 1px solid rgba(255,255,255,0.03);
                box-shadow: 0 8px 30px rgba(2,6,23,0.6);
                height: 100%;
                color: #e6eef8;
            }

            .metric-label {
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #98a2b3;
                margin-bottom: 0.25rem;
                font-weight: 700;
            }

            .metric-value {
                font-size: 1.6rem;
                line-height: 1.05;
                font-weight: 800;
                color: #7dd3fc; /* light cyan accent */
            }

            .metric-footnote {
                margin-top: 0.35rem;
                color: #98a2b3;
                font-size: 0.86rem;
            }

            .section-shell {
                padding: 1rem 1.05rem;
                border-radius: 12px;
                background: rgba(10,14,18,0.48);
                border: 1px solid rgba(255,255,255,0.03);
                box-shadow: 0 6px 18px rgba(2,6,23,0.5);
                margin-bottom: 1rem;
                color: #e6eef8;
            }

            .section-title {
                margin: 0 0 0.2rem;
                font-size: 1.02rem;
                font-weight: 800;
                color: #e6eef8;
            }

            .section-subtitle {
                margin: 0;
                color: #98a2b3;
                font-size: 0.92rem;
            }

            .video-badge {
                display: inline-block;
                margin-top: 0.4rem;
                padding: 0.36rem 0.68rem;
                border-radius: 999px;
                background: rgba(125,211,252,0.08);
                color: #7dd3fc;
                border: 1px solid rgba(125,211,252,0.14);
                font-weight: 700;
                font-size: 0.9rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, footnote: str = ""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {f'<div class="metric-footnote">{footnote}</div>' if footnote else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_confidence_display(conf_val) -> str:
    try:
        conf_num = float(conf_val)
    except Exception:
        return "0.00%"

    return f"{conf_num:.2f}/10" if conf_num > 1 else f"{conf_num:.2%}"


def render_section_header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="section-shell">
            <h3 class="section-title">{title}</h3>
            {f'<p class="section-subtitle">{subtitle}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    """Main Streamlit dashboard application."""
    
    st.set_page_config(
        page_title="Startup Pitch Dashboard",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    inject_styles()

    st.markdown(
        """
        <div class="hero-shell">
            <h1 class="hero-title">Startup Pitch Edge AI Dashboard</h1>
            <div class="hero-subtitle">Real Time Pitch Evaluation Results</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar
    st.sidebar.title("Dashboard Settings")
    refresh_interval = st.sidebar.slider(
        "Refresh interval (seconds)",
        min_value=2,
        max_value=60,
        value=5
    )
    limit = st.sidebar.slider(
        "Number of results",
        min_value=5,
        max_value=100,
        value=20
    )
    # Initialize Firebase
    db = init_firebase()

    if db is None:
        st.error("Firebase connection failed. Check your secrets.toml configuration.")
        st.stop()

    # Main content area with auto-refresh
    placeholder = st.empty()
    last_update = st.empty()

    update_count = 0

    while True:
        try:
            with placeholder.container():
                df = load_results(db, limit=limit)

                if df.empty:
                    st.info("No pitch evaluations received yet. Waiting for edge device...")
                else:
                    latest = df.iloc[0]

                    latest_video = latest.get("video_title", "Unknown")
                    overall_score = float(latest.get("overall_score", 0) or 0)
                    conf_display = format_confidence_display(latest.get("confidence_score", 0))
                    band_label, _ = format_investment_band(latest["investment_band"])

                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                    with metric_col1:
                        render_metric_card("Overall Score", f"{overall_score:.1f}/10", "How strong the pitch scored overall")
                    with metric_col2:
                        render_metric_card("Confidence", conf_display, "Displayed as percentage or /10 depending on source")
                    with metric_col3:
                        render_metric_card("Investment Band", band_label, "Categorized from the evaluation summary")
                    with metric_col4:
                        render_metric_card("Language", str(latest["language_detected"]), f"Mode: {latest['scoring_mode']}")

                    st.markdown(f'<div class="video-badge">Video: {latest_video}</div>', unsafe_allow_html=True)

                    overview_tab, history_tab, trend_tab = st.tabs(["Overview", "Recent Evaluations", "Trends"])

                    with overview_tab:
                        detail_col1, detail_col2 = st.columns([1.1, 0.9])

                        with detail_col1:
                            render_section_header("Latest Evaluation", "The most recent pitch analysis from Firebase.")
                            st.write("**Timestamp:**", latest["timestamp"])
                            st.write("**Request ID:**", latest["request_id"])
                            st.write("**Scoring Mode:**", latest["scoring_mode"])
                            st.write("**Strengths:**", latest["strengths"])
                            st.write("**Weaknesses:**", latest["weaknesses"])
                            st.write("**Suggestions:**", latest["suggestions"])

                        with detail_col2:
                            render_section_header("Pitch Breakdown", "What the model is emphasizing right now.")

                            scores_dict = create_score_chart(latest["quantitative_scores"])
                            if scores_dict:
                                st.bar_chart(
                                    pd.DataFrame({
                                        "Metric": list(scores_dict.keys()),
                                        "Score": list(scores_dict.values())
                                    }).set_index("Metric")
                                )
                            else:
                                st.info("No quantitative scores available")

                            modality_dict = create_score_chart(latest["modality_weights"])
                            if modality_dict:
                                st.bar_chart(
                                    pd.DataFrame({
                                        "Modality": list(modality_dict.keys()),
                                        "Weight": list(modality_dict.values())
                                    }).set_index("Modality")
                                )
                            else:
                                st.info("No modality weights available")

                            risk_dict = create_score_chart(latest["risk_distribution"])
                            if risk_dict:
                                st.bar_chart(
                                    pd.DataFrame({
                                        "Risk Factor": list(risk_dict.keys()),
                                        "Score": list(risk_dict.values())
                                    }).set_index("Risk Factor")
                                )
                            else:
                                st.info("No risk factors identified")

                    with history_tab:
                        render_section_header("Recent Evaluations", "Browse the latest runs stored in Firestore.")

                        display_cols = [
                            "timestamp",
                            "video_title",
                            "overall_score",
                            "confidence_score",
                            "investment_band",
                            "language_detected",
                        ]
                        table_df = df[display_cols].copy()
                        table_df.columns = ["Timestamp", "Video", "Score", "Confidence", "Band", "Language"]

                        st.dataframe(
                            table_df,
                            use_container_width=True,
                            hide_index=True,
                        )

                    with trend_tab:
                        render_section_header("Score Trend", "Track how the overall pitch score changes over time.")

                        trend_data = df[["timestamp", "overall_score"]].dropna().sort_values("timestamp")
                        if len(trend_data) > 1:
                            st.line_chart(
                                trend_data.set_index("timestamp"),
                                y="overall_score"
                            )
                        else:
                            st.info("Need at least 2 evaluations to show trend")

            # Update timestamp
            update_count += 1
            with last_update:
                st.caption(
                    f"Auto-refreshing every {refresh_interval}s | "
                    f"Updates: {update_count} | Last update: {pd.Timestamp.now().strftime('%H:%M:%S')}"
                )

            time.sleep(refresh_interval)
            st.rerun()

        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
            break
        except Exception:
            logger.exception("Dashboard error")
            st.error("Dashboard error")
            time.sleep(5)


if __name__ == "__main__":
    main()
