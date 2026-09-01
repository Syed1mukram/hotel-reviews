import re


class SearchQueryGenerator:

    def __init__(self):
        pass

    # ---------------------------------------------------------
    # LOCATION
    # Generic extraction — no hardcoded destination list
    # ---------------------------------------------------------

    def find_location(self, text):
        text = re.sub(r"\s+", " ", text.lower().strip())

        patterns = [
            r"\b(?:in|at|from|near|around|outside|within)\s+"
            r"([a-z][a-z .'-]{2,50}?)(?=\s+(?:and|but|with|where|which|"
            r"that|this|the|is|are|was|were|has|have|offers|features|"
            r"provides|you|we|it|they)\b|[,.!?]|$)",

            r"\b(?:located|situated|based)\s+(?:in|at|near)\s+"
            r"([a-z][a-z .'-]{2,50}?)(?=\s+(?:and|but|with|where|which|"
            r"that|this|the|is|are|was|were|has|have|offers|features|"
            r"provides|you|we|it|they)\b|[,.!?]|$)",
        ]

        stop_words = {
            "the", "hotel", "resort", "property", "area", "city",
            "country", "there", "here", "this", "that", "a", "an",
            "major attractions", "major attraction"
        }

        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue

            location = re.sub(r"\s+", " ", match.group(1).strip(" ,.-"))

            # Avoid capturing an ordinary noun phrase as a destination.
            if location in stop_words:
                continue

            # Keep the extracted location compact.
            words = location.split()
            if len(words) > 6:
                location = " ".join(words[:6])

            if len(location) >= 3:
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
                "hotel parking lot cars",
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
                    "scuba dive",
                    "dive center",
                    "dive centre",
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


            # TOILETRIES / ROOM AMENITIES
            (
                [
                    "toiletries", "toiletry", "shampoo", "conditioner",
                    "soap", "body wash", "toothbrush", "toothpaste",
                    "towels", "bathrobe", "slippers",
                ],
                "hotel room toiletries amenities",
            ),

            # HOUSEKEEPING / CLEANING
            (
                [
                    "cleaning", "clean", "housekeeping service",
                    "cleaned", "cleanliness", "room cleaning",
                ],
                "hotel housekeeping room cleaning",
            ),

            # LOCATION / CENTRAL LOCATION
            (
                [
                    "centrally located", "central location",
                    "central", "located near", "close to",
                    "nearby", "walking distance",
                ],
                "hotel location city attractions",
            ),

            # CITY / DOWNTOWN
            (
                [
                    "downtown", "city center", "city centre",
                    "town center", "town centre",
                ],
                "city center hotel location",
            ),

            # LANDMARKS / TEMPLES / MUSEUMS
            (
                [
                    "temple", "temples", "church", "mosque",
                    "museum", "museums", "landmark", "monument",
                ],
                "tourist landmark temple museum",
            ),

            # TRANSPORTATION
            (
                [
                    "taxi", "taxis", "bus", "buses", "transport",
                    "transportation", "public transport", "airport",
                    "airport transfer", "transfer",
                ],
                "travel transportation taxi airport",
            ),

            # CHECK-IN / CHECK-OUT
            (
                [
                    "check-in", "check in", "check-out", "check out",
                    "arrival", "departure",
                ],
                "hotel check in reception",
            ),

            # RESERVATION / BOOKING
            (
                [
                    "reservation", "reservations", "booking", "book",
                    "booked", "availability",
                ],
                "hotel booking reservation",
            ),

            # PRICE / VALUE
            (
                [
                    "price", "prices", "cost", "value", "budget",
                    "expensive", "affordable", "cheap", "rate", "rates",
                    "per night",
                ],
                "hotel price booking value",
            ),

            # ROOM SIZE / LAYOUT
            (
                [
                    "spacious room", "large room", "small room",
                    "room size", "living room", "sitting area",
                    "suite", "suites",
                ],
                "spacious hotel room suite",
            ),

            # BED / SLEEP QUALITY
            (
                [
                    "comfortable bed", "comfortable beds",
                    "good sleep", "sleep quality", "sleeping",
                    "comfortable mattress",
                ],
                "comfortable hotel bed bedroom",
            ),

            # VIEW / SCENERY
            (
                [
                    "sunset", "sunrise", "scenery", "scenic",
                    "panoramic", "view",
                ],
                "hotel scenic sunset view",
            ),

            # WIFI QUALITY
            (
                [
                    "fast wifi", "fast wi-fi", "strong wifi",
                    "strong wi-fi", "internet was fast",
                    "internet worked", "wifi worked",
                ],
                "hotel wifi internet connection",
            ),

            # ELEVATOR
            (
                [
                    "elevator", "lift", "lifts",
                ],
                "hotel elevator lift",
            ),

            # SMOKING
            (
                [
                    "smoking", "smoke", "smoking area",
                ],
                "hotel smoking area policy",
            ),

            # SAFETY / SECURITY
            (
                [
                    "safe", "safety", "secure", "security",
                    "security guard", "24-hour security",
                ],
                "hotel security safety entrance",
            ),

            # ACCESS / ENTRANCE
            (
                [
                    "entrance", "entrance area", "driveway",
                    "arrival area", "front door", "main door",
                ],
                "hotel entrance arrival",
            ),

            # STAFF / HOSPITALITY
            (
                [
                    "staff", "friendly staff", "helpful staff",
                    "hospitality", "welcoming", "welcome",
                    "receptionist", "concierge",
                ],
                "hotel staff hospitality service",
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

                if re.search(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])", text):

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
            if any(
                re.search(
                    r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])",
                    text,
                )
                for keyword in keywords
            ):
                return query

        return None

    # ---------------------------------------------------------
    # SEARCH QUERY
    # ---------------------------------------------------------

    def extract_visual_keywords(self, script_text, max_keywords=60):
        """
        Extract hotel/travel visual concepts directly from the supplied script.
        No hardcoded destination list is required.
        Returns unique keywords in first-appearance order.
        """
        text = re.sub(r"\s+", " ", str(script_text).lower()).strip()

        keyword_patterns = [
            ("hotel exterior", [r"\bhotel\b", r"\bresort\b", r"\bproperty\b",
                                r"\bentrance\b", r"\bexterior\b"]),
            ("hotel room", [r"\broom\b", r"\brooms\b", r"\bbedroom\b",
                            r"\bsuite\b", r"\baccommodation\b"]),
            ("hotel bathroom", [r"\bbathroom\b", r"\bshower\b", r"\bbathtub\b",
                                 r"\btoilet\b"]),
            ("balcony", [r"\bbalcony\b", r"\bterrace\b", r"\bpatio\b",
                         r"\bveranda\b"]),
            ("room view", [r"\bocean view\b", r"\bsea view\b", r"\bwater view\b",
                           r"\bmountain view\b", r"\bgarden view\b",
                           r"\bcity view\b", r"\bscenic view\b"]),
            ("air conditioning", [r"\bair conditioning\b", r"\bair conditioner\b",
                                   r"\bair-conditioned\b"]),
            ("wifi", [r"\bwi[\s-]?fi\b", r"\bwireless internet\b",
                      r"\binternet access\b"]),
            ("television", [r"\btelevision\b", r"\bsmart tv\b", r"\bflat[\s-]?screen tv\b"]),
            ("mini fridge", [r"\bmini[\s-]?fridge\b", r"\bmini[\s-]?bar\b",
                             r"\bminibar\b", r"\brefrigerator\b"]),
            ("coffee maker", [r"\bcoffee maker\b", r"\bcoffee machine\b",
                              r"\bkettle\b"]),
            ("bed", [r"\bking bed\b", r"\bqueen bed\b", r"\btwin beds?\b",
                     r"\bbed\b", r"\bmattress\b"]),
            ("toiletries", [r"\btoiletries?\b", r"\bshampoo\b", r"\bsoap\b",
                            r"\btowels?\b", r"\bbody wash\b"]),
            ("breakfast", [r"\bbreakfast\b", r"\bbreakfast buffet\b"]),
            ("restaurant", [r"\brestaurant\b", r"\bdining\b", r"\bdinner\b",
                            r"\blunch\b", r"\bmeal\b", r"\bbuffet\b"]),
            ("room service", [r"\broom service\b", r"\bin-room dining\b",
                              r"\bin room dining\b"]),
            ("pool", [r"\bswimming pool\b", r"\binfinity pool\b",
                      r"\bpool\b", r"\bpoolside\b"]),
            ("gym", [r"\bgym\b", r"\bfitness center\b", r"\bfitness centre\b"]),
            ("spa", [r"\bspa\b", r"\bmassage\b", r"\bwellness\b",
                     r"\bsauna\b"]),
            ("staff", [r"\bstaff\b", r"\bhospitality\b", r"\bconcierge\b",
                       r"\breceptionist\b"]),
            ("housekeeping", [r"\bhousekeeping\b", r"\bcleanliness\b",
                              r"\bcleaning\b", r"\bspotless\b"]),
            ("parking", [r"\bparking\b", r"\bcar park\b", r"\bparking lot\b"]),
            ("airport", [r"\bairport\b", r"\bairport transfer\b",
                         r"\bairport shuttle\b"]),
            ("transportation", [r"\btransportation\b", r"\btransport\b",
                                r"\btaxi\b", r"\bshuttle\b", r"\bbus\b"]),
            ("check in", [r"\bcheck-in\b", r"\bcheck in\b", r"\barrival\b"]),
            ("check out", [r"\bcheck-out\b", r"\bcheck out\b", r"\bdeparture\b"]),
            ("booking", [r"\bbooking\b", r"\breservation\b", r"\breserve\b"]),
            ("family", [r"\bfamily\b", r"\bfamilies\b", r"\bkids\b",
                        r"\bchildren\b"]),
            ("business", [r"\bbusiness center\b", r"\bmeeting\b",
                           r"\bconference\b", r"\bworkspace\b"]),
            ("museum", [r"\bmuseum\b", r"\barchaeological\b"]),
            ("temple", [r"\btemple\b", r"\btemples\b"]),
            ("landmark", [r"\blandmark\b", r"\bmonument\b",
                          r"\bhistoric site\b", r"\bhistorical site\b"]),
            ("attractions", [r"\battraction\b", r"\battractions\b",
                             r"\bsightseeing\b", r"\bthings to do\b"]),
            ("beach", [r"\bbeach\b", r"\bbeachfront\b", r"\bocean\b",
                       r"\bsea\b", r"\bcoast\b", r"\blagoon\b"]),
            ("island", [r"\bisland\b", r"\bislands\b"]),
            ("nature", [r"\bnature\b", r"\bjungle\b", r"\bforest\b",
                        r"\bwaterfall\b", r"\bwildlife\b"]),
            ("snorkeling", [r"\bsnorkeling\b", r"\bsnorkelling\b"]),
            ("diving", [r"\bscuba diving\b", r"\bdiving\b"]),
            ("kayaking", [r"\bkayaking\b", r"\bkayak\b"]),
            ("surfing", [r"\bsurfing\b", r"\bsurf\b"]),
            ("hiking", [r"\bhiking\b", r"\bhike\b", r"\btrekking\b"]),
            ("cycling", [r"\bcycling\b", r"\bbicycle\b", r"\bbiking\b"]),
            ("golf", [r"\bgolf\b", r"\bgolf course\b"]),
            ("tennis", [r"\btennis\b"]),
            ("water sports", [r"\bwater sports\b", r"\bwatersports\b"]),
            ("credit card payment", [r"\bcredit card\b", r"\bdebit card\b",
                                     r"\bpayment\b"]),
            ("price", [r"\bprice\b", r"\bprices\b", r"\bcost\b",
                       r"\bbudget\b", r"\baffordable\b", r"\bper night\b"]),
            ("reviews", [r"\breview\b", r"\breviews\b", r"\brating\b",
                         r"\bratings\b", r"\bscore\b"]),
        ]

        found = []
        for label, patterns in keyword_patterns:
            if any(re.search(pattern, text) for pattern in patterns):
                found.append(label)
                if len(found) >= max_keywords:
                    break

        return found

    def match_visual_keywords(self, sentence, keywords):
        """
        Rank extracted script keywords for one sentence.
        Matching is order-independent and based on keyword concepts.
        """
        text = re.sub(r"\s+", " ", str(sentence).lower()).strip()
        matches = []

        for keyword in keywords:
            parts = keyword.split()
            if all(re.search(r"(?<![a-z0-9])" + re.escape(part) +
                             r"(?![a-z0-9])", text) for part in parts):
                matches.append(keyword)

        return matches


    def generate(self, text, scene="general"):
        text = re.sub(r"\s+", " ", text.lower().strip())
        location = self.find_location(text)

        def q(base):
            return f"{base} {location}".strip() if location else base

        def has(*words):
            return any(re.search(r"(?<![a-z0-9])"+re.escape(w)+r"(?![a-z0-9])", text) for w in words)

        # Negative/policy statements first: never show the positive opposite.
        negatives = [
            (("no on-site parking","no onsite parking","no parking","parking is not available","parking isn't available"), "hotel parking unavailable"),
            (("pets aren't allowed","pets are not allowed","no pets","pets not permitted","pets prohibited"), "hotel no pets policy"),
            (("no smoking","smoking is not allowed","smoking isn't allowed","non-smoking","non smoking"), "hotel no smoking policy"),
            (("no wifi","no wi-fi","wifi is not available","wi-fi is not available"), "hotel wifi unavailable"),
            (("no elevator","no lift","elevator is not available"), "hotel elevator unavailable"),
            (("no breakfast","breakfast is not included","breakfast isn't included"), "hotel breakfast unavailable"),
            (("no cafe","no café","no cafeteria","cafeteria is not available"), "hotel cafe unavailable"),
            (("no cribs","no crib","cribs are not available"), "hotel crib unavailable"),
            (("doesn't offer toiletries","does not offer toiletries","no toiletries","toiletries are not provided"), "hotel toiletries unavailable"),
        ]
        for words, base in negatives:
            if has(*words): return q(base)

        # Very specific visual subjects. Ordered from specific to broad.
        rules = [
            (("air conditioning","air conditioner","air-conditioned","air conditioned","climate control"), "hotel room air conditioning"),
            (("wi-fi","wifi","wireless internet","internet access","free internet","high-speed internet"), "hotel wifi internet"),
            (("television","tv","smart tv","flat-screen tv","flat screen tv"), "hotel room television"),
            (("mini-fridge","mini fridge","minibar","mini bar","refrigerator","fridge"), "hotel room mini fridge"),
            (("coffee maker","coffee machine","tea maker","kettle","electric kettle"), "hotel room coffee maker"),
            (("toiletries","toiletry","shampoo","conditioner","soap","body wash","toothbrush","toothpaste","towels","bathrobe","slippers"), "hotel bathroom toiletries"),
            (("bathroom","shower","bathtub","walk-in shower","toilet","hairdryer","hair dryer"), "hotel bathroom shower"),
            (("king bed","queen bed","twin beds","extra bed","crib","cot","mattress","pillow","bedroom","bed"), "hotel bedroom bed"),
            (("spacious room","large room","small room","room size","square feet","square foot","suite","suites"), "hotel room interior suite"),
            (("balcony","terrace","private terrace","patio","veranda"), "hotel balcony terrace"),
            (("ocean view","sea view","water view","mountain view","garden view","city view","scenic view","panoramic view"), "hotel scenic room view"),
            (("sunset","sunrise"), "hotel scenic sunset view"),
            (("swimming pool","infinity pool","outdoor pool","indoor pool","poolside","pool area","pool"), "hotel swimming pool"),
            (("hot tub","jacuzzi","whirlpool"), "hotel jacuzzi hot tub"),
            (("gym","fitness center","fitness centre","fitness room","workout","exercise"), "hotel gym fitness"),
            (("tennis","tennis court"), "hotel tennis court"), (("golf","golf course","golf club"), "hotel golf course"),
            (("basketball","basketball court"), "hotel basketball court"), (("volleyball","beach volleyball"), "beach volleyball resort"),
            (("badminton",), "hotel badminton court"), (("table tennis","ping pong"), "hotel table tennis"),
            (("billiards","pool table","snooker"), "hotel billiards"),
            (("water sports","watersports"), "tropical resort water sports"), (("snorkeling","snorkelling"), "tropical snorkeling"),
            (("scuba diving","diving","scuba dive","dive center","dive centre"), "tropical scuba diving"),
            (("kayaking","kayak"), "tropical kayaking"), (("paddleboard","paddle boarding","stand up paddle"), "tropical paddle boarding"),
            (("surfing","surf"), "tropical surfing"), (("canoeing","canoe"), "tropical canoeing"),
            (("sailing","sailboat"), "tropical sailing"), (("boat tour","island hopping","island tour"), "tropical island boat tour"),
            (("hiking","hike","trekking","trek"), "tropical hiking"), (("cycling","bicycle","bike","biking"), "tropical cycling"),
            (("walking tour","nature walk","walking trail"), "travel walking tour"),
            (("spa","massage","wellness","sauna","steam room","steam bath"), "hotel spa wellness"),
            (("yoga","yoga class","meditation"), "resort yoga meditation"),
            (("breakfast","breakfast buffet","morning meal"), "hotel breakfast buffet"),
            (("room service","in-room dining","in room dining"), "hotel room service"),
            (("restaurant","dining","dinner","lunch","buffet","meal","food"), "hotel restaurant dining"),
            (("bar","cocktail","drinks","beverages","lounge"), "hotel bar lounge"),
            (("staff","friendly staff","helpful staff","hospitality","welcoming","receptionist","concierge"), "hotel staff hospitality"),
            (("housekeeping","cleaning","cleaned","room cleaning","cleanliness","spotless"), "hotel housekeeping cleaning"),
            (("laundry","laundry service","washing machine","dry cleaning"), "hotel laundry service"),
            (("business center","business centre","meeting room","conference room","conference","meeting","workspace","colleagues"), "hotel business conference"),
            (("kids club","kids activities","playground","play area","children","kids"), "family hotel kids activities"),
            (("family friendly","family-friendly","family vacation","families"), "family friendly hotel"),
            (("wheelchair","accessible room","accessibility","wheelchair accessible","accessible bathroom"), "accessible hotel room"),
            (("elevator","lift"), "hotel elevator"), (("security guard","24-hour security","security"), "hotel security"),
            (("smoking area","smoking"), "hotel smoking policy"),
            (("credit card","debit card","card payment","card payments","pay by card"), "credit card hotel payment"),
            (("security deposit","refundable deposit","deposit required","cash payment"), "hotel payment deposit"),
            (("check-in","check in","check-out","check out"), "hotel check in reception"),
            (("reservation","reservations","booking","booked","availability"), "hotel booking reservation"),
            (("car rental","rental car","rent a car","hire a car"), "car rental travel"),
            (("shuttle","hotel shuttle","airport transfer","airport shuttle","airport transportation","transfer service"), "hotel airport shuttle"),
            (("taxi","taxis","bus","buses","public transport","transportation","transport"), "travel transportation taxi"),
            (("airport","near the airport"), "airport travel"),
            (("parking","car park","parking lot","parking garage","free parking"), "hotel parking"),
            (("entrance","hotel entrance","front entrance","driveway","arrival area","front door"), "hotel entrance arrival"),
            (("garden","gardens","tropical garden","landscaped grounds"), "hotel tropical garden"),
            (("courtyard","outdoor area","outdoor space","grounds"), "hotel outdoor courtyard"),
        ]
        for words, base in rules:
            if has(*words): return q(base)

        # Culture/attractions before generic hotel fallbacks.
        if has("museum","museums","archaeological museum","archaeological site"): return q("archaeological museum travel")
        if has("temple","temples"): return q("Hindu temple landmark travel")
        if has("church","churches"): return q("historic church landmark travel")
        if has("mosque","mosques"): return q("mosque landmark travel")
        if has("stadium","sports stadium"): return q("city sports stadium")
        if has("landmark","landmarks","monument","historic site","historical site"): return q("city landmark travel")

        if has("centrally located","central location","city center","city centre","downtown","town center","town centre"): return q("city center hotel location")
        if has("attraction","attractions","nearby attractions","explore","exploring","sightseeing","things to do","day trip","tour","tours"): return q("travel destination attractions")
        if has("walking distance","short walk","short drive","drive away","minutes away","nearby","close to","located near"): return q("hotel location nearby attractions")
        if has("island","islands","beach","ocean","sea","coast","shore","lagoon"): return q("tropical island beach travel")
        if has("nature","jungle","forest","waterfall","river","wildlife"): return q("tropical nature travel")

        # Review/value statements get meaningful travel visuals, never luxury resort filler.
        if has("rating","ratings","rated","review","reviews","score","scores","guest rating","guests","satisfied","praised","appreciated","positive notes","high rating"): return q("hotel review travel")
        if has("price","prices","cost","value","budget","expensive","affordable","cheap","rate","rates","per night","worth considering","without breaking the bank"): return q("hotel booking price travel")
        if has("comfortable","comfort","well-maintained","well maintained","spotless","nice stay","solid experience","reliable option"): return q("comfortable hotel room")
        if has("problem","problems","issue","issues","improve","improvement","downside","minor issues","limited"): return q("hotel room problem review")

        scene_queries = {
            "room":"hotel room interior","bathroom":"hotel bathroom","pool":"hotel swimming pool","beach":"tropical beach resort",
            "restaurant":"hotel restaurant dining","bar":"hotel bar lounge","spa":"hotel spa wellness","gym":"hotel gym fitness",
            "lobby":"hotel lobby reception","balcony":"hotel balcony view","kids":"family hotel kids activities","outside":"hotel exterior property",
        }
        if scene in scene_queries: return q(scene_queries[scene])
        if has("hotel","resort","property","accommodation","stay","vacation"): return q("hotel exterior property")
        return q("travel destination")