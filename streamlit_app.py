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


def main():
    """Main Streamlit dashboard application."""
    
    st.set_page_config(
        page_title="Startup Pitch Edge Dashboard",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar
    st.sidebar.title("⚙️ Dashboard Settings")
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
        st.error("❌ Firebase connection failed. Check your secrets.toml configuration.")
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
                    st.warning("⏳ No pitch evaluations received yet. Waiting for edge device...")
                else:
                    latest = df.iloc[0]

                    # KPI Row
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "📊 Overall Score",
                            f"{latest['overall_score']:.1f}/10",
                            delta=None
                        )

                    with col2:
                        # Confidence may be stored either as a 0-1 fraction or a 0-10 score.
                        conf_val = latest.get('confidence_score', 0) if isinstance(latest, dict) else latest['confidence_score']
                        try:
                            conf_num = float(conf_val)
                        except Exception:
                            conf_num = 0.0

                        if conf_num > 1:
                            # Treat as 0-10 scale, display as 'x.xx/10'
                            st.metric(
                                "🎯 Confidence",
                                f"{conf_num:.2f}/10",
                                delta=None
                            )
                        else:
                            # Treat as fraction 0-1 and display as percent
                            st.metric(
                                "🎯 Confidence",
                                f"{conf_num:.2%}",
                                delta=None
                            )

                    with col3:
                        band_label, _ = format_investment_band(latest["investment_band"])
                        st.markdown(f"#### {band_label}")

                    with col4:
                        st.metric(
                            "🌍 Language",
                            latest["language_detected"],
                            delta=None
                        )

                    # Latest Evaluation Details
                    st.subheader("📋 Latest Evaluation")
                    
                    eval_col1, eval_col2 = st.columns(2)
                    
                    with eval_col1:
                        st.write("**Timestamp:**", latest["timestamp"])
                        st.write("**Request ID:**", latest["request_id"])
                        st.write("**Scoring Mode:**", latest["scoring_mode"])

                    with eval_col2:
                        st.write("**Strengths:**", latest["strengths"])
                        st.write("**Weaknesses:**", latest["weaknesses"])
                        st.write("**Suggestions:**", latest["suggestions"])

                    # Video title
                    st.markdown(f"**Video:** {latest.get('video_title', 'Unknown')}")

                    # Quantitative Scores Chart
                    st.subheader("📈 Quantitative Scores")
                    scores_dict = create_score_chart(latest["quantitative_scores"])
                    if scores_dict:
                        st.bar_chart(pd.DataFrame({
                            "Metric": list(scores_dict.keys()),
                            "Score": list(scores_dict.values())
                        }).set_index("Metric"))
                    else:
                        st.info("No quantitative scores available")

                    # Modality Weights Chart
                    st.subheader("🎙️ Modality Contribution")
                    modality_dict = create_score_chart(latest["modality_weights"])
                    if modality_dict:
                        st.bar_chart(pd.DataFrame({
                            "Modality": list(modality_dict.keys()),
                            "Weight": list(modality_dict.values())
                        }).set_index("Modality"))
                    else:
                        st.info("No modality weights available")

                    # Risk Distribution
                    st.subheader("⚠️ Risk Distribution")
                    risk_dict = create_score_chart(latest["risk_distribution"])
                    if risk_dict:
                        st.bar_chart(pd.DataFrame({
                            "Risk Factor": list(risk_dict.keys()),
                            "Score": list(risk_dict.values())
                        }).set_index("Risk Factor"))
                    else:
                        st.info("No risk factors identified")

                    # Recent Evaluations Table
                    st.subheader("📊 Recent Evaluations")
                    
                    display_cols = ["timestamp", "video_title", "overall_score", "confidence_score", 
                                   "investment_band", "language_detected"]
                    table_df = df[display_cols].copy()
                    table_df.columns = ["Timestamp", "Video", "Score", "Confidence", 
                                       "Band", "Language"]
                    
                    st.dataframe(
                        table_df,
                        use_container_width=True,
                        hide_index=True
                    )

                    # Score Trend Chart
                    st.subheader("📉 Score Trend")
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
                    f"🔄 Auto-refreshing every {refresh_interval}s | "
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
