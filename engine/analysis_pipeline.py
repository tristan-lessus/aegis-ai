from detectors.swing_detector import SwingDetector
from detectors.structure_classifier import StructureClassifier
from detectors.bos_detector import BOSDetector
from detectors.market_structure_detector import MarketStructureDetector
from detectors.liquidity_detector import LiquidityDetector
from detectors.displacement_detector import DisplacementDetector
from detectors.fvg_detector import FVGDetector
from detectors.premium_discount_detector import PremiumDiscountDetector
from detectors.breaker_block_detector import BreakerBlockDetector
from detectors.institutional_order_block_detector import (
    InstitutionalOrderBlockDetector,
)
from detectors.support_resistance_detector import (
    SupportResistanceDetector,
)

from engine.signal_engine import SignalEngine
from engine.entry_engine import EntryEngine
from engine.trade_validator import TradeValidator


class AnalysisPipeline:

    def __init__(self):

        self.swing_detector = (
            SwingDetector()
        )

        self.structure_classifier = (
            StructureClassifier()
        )

        self.bos_detector = (
            BOSDetector()
        )

        self.market_structure_detector = (
            MarketStructureDetector()
        )

        self.liquidity_detector = (
            LiquidityDetector()
        )

        self.displacement_detector = (
            DisplacementDetector()
        )

        self.fvg_detector = (
            FVGDetector()
        )

        self.premium_discount_detector = (
            PremiumDiscountDetector()
        )

        self.breaker_block_detector = (
            BreakerBlockDetector()
        )

        self.institutional_order_block_detector = (
            InstitutionalOrderBlockDetector()
        )

        self.support_resistance_detector = (
            SupportResistanceDetector()
        )

        self.signal_engine = (
            SignalEngine()
        )

        self.entry_engine = (
            EntryEngine()
        )

        self.trade_validator = (
            TradeValidator(
                min_risk_reward=1.5
            )
        )

    # ==========================================================
    # MTF STRUCTURE ANALYSIS
    # ==========================================================

    def _analyze_structure_context(self, candles):

        if not candles:
            return {
                "available": False,
                "swings": [],
                "structure": [],
                "structure_events": [],
                "bias": "UNKNOWN",
            }

        swings = (
            self.swing_detector.detect(
                candles
            )
        )

        classified = (
            self.structure_classifier.classify(
                swings
            )
        )

        structure_events = (
            self.bos_detector.detect(
                classified
            )
        )

        bias = self._derive_structure_bias(
            classified
        )

        return {
            "available": True,
            "swings": swings,
            "structure": classified,
            "structure_events": structure_events,
            "bias": bias,
        }

    # ==========================================================
    # STRUCTURE BIAS
    # ==========================================================

    def _derive_structure_bias(self, classified):

        if not classified:
            return "UNKNOWN"

        bullish_count = 0
        bearish_count = 0

        for structure in classified:

            label = structure.get(
                "label"
            )

            if label in (
                "HH",
                "HL",
            ):
                bullish_count += 1

            elif label in (
                "LH",
                "LL",
            ):
                bearish_count += 1

        if bullish_count > bearish_count:
            return "BULLISH"

        if bearish_count > bullish_count:
            return "BEARISH"

        return "NEUTRAL"

    # ==========================================================
    # MTF CONTEXT
    # ==========================================================

    def _build_mtf_context(
        self,
        m15_candles=None,
        h1_candles=None,
    ):

        h1_context = (
            self._analyze_structure_context(
                h1_candles
            )
            if h1_candles is not None
            else {
                "available": False,
                "swings": [],
                "structure": [],
                "structure_events": [],
                "bias": "UNKNOWN",
            }
        )

        m15_context = (
            self._analyze_structure_context(
                m15_candles
            )
            if m15_candles is not None
            else {
                "available": False,
                "swings": [],
                "structure": [],
                "structure_events": [],
                "bias": "UNKNOWN",
            }
        )

        h1_bias = h1_context["bias"]
        m15_bias = m15_context["bias"]

        if (
            h1_bias != "UNKNOWN"
            and m15_bias != "UNKNOWN"
            and h1_bias == m15_bias
        ):
            higher_timeframe_alignment = (
                "ALIGNED"
            )

        elif (
            h1_bias != "UNKNOWN"
            and m15_bias != "UNKNOWN"
        ):
            higher_timeframe_alignment = (
                "CONFLICTING"
            )

        else:
            higher_timeframe_alignment = (
                "INSUFFICIENT_DATA"
            )

        return {
            "h1": h1_context,
            "m15": m15_context,
            "alignment": higher_timeframe_alignment,
        }

    # ==========================================================
    # MAIN ANALYSIS
    # ==========================================================

    def analyze(
        self,
        candles,
        m15_candles=None,
        h1_candles=None,
    ):

        if not candles:
            raise ValueError(
                "No candles supplied"
            )

        current_candle = candles[-1]

        current_price = float(
            current_candle.close
        )

        # ------------------------------------------------------
        # MTF CONTEXT
        #
        # H1 -> M15 -> M5
        #
        # H1 and M15 provide higher-timeframe
        # structure context.
        #
        # M5 remains the execution timeframe.
        # ------------------------------------------------------

        mtf_context = (
            self._build_mtf_context(
                m15_candles=m15_candles,
                h1_candles=h1_candles,
            )
        )

        # ------------------------------------------------------
        # M5 MARKET STRUCTURE
        # ------------------------------------------------------

        swings = (
            self.swing_detector.detect(
                candles
            )
        )

        classified = (
            self.structure_classifier.classify(
                swings
            )
        )

        structure_events = (
            self.bos_detector.detect(
                classified
            )
        )

        (
            market_swings,
            market_breaks,
        ) = (
            self.market_structure_detector.process(
                candles
            )
        )

        # ------------------------------------------------------
        # LIQUIDITY
        # ------------------------------------------------------

        liquidity = (
            self.liquidity_detector.detect(
                swings
            )
        )

        liquidity = (
            self.liquidity_detector.detect_sweeps(
                liquidity,
                candles,
            )
        )

        # ------------------------------------------------------
        # DISPLACEMENT
        # ------------------------------------------------------

        displacement = (
            self.displacement_detector.detect(
                candles
            )
        )

        # ------------------------------------------------------
        # FVG
        # ------------------------------------------------------

        fvgs = (
            self.fvg_detector.detect(
                candles
            )
        )

        active_fvgs = [
            fvg
            for fvg in fvgs
            if getattr(
                fvg,
                "active",
                True,
            )
            and not getattr(
                fvg,
                "mitigated",
                False,
            )
        ]

        # ------------------------------------------------------
        # PREMIUM / DISCOUNT
        # ------------------------------------------------------

        premium_discount = (
            self.premium_discount_detector.detect(
                swings,
                current_price,
            )
        )

        zone = (
            premium_discount.zone
            if premium_discount
            else "UNKNOWN"
        )

        # ------------------------------------------------------
        # BREAKERS
        # ------------------------------------------------------

        breaker_blocks = (
            self.breaker_block_detector.process(
                candles
            )
        )

        confirmed_breakers = [
            breaker
            for breaker in breaker_blocks
            if getattr(
                breaker,
                "confirmed",
                False,
            )
            and not getattr(
                breaker,
                "invalidated",
                False,
            )
            and not getattr(
                breaker,
                "mitigated",
                False,
            )
        ]

        # ------------------------------------------------------
        # ORDER BLOCKS
        # ------------------------------------------------------

        institutional_order_blocks = (
            self.institutional_order_block_detector.process(
                candles
            )
        )

        active_institutional_obs = [
            ob
            for ob in institutional_order_blocks
            if not getattr(
                ob,
                "mitigated",
                False,
            )
            and not getattr(
                ob,
                "invalidated",
                False,
            )
        ]

        # ------------------------------------------------------
        # SUPPORT / RESISTANCE
        # ------------------------------------------------------

        support_resistance = (
            self.support_resistance_detector.detect(
                candles=candles,
                swings=swings,
            )
        )

        nearest_levels = (
            self.support_resistance_detector.nearest_levels(
                price=current_price,
                levels=support_resistance,
            )
        )

        nearest_support = (
            nearest_levels.get(
                "support"
            )
        )

        nearest_resistance = (
            nearest_levels.get(
                "resistance"
            )
        )

        # ------------------------------------------------------
        # SIGNAL
        # ------------------------------------------------------

        signal = (
            self.signal_engine.generate(
                structure_events=structure_events,
                liquidity_events=liquidity,
                displacement_events=displacement,
                fvg_events=active_fvgs,
                mitigation_events=[],
                zone=zone,
                breaker_blocks=confirmed_breakers,
                institutional_order_blocks=(
                    active_institutional_obs
                ),
                mtf_context=mtf_context,
            )
        )

        # ------------------------------------------------------
        # SWING EXTREMES
        # ------------------------------------------------------

        high_swings = [
            swing
            for swing in swings
            if swing.type == "HIGH"
        ]

        low_swings = [
            swing
            for swing in swings
            if swing.type == "LOW"
        ]

        if high_swings:

            recent_highs = (
                high_swings[-5:]
            )

            swing_high = max(
                swing.price
                for swing in recent_highs
            )

        else:

            swing_high = (
                current_candle.high
            )

        if low_swings:

            recent_lows = (
                low_swings[-5:]
            )

            swing_low = min(
                swing.price
                for swing in recent_lows
            )

        else:

            swing_low = (
                current_candle.low
            )

        # ------------------------------------------------------
        # ENTRY ENGINE
        # ------------------------------------------------------

        entry_setup = (
            self.entry_engine.generate(
                direction=signal.direction,
                current_price=current_price,
                swing_high=swing_high,
                swing_low=swing_low,
                order_blocks=(
                    active_institutional_obs
                ),
                breaker_blocks=(
                    confirmed_breakers
                ),
                fvg_events=active_fvgs,
                candles=candles,
                support_resistance=(
                    support_resistance
                ),
            )
        )

        signal.entry = (
            entry_setup.entry
        )

        signal.stop_loss = (
            entry_setup.stop_loss
        )

        signal.take_profit_1 = (
            entry_setup.take_profit_1
        )

        signal.take_profit_2 = (
            entry_setup.take_profit_2
        )

        signal.risk_reward = (
            entry_setup.risk_reward
        )

        signal.entry_zone = (
            entry_setup.entry_zone
        )

        signal.setup_type = (
            entry_setup.setup_type
        )

        signal.entry_source_time = (
            entry_setup.source_time
        )

        signal.reason = (
            entry_setup.reason
        )

        # ------------------------------------------------------
        # DEBUG / DASHBOARD DATA
        # ------------------------------------------------------

        signal.current_price = (
            current_price
        )

        signal.support_resistance = (
            support_resistance
        )

        signal.nearest_support = (
            nearest_support
        )

        signal.nearest_resistance = (
            nearest_resistance
        )

        signal.swing_high = (
            swing_high
        )

        signal.swing_low = (
            swing_low
        )

        signal.market_swings = (
            market_swings
        )

        signal.market_breaks = (
            market_breaks
        )

        signal.liquidity_events = (
            liquidity
        )

        signal.fvg_events = (
            active_fvgs
        )

        signal.all_fvg_events = (
            fvgs
        )

        signal.breaker_blocks = (
            confirmed_breakers
        )

        signal.order_blocks = (
            active_institutional_obs
        )

        # ------------------------------------------------------
        # MTF DATA
        # ------------------------------------------------------

        signal.mtf_context = (
            mtf_context
        )

        signal.h1_structure = (
            mtf_context["h1"]["structure"]
        )

        signal.h1_structure_events = (
            mtf_context["h1"]["structure_events"]
        )

        signal.h1_bias = (
            mtf_context["h1"]["bias"]
        )

        signal.m15_structure = (
            mtf_context["m15"]["structure"]
        )

        signal.m15_structure_events = (
            mtf_context["m15"]["structure_events"]
        )

        signal.m15_bias = (
            mtf_context["m15"]["bias"]
        )

        signal.mtf_alignment = (
            mtf_context["alignment"]
        )

        # ------------------------------------------------------
        # ENTRY STATUS
        # ------------------------------------------------------

        if entry_setup.status != "VALID":

            signal.trade_valid = False

            signal.validation_reasons = [
                entry_setup.reason
            ]

            signal.setup_status = (
                "WAIT"
            )

            return signal

        # ------------------------------------------------------
        # FINAL VALIDATION
        # ------------------------------------------------------

        validation = (
            self.trade_validator.validate(
                direction=signal.direction,
                entry=signal.entry,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit_1,
                risk_reward=signal.risk_reward,
                mtf_status=signal.mtf_status,
                execution_type=signal.execution_type,
                risk_mode=signal.risk_mode,
            )
        )

        signal.trade_valid = (
            validation.valid
        )

        signal.validation_reasons = (
            validation.reasons
        )

        if validation.valid:

            signal.setup_status = (
                "VALID"
            )

        else:

            signal.setup_status = (
                "WAIT"
            )

        return signal
