import re


class SearchQueryGenerator:

    def __init__(self):
        pass

    # ---------------------------------------------------------
    # LOCATION
    # ---------------------------------------------------------

    def find_location(self, text):

        text = text.lower()

        locations = [
            "el nido",
            "palawan",
            "coron",
            "busuanga",
            "bali",
            "barbados",
            "curacao",
            "maldives",
            "phuket",
            "bangkok",
            "thailand",
            "philippines",
            "mexico",
            "hawaii",
            "jamaica",
            "dubai",
            "singapore",
            "malaysia",
            "seychelles",
            "mauritius",
            "fiji",
            "sri lanka",
            "vijayawada",
        ]

        for location in locations:
            if location in text:
                return location

        return ""

    # ---------------------------------------------------------
    # SPECIFIC VISUAL KEYWORDS
    # Multiple matches are combined
    # ---------------------------------------------------------

    def specific_visual_query(self, text):

        # -----------------------------------------------------
        # PET-FRIENDLY / SERVICE ANIMALS
        # -----------------------------------------------------

        pet_rules = [
            ([
                "pets are allowed",
                "pets are welcome",
                "pet friendly",
                "pet-friendly",
                "pet friendly hotel",
                "dogs are allowed",
                "dogs are welcome",
                "cats are allowed",
                "cats are welcome",
            ], "pet friendly hotel dog"),

            ([
                "service animal",
                "service animals",
                "service dog",
                "guide dog",
                "assistance dog",
                "assistance animal",
            ], "service dog hotel travel"),
        ]

        for keywords, query in pet_rules:
            if any(keyword in text for keyword in keywords):
                return query


        visuals = []

        categories = [

            # PETS
            ([
                "dog", "dogs", "cat", "cats", "pet", "pets",
                "pet policy", "pet fee",
            ], "pet friendly hotel dog"),

            # SERVICE ANIMALS
            ([
                "service animal", "service dog", "guide dog",
                "assistance animal",
            ], "service dog hotel travel"),

            # ROOM
            (
                [
                    "bed",
                    "bedroom",
                    "king bed",
                    "queen bed",
                    "twin beds",
                    "mattress",
                    "pillow",
                    "extra bed",
                    "crib",
                    "cot",
                ],
                "hotel bedroom bed",
            ),

            # AC
            (
                [
                    "air conditioning",
                    "air conditioner",
                    "air-conditioned",
                    "air conditioned",
                    "central air",
                    "climate control",
                ],
                "air conditioner",
            ),

            # WIFI
            (
                [
                    "wi-fi",
                    "wifi",
                    "wireless internet",
                    "internet access",
                    "free internet",
                    "high-speed internet",
                ],
                "hotel wifi",
            ),

            # TV
            (
                [
                    "television",
                    "tv",
                    "smart tv",
                    "flat-screen tv",
                    "flat screen tv",
                ],
                "hotel room television",
            ),

            # PARKING
            (
                [
                    "parking",
                    "car park",
                    "parking lot",
                    "parking garage",
                    "free parking",
                    "complimentary parking",
                ],
                "hotel parking cars",
            ),

            # SHUTTLE
            (
                [
                    "shuttle",
                    "hotel shuttle",
                    "airport transfer",
                    "airport shuttle",
                    "airport transportation",
                    "transfer service",
                ],
                "hotel shuttle airport transfer",
            ),

            # CAR RENTAL
            (
                [
                    "car rental",
                    "rental car",
                    "rent a car",
                    "hire a car",
                ],
                "car rental travel",
            ),

            # BATHROOM
            (
                [
                    "bathroom",
                    "shower",
                    "bathtub",
                    "walk-in shower",
                    "toilet",
                    "toiletries",
                    "hairdryer",
                    "hair dryer",
                ],
                "luxury hotel bathroom shower",
            ),

            # FRIDGE / MINIBAR
            (
                [
                    "mini-fridge",
                    "mini fridge",
                    "minibar",
                    "mini bar",
                    "refrigerator",
                    "fridge",
                ],
                "hotel room mini fridge",
            ),

            # COFFEE
            (
                [
                    "coffee maker",
                    "coffee machine",
                    "tea maker",
                    "kettle",
                    "electric kettle",
                ],
                "hotel room coffee maker",
            ),

            # BREAKFAST
            (
                [
                    "breakfast",
                    "breakfast buffet",
                    "morning meal",
                ],
                "hotel breakfast buffet",
            ),

            # RESTAURANT
            (
                [
                    "restaurant",
                    "dining",
                    "dinner",
                    "lunch",
                    "buffet",
                    "meal",
                    "food",
                    "cafe",
                ],
                "hotel restaurant dining",
            ),

            # BAR / LOUNGE
            (
                [
                    "bar",
                    "cocktail",
                    "drinks",
                    "beverages",
                    "lounge",
            ],
                "hotel lounge drinks",
            ),

            # POOL
            (
                [
                    "swimming pool",
                    "pool",
                    "infinity pool",
                    "outdoor pool",
                    "indoor pool",
                    "poolside",
                    "pool area",
                ],
                "luxury resort swimming pool",
            ),

            # JACUZZI
            (
                [
                    "hot tub",
                    "jacuzzi",
                    "whirlpool",
                ],
                "hotel jacuzzi hot tub",
            ),

            # BEACH
            (
                [
                    "beach access",
                    "private beach",
                    "beachfront",
                    "beach front",
                ],
                "beachfront tropical resort",
            ),

            # OCEAN
            (
                [
                    "ocean",
                    "sea",
                    "seaside",
                    "oceanfront",
                    "seafront",
                ],
                "tropical ocean resort",
            ),

            # BALCONY
            (
                [
                    "balcony",
                    "terrace",
                    "private terrace",
                    "patio",
                    "veranda",
                ],
                "luxury hotel balcony terrace",
            ),

            # VIEWS
            (
                [
                    "ocean view",
                    "sea view",
                    "water view",
                    "mountain view",
                    "garden view",
                    "city view",
                    "scenic view",
                    "panoramic view",
                ],
                "hotel scenic view balcony",
            ),

            # GYM
            (
                [
                    "gym",
                    "fitness center",
                    "fitness centre",
                    "fitness room",
                    "workout",
                    "exercise",
                ],
                "hotel gym fitness center",
            ),

            # TENNIS
            (
                [
                    "tennis",
                    "tennis court",
                ],
                "hotel tennis court",
            ),

            # GOLF
            (
                [
                    "golf",
                    "golf course",
                    "golf club",
                ],
                "resort golf course",
            ),

            # BASKETBALL
            (
                [
                    "basketball",
                    "basketball court",
                ],
                "hotel basketball court",
            ),

            # VOLLEYBALL
            (
                [
                    "volleyball",
                    "beach volleyball",
                ],
                "resort volleyball",
            ),

            # BADMINTON
            (
                [
                    "badminton",
                ],
                "hotel badminton court",
            ),

            # TABLE TENNIS
            (
                [
                    "table tennis",
                    "ping pong",
                ],
                "hotel table tennis",
            ),

            # BILLIARDS
            (
                [
                    "billiards",
                    "pool table",
                    "snooker",
                ],
                "hotel billiards pool table",
            ),

            # WATER SPORTS
            (
                [
                    "water sports",
                    "watersports",
                    "water sport",
                ],
                "tropical resort water sports",
            ),

            # SNORKELING
            (
                [
                    "snorkeling",
                    "snorkelling",
                ],
                "tropical snorkeling",
            ),

            # DIVING
            (
                [
                    "scuba diving",
                    "diving",
                    "dive",
                ],
                "tropical scuba diving",
            ),

            # KAYAKING
            (
                [
                    "kayaking",
                    "kayak",
                ],
                "tropical kayaking",
            ),

            # PADDLEBOARD
            (
                [
                    "paddleboard",
                    "paddle boarding",
                    "stand up paddle",
                ],
                "tropical paddle boarding",
            ),

            # SURFING
            (
                [
                    "surfing",
                    "surf",
                ],
                "tropical surfing",
            ),

            # CANOE
            (
                [
                    "canoeing",
                    "canoe",
                ],
                "tropical canoeing",
            ),

            # SAILING
            (
                [
                    "sailing",
                    "sailboat",
                    "boat trip",
                ],
                "tropical sailing boat",
            ),

            # BOAT / ISLAND TOUR
            (
                [
                    "boat tour",
                    "boat trip",
                    "island hopping",
                    "island tour",
                ],
                "tropical island boat tour",
            ),

            # HIKING
            (
                [
                    "hiking",
                    "hike",
                    "trekking",
                    "trek",
                ],
                "tropical hiking adventure",
            ),

            # CYCLING
            (
                [
                    "cycling",
                    "bicycle",
                    "bike",
                    "biking",
                ],
                "tropical cycling vacation",
            ),

            # WALKING
            (
                [
                    "walking tour",
                    "nature walk",
                    "walking trail",
                ],
                "tropical nature walk",
            ),

            # SIGHTSEEING
            (
                [
                    "sightseeing",
                    "city tour",
                    "guided tour",
                    "tour",
                ],
                "travel sightseeing tour",
            ),

            # ACTIVITIES
            (
                [
                    "activity",
                    "activities",
                    "things to do",
                    "recreation",
                ],
                "resort vacation activities",
            ),

            # SPA
            (
                [
                    "spa",
                    "massage",
                    "wellness",
                    "sauna",
                    "steam room",
                    "steam bath",
                ],
                "luxury hotel spa wellness",
            ),

            # YOGA
            (
                [
                    "yoga",
                    "yoga class",
                    "meditation",
                ],
                "resort yoga meditation",
            ),

            # LOBBY
            (
                [
                    "lobby",
                    "reception",
                    "front desk",
                    "check-in",
                    "check in",
                    "check-out",
                    "check out",
                ],
                "luxury hotel lobby reception",
            ),

            # STAFF
            (
                [
                    "staff",
                    "friendly staff",
                    "helpful staff",
                    "hospitality",
                    "service",
                    "housekeeping",
                    "concierge",
                ],
                "hotel staff hospitality service",
            ),

            # ROOM SERVICE
            (
                [
                    "room service",
                    "in-room dining",
                    "in room dining",
                ],
                "hotel room service food",
            ),

            # KIDS
            (
                [
                    "kids",
                    "children",
                    "kids club",
                    "family activities",
                    "playground",
                    "play area",
                ],
                "family resort kids activities",
            ),

            # FAMILY
            (
                [
                    "family friendly",
                    "family-friendly",
                    "family vacation",
                ],
                "family friendly resort",
            ),

            # BUSINESS
            (
                [
                    "business center",
                    "business centre",
                    "meeting room",
                    "conference room",
                    "conference",
                    "meeting",
                    "workspace",
                    "work space",
                ],
                "hotel business conference room",
            ),

            # LAUNDRY
            (
                [
                    "laundry",
                    "laundry service",
                    "washing machine",
                    "dry cleaning",
                ],
                "hotel laundry service",
            ),

            # SHOPPING
            (
                [
                    "shopping",
                    "shopping center",
                    "shopping centre",
                    "gift shop",
                    "souvenir",
                    "shops",
                ],
                "hotel shopping vacation",
            ),

            # GARDEN
            (
                [
                    "garden",
                    "gardens",
                    "tropical garden",
                    "landscaped grounds",
                ],
                "tropical resort garden",
            ),

            # ACCESSIBILITY
            (
                [
                    "wheelchair",
                    "accessible room",
                    "accessibility",
                    "wheelchair accessible",
                    "accessible bathroom",
                ],
                "wheelchair accessible hotel",
            ),

            # SECURITY
            (
                [
                    "security",
                    "security guard",
                    "24-hour security",
                    "safe and secure",
                ],
                "hotel security entrance",
            ),

            # ENTRANCE
            (
                [
                    "entrance",
                    "hotel entrance",
                    "front entrance",
                    "driveway",
                    "arrival",
                ],
                "luxury hotel entrance arrival",
            ),

            # OUTDOOR AREA
            (
                [
                    "outdoor area",
                    "outdoor space",
                    "grounds",
                    "courtyard",
                    "terrace area",
                ],
                "luxury resort outdoor area",
            ),

            # PAYMENT / CREDIT CARD
            (
                [
                    "credit card",
                    "debit card",
                    "card payment",
                    "card payments",
                    "pay by card",
                    "payment card",
                    "credit or debit card",
                    "credit and debit card",
                ],
                "credit card debit card payment",
            ),

            # PAYMENT / CHECKOUT
            (
                [
                    "payment",
                    "paying by card",
                    "checkout",
                    "security deposit",
                    "refundable deposit",
                    "deposit required",
                    "cash payment",
                ],
                "hotel payment checkout",
            ),

            (
                [
                    "credit card",
                    "debit card",
                    "card payment",
                    "card payments",
                    "pay by card",
                    "payment card",
                    "credit or debit card",
                    "credit and debit card",
                ],
                "credit card debit card payment",
            ),

            # payment-related And terms

            (
                [
                    "paying by card",
                    "security deposit",
                    "cash payment",
                ],
                "hotel payment checkout",
            ),

            # NATURE
            (
                [
                    "nature",
                    "jungle",
                    "forest",
                    "waterfall",
                    "river",
                    "lagoon",
                    "wildlife",
                ],
                "tropical nature travel",
            ),

            # ATTRACTIONS
            (
                [
                    "attraction",
                    "attractions",
                    "nearby attractions",
                    "landmark",
                    "landmarks",
                ],
                "travel destination attractions",
            ),
        ]

        for keywords, query in categories:

            matched = False

            for keyword in keywords:

                if keyword in text:

                    matched = True
                    break

            if matched:

                visuals.append(query)

        # -----------------------------------------------------
        # REMOVE DUPLICATES
        # -----------------------------------------------------

        unique = []

        for visual in visuals:

            if visual not in unique:

                unique.append(visual)

        # -----------------------------------------------------
        # LIMIT QUERY LENGTH
        # Pexels works better with concise queries
        # -----------------------------------------------------

        if unique:

            words = []

            for visual in unique:

                for word in visual.split():

                    if word not in words:

                        words.append(word)

            # Keep Pexels queries focused.
            # Three visual concepts are usually enough.
            return " ".join(words[:10])

        return None

    # ---------------------------------------------------------
    # POLICY / NEGATIVE STATEMENTS
    # ---------------------------------------------------------

    def policy_query(self, text):

        rules = [
            ([
                "pets aren't allowed",
                "pets are not allowed",
                "pet not allowed",
                "pets not permitted",
                "no pets",
                "pets prohibited",
            ], "hotel no pets policy"),

            ([
                "no smoking",
                "smoking is not allowed",
                "smoking isn't allowed",
                "non-smoking",
                "non smoking",
            ], "hotel no smoking"),

            ([
                "no parking",
                "no on-site parking",
                "no onsite parking",
                "parking is not available",
                "parking isn't available",
            ], "hotel parking unavailable"),

            ([
                "no wifi",
                "no wi-fi",
                "wifi is not available",
                "wi-fi is not available",
            ], "hotel wifi unavailable"),

            ([
                "no elevator",
                "elevator is not available",
                "no lift",
                "no lift available",
            ], "hotel elevator"),

            ([
                "no breakfast",
                "breakfast is not included",
                "breakfast isn't included",
            ], "hotel breakfast"),
        ]

        for keywords, query in rules:
            if any(keyword in text for keyword in keywords):
                return query

        return None

    # ---------------------------------------------------------
    # SEARCH QUERY
    # ---------------------------------------------------------

    def generate(self, text, scene="general"):

        text = text.lower().strip()

        location = self.find_location(text)

        # =====================================================
        # POLICY / NEGATIVE STATEMENTS FIRST
        # =====================================================

        policy = self.policy_query(text)

        if policy:
            return f"{policy} {location}".strip()

        # =====================================================
        # SPECIFIC VISUALS FIRST
        # =====================================================

        specific = self.specific_visual_query(text)

        if specific:

            if location:
                return f"{specific} {location}"

            return specific

        # =====================================================
        # ROOM
        # =====================================================

        if scene == "room":

            query = "luxury hotel room"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # BATHROOM
        # =====================================================

        if scene == "bathroom":

            query = "luxury hotel bathroom"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # POOL
        # =====================================================

        if scene == "pool":

            query = "luxury resort swimming pool"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # BEACH
        # =====================================================

        if scene == "beach":

            query = "tropical beach resort"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # RESTAURANT
        # =====================================================

        if scene == "restaurant":

            query = "luxury hotel restaurant dining"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # BAR
        # =====================================================

        if scene == "bar":

            query = "luxury resort bar lounge"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # SPA
        # =====================================================

        if scene == "spa":

            query = "luxury resort spa wellness"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # GYM
        # =====================================================

        if scene == "gym":

            query = "luxury hotel fitness gym"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # LOBBY
        # =====================================================

        if scene == "lobby":

            query = "luxury hotel lobby reception"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # BALCONY
        # =====================================================

        if scene == "balcony":

            query = "luxury hotel balcony ocean view"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # KIDS
        # =====================================================

        if scene == "kids":

            query = "family resort kids activities"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # HOTEL EXTERIOR
        # =====================================================

        if scene == "outside":

            query = "luxury tropical hotel resort exterior"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # SERVICE
        # =====================================================

        service_words = [
            "service",
            "staff",
            "friendly",
            "helpful",
            "hospitality",
            "welcome",
            "welcoming",
        ]

        if any(
            word in text
            for word in service_words
        ):

            return "luxury hotel staff hospitality"

        # =====================================================
        # FOOD
        # =====================================================

        food_words = [
            "food",
            "meal",
            "breakfast",
            "dinner",
            "lunch",
            "buffet",
            "restaurant",
            "dining",
        ]

        if any(
            word in text
            for word in food_words
        ):

            query = "luxury hotel restaurant dining"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # BEACH / ISLAND
        # =====================================================

        travel_words = [
            "island",
            "islands",
            "beach",
            "ocean",
            "sea",
            "coast",
            "shore",
            "lagoon",
        ]

        if any(
            word in text
            for word in travel_words
        ):

            query = "tropical island beach"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # ATTRACTIONS
        # =====================================================

        attraction_words = [
            "attraction",
            "attractions",
            "explore",
            "exploring",
            "sightseeing",
            "tour",
            "tours",
            "destination",
            "nearby",
            "area",
        ]

        if any(
            word in text
            for word in attraction_words
        ):

            if location:
                return f"{location} travel attractions"

            return "tropical destination travel attractions"

        # =====================================================
        # RATINGS / REVIEWS / PRICE
        # =====================================================

        rating_words = [
            "rating",
            "ratings",
            "rated",
            "review",
            "reviews",
            "score",
            "google",
            "tripadvisor",
            "price",
            "prices",
            "cost",
            "value",
            "budget",
            "expensive",
            "affordable",
        ]

        if any(
            word in text
            for word in rating_words
        ):

            return "luxury hotel resort exterior"

        # =====================================================
        # HOTEL / PROPERTY
        # =====================================================

        hotel_words = [
            "hotel",
            "resort",
            "property",
            "accommodation",
            "stay",
            "vacation",
        ]

        if any(
            word in text
            for word in hotel_words
        ):

            query = "luxury tropical hotel resort"

            if location:
                query += f" {location}"

            return query

        # =====================================================
        # GENERAL FALLBACK
        # =====================================================

        return "luxury tropical hotel resort"
