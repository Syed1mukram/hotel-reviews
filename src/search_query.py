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
                "bed",
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
                "wifi",
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
                "television",
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
                    "shuttle",
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
                "restaurant dining",
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
            ], "breakfast"),
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
            ("bathroom", [r"\bbathroom\b", r"\bshower\b", r"\bbathtub\b",
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

    # ---------------------------------------------------------
    # NAMED LANDMARK / PROPER NOUN FALLBACK
    # Catches sentences that just state a place name directly
    # ("Balboa Park sits about...") with no trigger keyword like
    # "attraction" or "landmark" nearby.
    # ---------------------------------------------------------

    # Chain/brand names aren't landmarks — searching their own name risks
    # pulling in branded logos or trademarked stock footage. Route these
    # to the generic restaurant/dining query instead.
    BRAND_NAMES = {
        "mcdonald's", "mcdonalds", "starbucks", "taco bell", "wendy's",
        "wendys", "burger king", "subway", "kfc", "dunkin", "dunkin'",
        "chipotle", "domino's", "dominos", "pizza hut", "chick-fil-a",
        "chick fil a", "7-eleven", "7 eleven", "walgreens", "cvs",
    }

    def extract_proper_nouns(self, original_text):
        text = str(original_text).strip()

        # Two or more consecutive capitalized words, e.g.
        # "Balboa Park", "Old Town Transit Center",
        # "Queen Bee's Art and Cultural Center".
        matches = re.findall(
            r"\b[A-Z][a-zA-Z']*(?:\s+(?:of|the|and)\s+[A-Z][a-zA-Z']*"
            r"|\s+[A-Z][a-zA-Z']*)+\b",
            text,
        )

        # Drop brand/chain names before picking the best match.
        matches = [
            m for m in matches
            if m.strip().lower() not in self.BRAND_NAMES
        ]

        if not matches:
            return ""

        # Prefer the longest match (most specific named entity).
        best = max(matches, key=len).strip()

        if best.lower() in self.BRAND_NAMES:
            return ""

        generic_leads = {
            "this is", "there is", "there's", "one guest", "one traveler",
            "another traveler", "another minor", "no property",
        }
        if best.lower() in generic_leads:
            return ""

        return f"{best} travel landmark"

    def generate(self, text, scene="general"):
        """
        Return one clean, natural-language visual query for Pexels.

        Rules:
        - Prefer the most specific concrete visual mentioned.
        - Do not add "hotel" to generic objects/activities.
        - Use location only for named places / destination-specific searches.
        - Never return raw prose, pipe separators, or duplicated location text.
        """
        original = str(text).strip()
        t = re.sub(r"\s+", " ", original.lower())
        t = t.replace("wi-fi", "wifi").replace("wi fi", "wifi")
        t = t.replace("mini-fridge", "mini fridge")
        t = t.replace("air-conditioned", "air conditioned")
        t = t.replace("smag", "smeg")

        # More specific concepts are listed first.
        rules = [
            (("family suite",), "family suite"),
            (("bunk beds", "bunk bed"), "bunk beds"),
            (("electric kettle", "smeg"), "electric kettle"),
            (("coffee maker", "coffee machine", "tea maker"), "coffee maker"),
            (("mini fridge", "minibar", "mini bar", "refrigerator", "fridge"), "mini fridge"),
            (("bathroom", "shower", "bathtub", "walk-in shower", "toilet"), "bathroom"),
            (("toiletries", "shampoo", "conditioner", "soap", "body wash", "toothbrush", "toothpaste", "towels"), "bathroom toiletries"),
            (("wifi", "wireless internet", "internet access", "free internet", "high-speed internet"), "wifi"),
            (("air conditioning", "air conditioner", "air conditioned", "climate control"), "air conditioning"),
            (("king bed", "queen bed", "twin beds", "twin bed", "bedroom", "bed", "beds", "mattress", "pillow"), "bed"),
            (("television", "tv", "smart tv", "flat-screen tv", "flat screen tv"), "television"),
            (("balcony", "terrace", "private terrace", "patio", "veranda"), "balcony"),
            (("ocean view", "sea view", "water view", "mountain view", "garden view", "city view", "scenic view", "panoramic view"), "scenic view"),
            (("swimming pool", "infinity pool", "outdoor pool", "indoor pool", "poolside", "pool area", "pool"), "swimming pool"),
            (("hot tub", "jacuzzi", "whirlpool"), "jacuzzi"),
            (("spa", "massage", "wellness", "sauna", "steam room", "treatment"), "spa"),
            (("gym", "fitness center", "fitness centre", "fitness room", "workout", "exercise"), "gym"),
            (("game room", "games room"), "game room"),
            (("meeting room", "business center", "business centre", "conference room", "conference", "workspace"), "meeting room"),
            (("room service", "in-room dining", "in room dining"), "room service"),
            (("breakfast", "breakfast buffet", "morning meal"), "breakfast"),
            (("restaurant", "restaurants", "dining", "dinner", "lunch", "buffet", "meal", "food", "coffee shop", "cafe"), "restaurant dining"),
            (("bar", "cocktail", "drinks", "beverages", "lounge"), "bar lounge"),
            (("parking", "car park", "parking lot", "parking garage", "free parking"), "parking lot cars"),
            (("electric car charging", "ev charging", "charging station"), "ev charging station"),
            (("shuttle", "airport transfer", "airport shuttle", "airport transportation"), "shuttle"),
            (("airport",), "airport"),
            (("check-in", "check in", "front desk", "arrival"), "reception desk"),
            (("check-out", "check out", "departure"), "hotel checkout"),
            (("credit card", "debit card", "card payment", "payment card"), "card payment"),
            (("security deposit", "refundable deposit", "deposit required", "cash deposit"), "security deposit"),
            (("reservation", "reservations", "booking", "booked"), "hotel booking"),
            (("pet friendly", "pet-friendly", "pet policy", "pet fee", "dogs", "dog", "cats", "cat", "pets", "pet"), "pet friendly dog"),
            (("museum", "museums"), "museum"),
            (("temple", "temples"), "temple"),
            (("church", "churches"), "historic church"),
            (("mosque", "mosques"), "mosque"),
            (("stadium", "sports stadium"), "stadium"),
            (("landmark", "landmarks", "monument", "historic site", "historical site"), "city landmark"),
            (("beach", "beaches", "beachfront", "ocean", "sea", "coast", "shore", "lagoon"), "beach ocean"),
            (("snorkeling", "snorkelling"), "snorkeling"),
            (("scuba diving", "diving", "scuba dive"), "scuba diving"),
            (("kayaking", "kayak"), "kayaking"),
            (("paddleboard", "paddle boarding", "stand up paddle"), "paddle boarding"),
            (("surfing", "surf"), "surfing"),
            (("canoeing", "canoe"), "canoeing"),
            (("sailing", "sailboat"), "sailing"),
            (("boat tour", "boat trip", "island hopping", "island tour"), "island boat tour"),
            (("hiking", "hike", "trekking", "trek"), "hiking"),
            (("cycling", "bicycle", "bike", "biking"), "cycling"),
            (("golf", "golf course", "golf club"), "golf course"),
            (("tennis", "tennis court"), "tennis court"),
            (("water sports", "watersports"), "water sports"),
            (("five star", "four star"), "luxury hotel"),
            (("rated", "rating", "ratings", "score", "guest reviews", "reviews", "review"), "guest review"),
            (("price", "prices", "cost", "budget", "expensive", "affordable", "cheap", "per night", "taxes", "fees"), "price tag booking"),
        ]

        def has(term):
            return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", t) is not None

        for terms, query in rules:
            if any(has(term) for term in terms):
                return query

        # Proper-noun place extraction, only when no stronger visual exists.
        patterns = [
            r"\b([A-Z][a-zA-Z']+(?:\s+(?:of|the|and)\s+)?(?:\s+[A-Z][a-zA-Z']+)+)\b"
        ]
        for pattern in patterns:
            matches = re.findall(pattern, original)
            if matches:
                candidate = max(matches, key=len).strip()
                if candidate.lower() not in {
                    "there is", "this is", "the property", "one guest"
                }:
                    return f"{candidate} landmark"

        scene_l = str(scene).lower()
        defaults = [
            ("bathroom", "bathroom"),
            ("pool", "swimming pool"),
            ("spa", "spa"),
            ("gym", "gym"),
            ("restaurant", "restaurant dining"),
            ("room", "room interior"),
            ("lobby", "hotel lobby"),
            ("outside", "hotel exterior"),
            ("location", "city travel"),
            ("review", "five star hotel"),
        ]
        for key, query in defaults:
            if key in scene_l:
                return query

        return "hotel interior"
