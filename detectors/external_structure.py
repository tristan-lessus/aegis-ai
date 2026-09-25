class ExternalStructure:

    def __init__(self, min_move=0.0015):
        """
        min_move = minimum percentage move between swings.
        Prevents tiny internal swings from becoming market structure.
        """
        self.min_move = min_move

    def filter(self, swings):

        if len(swings) < 2:
            return swings

        filtered = [swings[0]]

        last_price = swings[0].price

        for swing in swings[1:]:

            move = abs(swing.price - last_price) / last_price

            if move >= self.min_move:
                filtered.append(swing)
                last_price = swing.price

        return filtered
