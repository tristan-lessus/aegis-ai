import streamlit as st

from feeds.provider_factory import ProviderFactory
from config.settings import DEFAULT_MARKETS
from engine.analysis_pipeline import AnalysisPipeline


st.set_page_config(
    page_title="AEGIS AI",
    page_icon="⚡",
    layout="wide",
)


def format_price(value):

    if value is None:
        return "—"

    try:
        value = float(value)

        if value == 0:
            return "—"

        return f"{value:,.2f}"

    except (
        TypeError,
        ValueError,
    ):

        return "—"


def format_rr(value):

    if value is None:
        return "—"

    try:

        value = float(value)

        if value <= 0:
            return "—"

        return f"1:{value:.2f}"

    except (
        TypeError,
        ValueError,
    ):

        return "—"


def main():

    st.title("⚡ AEGIS AI")
    st.caption(
        "Multi-Timeframe Smart Money Analysis Engine"
    )

    # ==========================================
    # SIDEBAR
    # ==========================================

    st.sidebar.header("Market")

    market = st.sidebar.selectbox(
        "Instrument",
        DEFAULT_MARKETS,
    )

    timeframe = st.sidebar.selectbox(
        "Execution Timeframe",
        ["M1", "M5", "M15", "M30", "H1"],
        index=1,
    )

    candle_count = st.sidebar.slider(
        "Execution Candles",
        min_value=100,
        max_value=500,
        value=300,
        step=50,
    )

    refresh = st.sidebar.button(
        "🔄 Refresh Analysis"
    )

    # ==========================================
    # PROVIDER / PIPELINE
    # ==========================================

    provider = ProviderFactory.create(
        "live"
    )

    pipeline = AnalysisPipeline()

    # ==========================================
    # LOAD MTF MARKET DATA
    # ==========================================

    try:

        with st.spinner(
            "Fetching H1..."
        ):

            h1_candles = provider.get_candles(
                symbol=market,
                timeframe="H1",
                count=candle_count,
            )

        with st.spinner(
            "Fetching M15..."
        ):

            m15_candles = provider.get_candles(
                symbol=market,
                timeframe="M15",
                count=candle_count,
            )

        with st.spinner(
            f"Fetching {timeframe}..."
        ):

            candles = provider.get_candles(
                symbol=market,
                timeframe=timeframe,
                count=candle_count,
            )

    except Exception as error:

        st.error(
            f"Failed to load market data: {error}"
        )

        return

    if not candles:

        st.warning(
            "No execution timeframe data received."
        )

        return

    if not h1_candles:

        st.warning(
            "No H1 data received."
        )

        return

    if not m15_candles:

        st.warning(
            "No M15 data received."
        )

        return

    # ==========================================
    # ANALYZE MTF
    # ==========================================

    try:

        signal = pipeline.analyze(
            candles,
            m15_candles=m15_candles,
            h1_candles=h1_candles,
        )

    except Exception as error:

        st.error(
            f"Analysis failed: {error}"
        )

        return

    last = candles[-1]

    # ==========================================
    # SIGNAL FIELDS
    # ==========================================

    direction = getattr(
        signal,
        "direction",
        "NONE",
    )

    confidence = getattr(
        signal,
        "confidence",
        0,
    )

    h1_bias = getattr(
        signal,
        "h1_bias",
        "UNKNOWN",
    )

    m15_bias = getattr(
        signal,
        "m15_bias",
        "UNKNOWN",
    )

    mtf_alignment = getattr(
        signal,
        "mtf_alignment",
        "INSUFFICIENT_DATA",
    )

    mtf_status = getattr(
        signal,
        "mtf_status",
        "INSUFFICIENT_DATA",
    )

    execution_type = getattr(
        signal,
        "execution_type",
        "UNKNOWN",
    )

    risk_mode = getattr(
        signal,
        "risk_mode",
        "NORMAL",
    )

    htf_conflict = getattr(
        signal,
        "htf_conflict",
        False,
    )

    trade_valid = getattr(
        signal,
        "trade_valid",
        False,
    )

    setup_status = getattr(
        signal,
        "setup_status",
        "WAIT",
    )

    validation_reasons = getattr(
        signal,
        "validation_reasons",
        [],
    )

    # ==========================================
    # MARKET HEADER
    # ==========================================

    st.subheader(
        f"{market} • {timeframe} Execution"
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Current Price",
            format_price(
                last.close
            ),
        )

    with col2:

        st.metric(
            "H1 Bias",
            h1_bias,
        )

    with col3:

        st.metric(
            "M15 Bias",
            m15_bias,
        )

    with col4:

        st.metric(
            f"{timeframe} Direction",
            direction,
        )

    st.caption(
        f"Last candle: {last.time}"
    )

    st.divider()

    # ==========================================
    # MTF STATUS
    # ==========================================

    st.subheader(
        "🧭 Multi-Timeframe Structure"
    )

    mtf_col1, mtf_col2, mtf_col3, mtf_col4 = (
        st.columns(4)
    )

    with mtf_col1:

        st.metric(
            "MTF Alignment",
            mtf_alignment,
        )

    with mtf_col2:

        st.metric(
            "MTF Status",
            mtf_status,
        )

    with mtf_col3:

        st.metric(
            "Execution Type",
            execution_type,
        )

    with mtf_col4:

        st.metric(
            "Risk Mode",
            risk_mode,
        )

    if htf_conflict:

        st.warning(
            "⚠️ Higher-timeframe conflict detected."
        )

    elif mtf_status == "ALIGNED":

        st.success(
            "🟢 H1 and M15 support the execution direction."
        )

    elif mtf_status == "PARTIAL":

        st.info(
            "🟡 Partial higher-timeframe confirmation."
        )

    elif mtf_status == "COUNTERTREND":

        st.warning(
            "🟠 Execution is counter to higher-timeframe structure."
        )

    else:

        st.info(
            "⚪ Insufficient higher-timeframe confirmation."
        )

    st.divider()

    # ==========================================
    # SIGNAL
    # ==========================================

    st.subheader(
        "📡 AEGIS Signal"
    )

    if direction == "BULLISH":

        st.success(
            f"🟢 BULLISH — Confluence {confidence}%"
        )

    elif direction == "BEARISH":

        st.error(
            f"🔴 BEARISH — Confluence {confidence}%"
        )

    else:

        st.warning(
            f"🟡 NO CLEAR DIRECTION — Confluence {confidence}%"
        )

    st.caption(
        "Confluence is an internal signal score, "
        "not a probability of winning."
    )

    # ==========================================
    # TRADE SETUP
    # ==========================================

    st.subheader(
        "🎯 Trade Setup"
    )

    entry = getattr(
        signal,
        "entry",
        None,
    )

    stop_loss = getattr(
        signal,
        "stop_loss",
        None,
    )

    tp1 = getattr(
        signal,
        "take_profit_1",
        None,
    )

    tp2 = getattr(
        signal,
        "take_profit_2",
        None,
    )

    rr = getattr(
        signal,
        "risk_reward",
        None,
    )

    entry_zone = getattr(
        signal,
        "entry_zone",
        "—",
    )

    setup_type = getattr(
        signal,
        "setup_type",
        "—",
    )

    source_time = getattr(
        signal,
        "entry_source_time",
        "—",
    )

    setup_col1, setup_col2, setup_col3, setup_col4 = (
        st.columns(4)
    )

    with setup_col1:

        st.metric(
            "ENTRY",
            format_price(entry),
        )

    with setup_col2:

        st.metric(
            "STOP LOSS",
            format_price(stop_loss),
        )

    with setup_col3:

        st.metric(
            "TP1",
            format_price(tp1),
        )

    with setup_col4:

        st.metric(
            "TP2",
            format_price(tp2),
        )

    detail_col1, detail_col2, detail_col3 = (
        st.columns(3)
    )

    with detail_col1:

        st.metric(
            "Risk / Reward",
            format_rr(rr),
        )

    with detail_col2:

        st.metric(
            "Entry Zone",
            entry_zone,
        )

    with detail_col3:

        st.metric(
            "Setup Type",
            setup_type,
        )

    st.caption(
        f"Setup source: {source_time}"
    )

    st.divider()

    # ==========================================
    # CONFLUENCE
    # ==========================================

    st.subheader(
        "🧠 Confluence Factors"
    )

    reasons = getattr(
        signal,
        "reasons",
        [],
    )

    if reasons:

        columns = st.columns(2)

        for index, reason in enumerate(
            reasons
        ):

            with columns[
                index % 2
            ]:

                st.write(
                    f"✅ {reason}"
                )

    else:

        st.info(
            "No confluence detected."
        )

    st.divider()

    # ==========================================
    # SIGNAL STATUS
    # ==========================================

    st.subheader(
        "📊 Signal Status"
    )

    if (
        setup_status == "VALID"
        and trade_valid
    ):

        st.success(
            "🟢 VALID SETUP — REVIEW BEFORE ENTRY"
        )

    elif setup_status == "WAIT":

        st.warning(
            "🟡 WAIT — Setup has not passed validation."
        )

    else:

        st.info(
            "⚪ NO TRADE"
        )

    if validation_reasons:

        st.caption(
            "Validation:"
        )

        for reason in validation_reasons:

            st.write(
                f"• {reason}"
            )

    st.divider()

    # ==========================================
    # LATEST CANDLE
    # ==========================================

    with st.expander(
        "Latest Candle Details"
    ):

        candle_col1, candle_col2, candle_col3 = (
            st.columns(3)
        )

        with candle_col1:

            st.write(
                f"**Open:** "
                f"{format_price(last.open)}"
            )

            st.write(
                f"**High:** "
                f"{format_price(last.high)}"
            )

        with candle_col2:

            st.write(
                f"**Low:** "
                f"{format_price(last.low)}"
            )

            st.write(
                f"**Close:** "
                f"{format_price(last.close)}"
            )

        with candle_col3:

            st.write(
                f"**Volume:** {last.volume}"
            )

            st.write(
                f"**Time:** {last.time}"
            )


if __name__ == "__main__":
    main()
