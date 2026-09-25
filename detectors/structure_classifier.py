class StructureClassifier:

    def classify(self, swings):

        if len(swings) < 2:
            return []

        classified = []

        previous_high = None
        previous_low = None

        for swing in swings:

            swing = {
                "index": swing.index,
                "time": swing.time,
                "price": swing.price,
                "type": swing.type,
            }

            if swing["type"] == "HIGH":

                if previous_high is None:
                    swing["label"] = "HH"

                elif swing["price"] > previous_high:
                    swing["label"] = "HH"

                else:
                    swing["label"] = "LH"

                previous_high = swing["price"]

            else:

                if previous_low is None:
                    swing["label"] = "LL"

                elif swing["price"] > previous_low:
                    swing["label"] = "HL"

                else:
                    swing["label"] = "LL"

                previous_low = swing["price"]

            classified.append(swing)

        return classified
