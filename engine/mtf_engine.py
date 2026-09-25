from dataclasses import dataclass


@dataclass
class MTFAnalysis:
    h1_bias: str
    m15_context: str
    m5_confirmation: str
    final_direction: str
    status: str
    reasons: list


class MTFEngine:
    """
    Multi-timeframe directional filter.

    Hierarchy:
        H1  = primary market bias
        M15 = confirmation/context
        M5  = entry confirmation

    M5 is not allowed to override H1 by itself.
    """

    VALID_DIRECTIONS = (
        "BULLISH",
        "BEARISH",
        "NONE",
    )

    def _direction_from_breaks(self, breaks):
        """
        Determine directional bias from recent structure breaks.

        Only the most recent meaningful break is used.
        """

        if not breaks:
            return "NONE"

        for event in reversed(breaks):

            direction = getattr(
                event,
                "direction",
                None,
            )

            if direction in self.VALID_DIRECTIONS:
                return direction

            direction = getattr(
                event,
                "trend",
                None,
            )

            if direction in self.VALID_DIRECTIONS:
                return direction

        return "NONE"

    def _recent_structure_direction(
        self,
        structure_events,
    ):
        """
        Read direction from the latest structure event.
        """

        if not structure_events:
            return "NONE"

        for event in reversed(
            structure_events
        ):

            direction = getattr(
                event,
                "direction",
                None,
            )

            if direction in self.VALID_DIRECTIONS:
                return direction

        return "NONE"

    def _resolve_h1_bias(
        self,
        h1_breaks=None,
        h1_structure=None,
    ):
        """
        H1 is the primary directional source.

        Structure events have priority when available.
        """

        structure_direction = (
            self._recent_structure_direction(
                h1_structure
            )
        )

        if structure_direction != "NONE":
            return structure_direction

        return self._direction_from_breaks(
            h1_breaks
        )

    def _resolve_m15_context(
        self,
        m15_breaks=None,
        m15_structure=None,
    ):
        """
        Determine M15 directional context.
        """

        structure_direction = (
            self._recent_structure_direction(
                m15_structure
            )
        )

        if structure_direction != "NONE":
            return structure_direction

        return self._direction_from_breaks(
            m15_breaks
        )

    def _resolve_m5_confirmation(
        self,
        m5_breaks=None,
        m5_structure=None,
    ):
        """
        Determine M5 entry-direction confirmation.
        """

        structure_direction = (
            self._recent_structure_direction(
                m5_structure
            )
        )

        if structure_direction != "NONE":
            return structure_direction

        return self._direction_from_breaks(
            m5_breaks
        )

    def analyze(
        self,
        h1_breaks=None,
        h1_structure=None,
        m15_breaks=None,
        m15_structure=None,
        m5_breaks=None,
        m5_structure=None,
    ):
        """
        Resolve the complete H1 -> M15 -> M5 hierarchy.

        Rules:

        1. H1 establishes primary bias.
        2. M15 must agree with H1.
        3. M5 must agree with both H1 and M15.
        4. If any timeframe disagrees or is unclear,
           final direction becomes NONE.
        """

        h1_breaks = h1_breaks or []
        h1_structure = h1_structure or []
        m15_breaks = m15_breaks or []
        m15_structure = m15_structure or []
        m5_breaks = m5_breaks or []
        m5_structure = m5_structure or []

        reasons = []

        h1_bias = self._resolve_h1_bias(
            h1_breaks=h1_breaks,
            h1_structure=h1_structure,
        )

        m15_context = self._resolve_m15_context(
            m15_breaks=m15_breaks,
            m15_structure=m15_structure,
        )

        m5_confirmation = self._resolve_m5_confirmation(
            m5_breaks=m5_breaks,
            m5_structure=m5_structure,
        )

        if h1_bias == "NONE":

            reasons.append(
                "H1 has no clear directional bias"
            )

            return MTFAnalysis(
                h1_bias=h1_bias,
                m15_context=m15_context,
                m5_confirmation=m5_confirmation,
                final_direction="NONE",
                status="NO TRADE",
                reasons=reasons,
            )

        reasons.append(
            f"H1 bias: {h1_bias}"
        )

        if m15_context == "NONE":

            reasons.append(
                "M15 has no clear directional context"
            )

            return MTFAnalysis(
                h1_bias=h1_bias,
                m15_context=m15_context,
                m5_confirmation=m5_confirmation,
                final_direction="NONE",
                status="WAIT",
                reasons=reasons,
            )

        reasons.append(
            f"M15 context: {m15_context}"
        )

        if m15_context != h1_bias:

            reasons.append(
                "M15 conflicts with H1 bias"
            )

            return MTFAnalysis(
                h1_bias=h1_bias,
                m15_context=m15_context,
                m5_confirmation=m5_confirmation,
                final_direction="NONE",
                status="WAIT",
                reasons=reasons,
            )

        reasons.append(
            "H1 and M15 are aligned"
        )

        if m5_confirmation == "NONE":

            reasons.append(
                "M5 has no entry confirmation"
            )

            return MTFAnalysis(
                h1_bias=h1_bias,
                m15_context=m15_context,
                m5_confirmation=m5_confirmation,
                final_direction="NONE",
                status="WAIT",
                reasons=reasons,
            )

        reasons.append(
            f"M5 confirmation: {m5_confirmation}"
        )

        if m5_confirmation != h1_bias:

            reasons.append(
                "M5 is counter-directional to HTF bias"
            )

            return MTFAnalysis(
                h1_bias=h1_bias,
                m15_context=m15_context,
                m5_confirmation=m5_confirmation,
                final_direction="NONE",
                status="WAIT",
                reasons=reasons,
            )

        reasons.append(
            "H1 → M15 → M5 fully aligned"
        )

        return MTFAnalysis(
            h1_bias=h1_bias,
            m15_context=m15_context,
            m5_confirmation=m5_confirmation,
            final_direction=h1_bias,
            status="ALIGNED",
            reasons=reasons,
        )
