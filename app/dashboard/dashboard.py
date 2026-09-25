import json
import os
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# AEGIS AI DASHBOARD
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

STATE_FILE = os.path.join(
    BASE_DIR,
    "app",
    "latest_signal.json",
)

MARKET_DATA_FILE = os.path.join(
    BASE_DIR,
    "app",
    "market_data.json",
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="AEGIS AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# GLOBAL STYLE
# ============================================================

st.html(
    """
<style>
html, body {
    font-family: Inter, Arial, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 15% 10%, rgba(0,255,120,0.08), transparent 28%),
        radial-gradient(circle at 85% 15%, rgba(255,0,70,0.06), transparent 25%),
        radial-gradient(circle at 50% 100%, rgba(0,255,120,0.04), transparent 30%),
        #070b09;
    color: #eafff0;
}

.aegis-header {
    background:
        linear-gradient(
            135deg,
            rgba(9,30,19,0.95),
            rgba(7,12,10,0.98)
        );
    border: 1px solid rgba(57,255,136,0.20);
    border-radius: 18px;
    padding: 20px 24px;
    margin-bottom: 18px;
    box-shadow:
        0 0 30px rgba(57,255,136,0.04),
        inset 0 0 30px rgba(57,255,136,0.02);
}

.aegis-title {
    font-size: 32px;
    font-weight: 800;
    color: #39ff88;
    letter-spacing: 1px;
}

.aegis-subtitle {
    color: #7e9688;
    font-size: 13px;
    margin-top: 3px;
}

.metric-card {
    background:
        linear-gradient(
            145deg,
            rgba(12,28,19,0.96),
            rgba(7,15,11,0.96)
        );
    border: 1px solid rgba(57,255,136,0.14);
    border-radius: 14px;
    padding: 15px 17px;
    min-height: 94px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.18);
}

.metric-label {
    color: #71887a;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.3px;
}

.metric-value {
    color: #eafff0;
    font-size: 23px;
    font-weight: 750;
    margin-top: 7px;
}

.green {
    color: #39ff88;
}

.red {
    color: #ff5364;
}

.yellow {
    color: #ffd166;
}

.muted {
    color: #8ca497;
}

.panel {
    background:
        linear-gradient(
            145deg,
            rgba(10,20,14,0.96),
            rgba(6,11,9,0.96)
        );
    border: 1px solid rgba(57,255,136,0.12);
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 10px 35px rgba(0,0,0,0.20);
}

.panel-title {
    color: #dfffea;
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 10px;
}

.reason {
    background: rgba(57,255,136,0.045);
    border: 1px solid rgba(57,255,136,0.08);
    border-radius: 9px;
    padding: 8px 10px;
    margin-bottom: 7px;
    color: #b9d5c5;
    font-size: 12px;
}

.status-online {
    color: #39ff88;
    font-weight: 700;
}

.data-status {
    color: #7e9688;
    font-size: 11px;
    margin-top: 5px;
}

div[data-testid="stHorizontalBlock"] {
    gap: 12px;
}

button[kind="secondary"] {
    border-color: rgba(57,255,136,0.15);
}

button[kind="primary"] {
    border-color: rgba(57,255,136,0.50);
}

</style>
"""
)


# ============================================================
# DATA LOADERS
# ============================================================

def load_state():
    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    except Exception:
        return None


def load_market_data():
    if not os.path.exists(MARKET_DATA_FILE):
        return None

    try:
        with open(
            MARKET_DATA_FILE,
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    except Exception:
        return None


def age_text(updated_at):
    if not updated_at:
        return "UNKNOWN"

    try:
        dt = datetime.fromisoformat(
            updated_at.replace("Z", "+00:00")
        )

        now = datetime.now(timezone.utc)

        seconds = max(
            0,
            int(
                (now - dt).total_seconds()
            ),
        )

        if seconds < 60:
            return f"{seconds}s AGO"

        if seconds < 3600:
            return f"{seconds // 60}m AGO"

        return f"{seconds // 3600}h AGO"

    except Exception:
        return "UNKNOWN"


# ============================================================
# CANDLE DATA
# ============================================================

def candles_to_dataframe(
    market_data,
    timeframe,
):
    if not market_data:
        return pd.DataFrame()

    timeframes = market_data.get(
        "timeframes",
        {},
    )

    candles = timeframes.get(
        timeframe,
        [],
    )

    if not candles:
        return pd.DataFrame()

    df = pd.DataFrame(candles)

    required = [
        "time",
        "open",
        "high",
        "low",
        "close",
    ]

    if not all(
        column in df.columns
        for column in required
    ):
        return pd.DataFrame()

    df["time"] = pd.to_datetime(
        df["time"],
        utc=True,
        errors="coerce",
    )

    for column in [
        "open",
        "high",
        "low",
        "close",
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=[
            "time",
            "open",
            "high",
            "low",
            "close",
        ]
    )

    return df.sort_values(
        "time"
    ).reset_index(drop=True)


# ============================================================
# CHART
# ============================================================

def build_chart(
    df,
    signal,
    timeframe,
):
    """
    Build the AEGIS trading-terminal chart.

    All annotations come from actual AEGIS detector output
    serialized by the watcher. No synthetic market structure
    is generated here.
    """

    fig = go.Figure()

    if df.empty:
        fig.update_layout(
            height=720,
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(4,9,7,0.78)",
            annotations=[
                dict(
                    text="NO MARKET DATA AVAILABLE",
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(
                        size=16,
                        color="#7e9688",
                    ),
                )
            ],
        )
        return fig

    # ========================================================
    # DISPLAY WINDOW
    # ========================================================

    visible_count = min(60, len(df))
    visible_df = df.iloc[-visible_count:].copy()

    x_start = visible_df["time"].iloc[0]
    x_end = visible_df["time"].iloc[-1]

    # ========================================================
    # CANDLESTICKS
    # ========================================================

    fig.add_trace(
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=f"XAU/USD {timeframe}",
            increasing_fillcolor="#39ff88",
            increasing_line_color="#39ff88",
            decreasing_fillcolor="#ff5364",
            decreasing_line_color="#ff5364",
            increasing_line_width=2,
            decreasing_line_width=2,
            whiskerwidth=0.9,
        )
    )

    # ========================================================
    # HELPERS
    # ========================================================

    def candle_time(index):
        try:
            index = int(index)

            if 0 <= index < len(df):
                return df.iloc[index]["time"]

        except (
            TypeError,
            ValueError,
            IndexError,
        ):
            pass

        return None

    def in_visible_range(value):
        if value is None:
            return False

        try:
            value = float(value)
            low = float(visible_df["low"].min())
            high = float(visible_df["high"].max())

            padding = (high - low) * 0.15

            return (
                value >= low - padding
                and value <= high + padding
            )

        except (
            TypeError,
            ValueError,
        ):
            return False

    def add_label(
        x,
        y,
        text,
        position="top",
        size=10,
    ):
        if x is None or y is None:
            return

        if position == "bottom":
            yshift = -14
        else:
            yshift = 14

        fig.add_annotation(
            x=x,
            y=float(y),
            text=text,
            showarrow=False,
            yshift=yshift,
            font=dict(
                size=size,
                color="#dfffea",
            ),
            bgcolor="rgba(3,10,6,0.82)",
            bordercolor="rgba(57,255,136,0.25)",
            borderwidth=1,
            borderpad=2,
        )

    # ========================================================
    # REAL MARKET STRUCTURE
    #
    # Uses M5 structure for M5 chart and HTF structure for
    # H1 / M15 charts.
    # ========================================================

    if timeframe == "M5":
        structure = signal.get(
            "market_swings",
            [],
        )
    elif timeframe == "M15":
        structure = signal.get(
            "m15_structure",
            [],
        )
    else:
        structure = signal.get(
            "h1_structure",
            [],
        )

    for swing in structure:
        if not isinstance(swing, dict):
            continue

        price = swing.get("price")
        label = swing.get("label")

        if price is None or not label:
            continue

        index = swing.get("index")
        x = candle_time(index)

        if x is None:
            x = swing.get("time")

        if x is None:
            continue

        if not in_visible_range(price):
            continue

        position = (
            "bottom"
            if swing.get("type") == "LOW"
            else "top"
        )

        add_label(
            x,
            price,
            str(label),
            position=position,
            size=9,
        )

    # ========================================================
    # BOS
    # ========================================================

    market_breaks = signal.get(
        "market_breaks",
        [],
    )

    for event in market_breaks:
        if not isinstance(event, dict):
            continue

        level = event.get("level")

        if level is None:
            continue

        index = event.get("index")
        x = candle_time(index)

        if x is None:
            continue

        if not in_visible_range(level):
            continue

        direction = str(
            event.get(
                "direction",
                "",
            )
        ).upper()

        bos_type = str(
            event.get(
                "type",
                "BOS",
            )
        ).upper()

        fig.add_trace(
            go.Scatter(
                x=[
                    x_start,
                    x_end,
                ],
                y=[
                    float(level),
                    float(level),
                ],
                mode="lines",
                name=f"{bos_type} {direction}",
                line=dict(
                    dash="dot",
                    width=1,
                ),
                opacity=0.45,
                hovertemplate=(
                    f"{bos_type} • "
                    f"{direction}<br>"
                    f"Level: {float(level):.2f}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

        add_label(
            x,
            level,
            f"{bos_type} {direction[:1]}",
            position="top",
            size=8,
        )

    # ========================================================
    # LIQUIDITY POOLS + SWEEPS
    # ========================================================

    liquidity_events = signal.get(
        "liquidity_events",
        [],
    )

    for event in liquidity_events:
        if not isinstance(event, dict):
            continue

        price = event.get("price")

        if price is None:
            continue

        if not in_visible_range(price):
            continue

        first_index = event.get(
            "first_index"
        )

        second_index = event.get(
            "second_index"
        )

        first_x = candle_time(
            first_index
        )

        second_x = candle_time(
            second_index
        )

        if first_x is None:
            first_x = x_start

        if second_x is None:
            second_x = x_end

        liquidity_type = str(
            event.get(
                "type",
                "LIQUIDITY",
            )
        ).upper()

        swept = bool(
            event.get(
                "swept",
                False,
            )
        )

        label = (
            f"{liquidity_type} SWEEP"
            if swept
            else liquidity_type
        )

        fig.add_trace(
            go.Scatter(
                x=[
                    first_x,
                    second_x,
                ],
                y=[
                    float(price),
                    float(price),
                ],
                mode="lines",
                name=label,
                line=dict(
                    dash="dash",
                    width=1,
                ),
                opacity=0.5,
                hovertemplate=(
                    f"{label}<br>"
                    f"Price: {float(price):.2f}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

        if swept:
            sweep_index = event.get(
                "sweep_index"
            )

            sweep_x = candle_time(
                sweep_index
            )

            if sweep_x is None:
                sweep_x = event.get(
                    "sweep_time"
                )

            if sweep_x is not None:
                add_label(
                    sweep_x,
                    price,
                    f"⚡ {liquidity_type} SWEEP",
                    position="top",
                    size=8,
                )

    # ========================================================
    # FAIR VALUE GAPS
    # ========================================================

    fvg_events = signal.get(
        "fvg_events",
        [],
    )

    for fvg in fvg_events:
        if not isinstance(fvg, dict):
            continue

        top = fvg.get("top")
        bottom = fvg.get("bottom")

        if top is None or bottom is None:
            continue

        index = fvg.get("index")
        x = candle_time(index)

        if x is None:
            x = fvg.get("time")

        if x is None:
            continue

        direction = str(
            fvg.get(
                "direction",
                "",
            )
        ).upper()

        active = bool(
            fvg.get(
                "active",
                False,
            )
        )

        mitigated = bool(
            fvg.get(
                "mitigated",
                False,
            )
        )

        # Extend the actual detected FVG toward current price.
        x0 = x
        x1 = x_end

        opacity = (
            0.16
            if active and not mitigated
            else 0.06
        )

        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x1,
            y0=float(bottom),
            y1=float(top),
            xref="x",
            yref="y",
            fillcolor=(
                "rgba(57,255,136,0.18)"
                if direction == "BULLISH"
                else "rgba(255,83,100,0.18)"
            ),
            line=dict(
                width=1,
                dash="dot",
            ),
            opacity=opacity,
            layer="below",
        )

        if active and not mitigated:
            add_label(
                x,
                (
                    float(top)
                    + float(bottom)
                ) / 2,
                f"FVG {direction[:1]}",
                position="top",
                size=8,
            )

    # ========================================================
    # SUPPORT / RESISTANCE
    # ========================================================

    support_resistance = signal.get(
        "support_resistance",
        [],
    )

    for level in support_resistance:
        if not isinstance(level, dict):
            continue

        price = level.get("price")

        if price is None:
            continue

        if not in_visible_range(price):
            continue

        level_type = str(
            level.get(
                "level_type",
                "",
            )
        ).upper()

        touches = level.get(
            "touches",
            0,
        )

        strength = level.get(
            "strength",
            0,
        )

        first_index = level.get(
            "first_index"
        )

        last_index = level.get(
            "last_index"
        )

        x0 = candle_time(first_index)
        x1 = candle_time(last_index)

        if x0 is None:
            x0 = x_start

        if x1 is None:
            x1 = x_end

        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[
                    float(price),
                    float(price),
                ],
                mode="lines",
                name=level_type,
                line=dict(
                    dash="dashdot",
                    width=1,
                ),
                opacity=0.35,
                hovertemplate=(
                    f"{level_type}<br>"
                    f"Price: {float(price):.2f}<br>"
                    f"Touches: {touches}<br>"
                    f"Strength: {strength}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    # ========================================================
    # ENTRY / SL / TP
    # ========================================================

    entry = signal.get("entry")
    sl = signal.get("sl")
    tp1 = signal.get("tp1")
    tp2 = signal.get("tp2")

    valid_levels = []

    for value in [
        entry,
        sl,
        tp1,
        tp2,
    ]:
        try:
            if value is not None and float(value) > 0:
                valid_levels.append(
                    float(value)
                )
        except (
            TypeError,
            ValueError,
        ):
            pass

    if entry is not None and float(entry or 0) > 0:
        fig.add_hline(
            y=float(entry),
            line_width=2,
            line_dash="dash",
            annotation_text=(
                f" ENTRY {float(entry):.2f}"
            ),
            annotation_position="top left",
        )

    if sl is not None and float(sl or 0) > 0:
        fig.add_hline(
            y=float(sl),
            line_width=1.5,
            line_dash="dot",
            annotation_text=(
                f" SL {float(sl):.2f}"
            ),
            annotation_position="bottom left",
        )

    if tp1 is not None and float(tp1 or 0) > 0:
        fig.add_hline(
            y=float(tp1),
            line_width=1.5,
            line_dash="dot",
            annotation_text=(
                f" TP1 {float(tp1):.2f}"
            ),
            annotation_position="top right",
        )

    if tp2 is not None and float(tp2 or 0) > 0:
        fig.add_hline(
            y=float(tp2),
            line_width=1.5,
            line_dash="dot",
            annotation_text=(
                f" TP2 {float(tp2):.2f}"
            ),
            annotation_position="top right",
        )

    # ========================================================
    # WAITING FOR ENTRY
    # ========================================================

    setup_status = str(
        signal.get(
            "setup_status",
            "",
        )
    ).upper()

    entry_zone = str(
        signal.get(
            "entry_zone",
            "NONE",
        )
    ).upper()

    if (
        setup_status == "WAIT"
        and (
            entry is None
            or float(entry or 0) <= 0
            or entry_zone == "NONE"
        )
    ):
        fig.add_annotation(
            x=0.5,
            y=0.96,
            xref="paper",
            yref="paper",
            text="⏳ WAITING FOR ENTRY",
            showarrow=False,
            font=dict(
                size=13,
                color="#ffe28a",
            ),
            bgcolor="rgba(20,16,3,0.86)",
            bordercolor="rgba(255,210,90,0.35)",
            borderwidth=1,
            borderpad=6,
        )

    # ========================================================
    # Y RANGE
    # ========================================================

    visible_low = float(
        visible_df["low"].min()
    )

    visible_high = float(
        visible_df["high"].max()
    )

    price_range = (
        visible_high
        - visible_low
    )

    if price_range <= 0:
        price_range = 1

    padding = price_range * 0.08

    y_min = visible_low - padding
    y_max = visible_high + padding

    if valid_levels:
        y_min = min(
            y_min,
            *valid_levels,
        )

        y_max = max(
            y_max,
            *valid_levels,
        )

    # ========================================================
    # LAYOUT
    # ========================================================

    fig.update_layout(
        height=720,
        template="plotly_dark",

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(3,8,6,0.92)",

        margin=dict(
            l=10,
            r=10,
            t=20,
            b=10,
        ),

        dragmode="pan",
        hovermode="x unified",

        font=dict(
            color="#a9c0b1",
            size=11,
        ),

        xaxis=dict(
            type="date",

            rangeslider=dict(
                visible=False
            ),

            range=[
                x_start,
                x_end,
            ],

            showgrid=True,
            gridcolor="rgba(120,150,130,0.07)",

            zeroline=False,

            showline=True,
            linewidth=1,
            linecolor="rgba(57,255,136,0.15)",

            fixedrange=False,

            showspikes=True,
            spikemode="across",
            spikesnap="cursor",

            tickfont=dict(
                size=10,
            ),
        ),

        yaxis=dict(
            range=[
                y_min,
                y_max,
            ],

            autorange=False,

            side="right",

            showgrid=True,
            gridcolor="rgba(120,150,130,0.07)",

            zeroline=False,

            showline=True,
            linewidth=1,
            linecolor="rgba(57,255,136,0.15)",

            fixedrange=False,

            tickfont=dict(
                size=10,
            ),
        ),

        hoverlabel=dict(
            bgcolor="#07100b",
            bordercolor="#39ff88",
            font=dict(
                color="#eafff0",
                size=12,
            ),
        ),

        legend=dict(
            bgcolor="rgba(0,0,0,0)"
        ),
    )

    return fig


# ============================================================
# LOAD ENGINE STATE
# ============================================================

data = load_state()
market_data = load_market_data()

# ============================================================
# CLOUD / OFFLINE STATE
# ============================================================
# The public dashboard must never crash just because the
# watcher has not yet published runtime state.
#
# Runtime files are intentionally excluded from GitHub.
# When the cloud watcher/API is connected, these loaders
# will receive the live state again.

if not data:
    st.html(
        """
<div style="
    min-height:70vh;
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
">
    <div style="
        max-width:720px;
        padding:45px;
        border:1px solid rgba(57,255,136,0.18);
        border-radius:18px;
        background:rgba(5,12,8,0.72);
        box-shadow:0 0 40px rgba(57,255,136,0.05);
    ">

        <div style="
            color:#39ff88;
            font-size:14px;
            letter-spacing:4px;
            margin-bottom:18px;
        ">
            AEGIS AI
        </div>

        <div style="
            color:#eafff0;
            font-size:30px;
            font-weight:700;
            margin-bottom:14px;
        ">
            CLOUD ENGINE INITIALIZING
        </div>

        <div style="
            color:#7d9485;
            font-size:14px;
            line-height:1.8;
        ">
            The public dashboard is online, but the AEGIS
            market engine has not published live state yet.
            <br><br>
            No synthetic market data is being displayed.
        </div>

        <div style="
            margin-top:25px;
            color:#d8e7dc;
            font-size:12px;
            letter-spacing:1px;
        ">
            ● AWAITING LIVE MARKET FEED
        </div>

    </div>
</div>
"""
    )

    st.stop()

signal = data.get(
    "signal",
    {},
)

symbol = data.get(
    "symbol",
    "XAU/USD",
)

default_timeframe = data.get(
    "timeframe",
    "M5",
)

updated_at = data.get(
    "updated_at"
)

direction = signal.get(
    "direction",
    "N/A",
)

confidence = signal.get(
    "confidence",
    0,
)

entry = signal.get("entry")
rr = signal.get("risk_reward")

setup = signal.get(
    "setup_type",
    "N/A",
)

zone = signal.get(
    "entry_zone",
    "N/A",
)

mtf = signal.get(
    "mtf_status",
    "N/A",
)

execution = signal.get(
    "execution_type",
    "N/A",
)

risk = signal.get(
    "risk_mode",
    "N/A",
)

valid = data.get(
    "valid_setup",
    False,
)

# ============================================================
# DASHBOARD SETUP STATUS
#
# The engine distinguishes between:
#   VALID  -> executable trade passed validation
#   WAIT   -> market bias/confluence exists, but no valid
#             fresh entry zone is available yet
#   INVALID -> an actual setup failed validation
#
# Do NOT change the engine's signal. This is presentation logic.
# ============================================================

signal_setup_status = str(
    signal.get(
        "setup_status",
        "",
    )
).upper()

entry = signal.get("entry")
entry_zone = str(
    signal.get(
        "entry_zone",
        "NONE",
    )
).upper()

trade_valid = bool(
    signal.get(
        "trade_valid",
        False,
    )
)

validation_reasons = signal.get(
    "validation_reasons",
    [],
)

if trade_valid and valid:
    dashboard_status = "VALID"
    dashboard_status_label = "VALID ✓"
    dashboard_status_class = "valid"

elif signal_setup_status == "WAIT":
    dashboard_status = "WAIT"
    dashboard_status_label = "WAITING FOR ENTRY"
    dashboard_status_class = "wait"

elif (
    not trade_valid
    and (
        entry is None
        or float(entry or 0) <= 0
        or entry_zone == "NONE"
    )
):
    dashboard_status = "WAIT"
    dashboard_status_label = "WAITING FOR ENTRY"
    dashboard_status_class = "wait"

else:
    dashboard_status = "INVALID"
    dashboard_status_label = "INVALID ✕"
    dashboard_status_class = "invalid"

reasons = signal.get(
    "reasons",
    []
)


# ============================================================
# SESSION TIMEFRAME
# ============================================================

if "aegis_timeframe" not in st.session_state:
    st.session_state.aegis_timeframe = default_timeframe

selected_timeframe = st.session_state.aegis_timeframe


# ============================================================
# HEADER
# ============================================================

st.html(
    """
<div class="aegis-header">
    <div class="aegis-title">🛡️ AEGIS AI</div>

    <div class="aegis-subtitle">
        MULTI-TIMEFRAME MARKET INTELLIGENCE
        &nbsp; • &nbsp;

        <span class="status-online">
            ● ENGINE ONLINE
        </span>

        &nbsp; • &nbsp;

        XAU/USD
    </div>
</div>
"""
)


# ============================================================
# TOP METRICS
# ============================================================

m1, m2, m3, m4, m5, m6 = st.columns(6)

direction_class = (
    "green"
    if direction == "BULLISH"
    else "red"
    if direction == "BEARISH"
    else "yellow"
)

metrics = [
    ("MARKET", symbol),
    ("TIMEFRAME", selected_timeframe),
    ("DIRECTION", direction),
    ("CONFIDENCE", f"{confidence}%"),
    ("ENTRY", entry if entry is not None else "—"),
    ("R:R", rr if rr is not None else "—"),
]

for col, (label, value) in zip(
    [
        m1,
        m2,
        m3,
        m4,
        m5,
        m6,
    ],
    metrics,
):
    with col:

        extra = (
            direction_class
            if label == "DIRECTION"
            else ""
        )

        st.html(
            f"""
<div class="metric-card">
    <div class="metric-label">
        {label}
    </div>

    <div class="metric-value {extra}">
        {value}
    </div>
</div>
"""
        )


st.write("")


# ============================================================
# TIMEFRAME SELECTOR
# ============================================================

st.html(
    '<div class="panel-title">📈 MARKET CHART</div>'
)

chart_cols = st.columns(
    [
        1,
        1,
        1,
        5,
    ]
)

with chart_cols[0]:

    if st.button(
        "M5",
        use_container_width=True,
        type=(
            "primary"
            if selected_timeframe == "M5"
            else "secondary"
        ),
    ):
        st.session_state.aegis_timeframe = "M5"
        st.rerun()

with chart_cols[1]:

    if st.button(
        "M15",
        use_container_width=True,
        type=(
            "primary"
            if selected_timeframe == "M15"
            else "secondary"
        ),
    ):
        st.session_state.aegis_timeframe = "M15"
        st.rerun()

with chart_cols[2]:

    if st.button(
        "H1",
        use_container_width=True,
        type=(
            "primary"
            if selected_timeframe == "H1"
            else "secondary"
        ),
    ):
        st.session_state.aegis_timeframe = "H1"
        st.rerun()


selected_timeframe = st.session_state.aegis_timeframe

market_updated = (
    market_data.get("updated_at")
    if market_data
    else None
)

candle_df = candles_to_dataframe(
    market_data,
    selected_timeframe,
)

st.html(
    f"""
<div class="data-status">
    ● LIVE WATCHER DATA
    &nbsp; • &nbsp;
    {selected_timeframe}
    &nbsp; • &nbsp;
    {len(candle_df)} CANDLES
    &nbsp; • &nbsp;
    UPDATED {age_text(market_updated)}
</div>
"""
)


# ============================================================
# CHART + INTELLIGENCE
# ============================================================

left, right = st.columns(
    [
        2.8,
        1,
    ]
)

with left:

    fig = build_chart(
        candle_df,
        signal,
        selected_timeframe,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True,
            "displayModeBar": True,
        },
    )


with right:

    status_class = (
        "green"
        if dashboard_status == "VALID"
        else "yellow"
        if dashboard_status == "WAIT"
        else "red"
    )

    status_text = dashboard_status_label

    st.html(
        f"""
<div class="panel">

    <div class="panel-title">
        🧠 AEGIS INTELLIGENCE
    </div>

    <div style="color:#b9d5c5;font-size:12px;line-height:1.9;">

        <b>MTF STATUS</b><br>
        <span class="muted">{mtf}</span><br>

        <b>EXECUTION</b><br>
        <span class="muted">{execution}</span><br>

        <b>RISK MODE</b><br>
        <span class="muted">{risk}</span><br>

        <b>SETUP</b><br>
        <span class="muted">{setup}</span><br>

        <b>ENTRY ZONE</b><br>
        <span class="muted">{zone}</span><br>

        <b>SETUP STATUS</b><br>
        <span class="{status_class}">{status_text}</span><br><br>

        <b>LAST SIGNAL UPDATE</b><br>
        <span class="muted">{age_text(updated_at)}</span>

    </div>

</div>
"""
    )


# ============================================================
# CONFLUENCE
# ============================================================

st.write("")

st.html(
    '<div class="panel-title">🔎 MARKET CONFLUENCE</div>'
)

if reasons:

    reason_cols = st.columns(2)

    for i, reason in enumerate(reasons):

        with reason_cols[i % 2]:

            st.html(
                f"""
<div class="reason">
    <span class="green">✓</span>
    {reason}
</div>
"""
            )

else:

    st.info(
        "No confluence factors reported."
    )


# ============================================================
# DATA HEALTH
# ============================================================

st.write("")

health_left, health_mid, health_right = st.columns(3)

with health_left:

    h1_count = len(
        candles_to_dataframe(
            market_data,
            "H1",
        )
    )

    m15_count = len(
        candles_to_dataframe(
            market_data,
            "M15",
        )
    )

    m5_count = len(
        candles_to_dataframe(
            market_data,
            "M5",
        )
    )

    st.html(
        f"""
<div class="metric-card">

    <div class="metric-label">
        MARKET DATA
    </div>

    <div class="metric-value green">
        {"ONLINE" if market_data else "OFFLINE"}
    </div>

    <div class="data-status">
        H1 {h1_count}
        • M15 {m15_count}
        • M5 {m5_count}
    </div>

</div>
"""
    )


with health_mid:

    signal_class = (
        "green"
        if dashboard_status == "VALID"
        else "yellow"
        if dashboard_status == "WAIT"
        else "red"
    )

    signal_text = (
        "VALID"
        if dashboard_status == "VALID"
        else "WAITING FOR ENTRY"
        if dashboard_status == "WAIT"
        else "INVALID"
    )

    st.html(
        f"""
<div class="metric-card">

    <div class="metric-label">
        SIGNAL STATE
    </div>

    <div class="metric-value {signal_class}">
        {signal_text}
    </div>

    <div class="data-status">
        UPDATED {age_text(updated_at)}
    </div>

</div>
"""
    )


with health_right:

    st.html(
        f"""
<div class="metric-card">

    <div class="metric-label">
        WATCHER DATA
    </div>

    <div class="metric-value green">
        ACTIVE
    </div>

    <div class="data-status">
        MARKET CACHE UPDATED
        {age_text(market_updated)}
    </div>

</div>
"""
    )


# ============================================================
# FOOTER
# ============================================================

st.write("")

st.html(
    f"""
<div style="
    text-align:center;
    color:#53685b;
    font-size:11px;
    padding:15px;
">
    AEGIS AI • XAU/USD • {selected_timeframe} •
    REAL WATCHER MARKET DATA
</div>
"""
)
