SCORING_CONFIG = {
    "version": "1.0.0",
    "name": "BookOfH_ProfileScoringEngine",
    "score_range": {"min": 0, "max": 100},
    "bands": [
        {"name": "Beginner", "min": 0, "max": 39},
        {"name": "Engaged", "min": 40, "max": 69},
        {"name": "Insider", "min": 70, "max": 100},
    ],
    "categories": {
        "spend_12mo": {"label": "Total Spend (12 months)", "weight": 30},
        "sa_loyalty": {"label": "Sales Associate Loyalty", "weight": 20},
        "purchase_mix": {"label": "Purchase Mix", "weight": 20},
        "visit_engagement": {"label": "Visit & Engagement", "weight": 15},
        "behavior": {"label": "Behavior & Demeanor", "weight": 15},
    },
    "questions": {
        "q_spend_12mo": {
            "category": "spend_12mo",
            # Use stable codes for scoring (client should send codes when possible).
            # Points are canonical and based on USD thresholds.
            "points": {
                "no_shops": 0,
                "lt_5000": 5,
                "5000_15000": 10,
                "15000_40000": 20,
                "40000_plus": 30,
            },
            "max_points": 30
        },
        "q_sa_tenure": {
            "category": "sa_loyalty",
            "points": {
                "no_dedicated_sa": 0,
                "lt_6m": 5,
                "6_24m": 10,
                "gt_2y": 15,
            },
            "max_points": 15
        },
        "q_sa_switches": {
            "category": "sa_loyalty",
            "points": {
                "no_switches": 5,
                "1_2_switches": 0,
                "3_plus_switches": -5,
            },
            "max_points": 5
        },
        "q_purchase_mix": {
            "category": "purchase_mix",
            "points": {
                "no_purchases": 0,
                "home": 2,
                "outdoor_equestrian": 3,
                "fine_jewellery_watches": 5,
                "jewellery": 5,
                "makeup": 3,
                "fragrances": 2,
            },
            "max_points": 20
        },
        "q_visit_frequency": {
            "category": "visit_engagement",
            "points": {
                "have_not_visited": 0,
                "1_2_per_year": 0,
                "a_few_per_year": 5,
                "monthly": 10,
                "weekly_plus": 15,
            },
            "max_points": 15
        },
        "q_wishlist_active": {
            "category": "visit_engagement",
            "points": {
                "wishlist_yes": 5,
                "wishlist_no": 0,
            },
            "max_points": 5
        },
        "q_store_vibe": {
            "category": "behavior",
            "points": {
                "star_1": 2,
                "star_2": 4,
                "star_3": 6,
                "star_4": 8,
                "star_5": 10,
            },
            "max_points": 10
        },
        "q_cancellations": {
            "category": "behavior",
            "points": {
                "ask_cancellations_yes": 5,
                "ask_cancellations_no": 0,
            },
            "max_points": 5
        },
    }
}


def calculate_score(answers):
    # Initialize category totals
    category_scores = {cat: 0 for cat in SCORING_CONFIG["categories"]}
    
    # Pre-calculate category theoretical max from config
    category_max = {cat: 0 for cat in SCORING_CONFIG["categories"]}
    for q_config in SCORING_CONFIG["questions"].values():
        cat = q_config["category"]
        category_max[cat] += q_config["max_points"]
    
    for answer in answers:
        # Finding the question by ID or text
        q_config = None
        q_id_from_frontend = answer.get('question_id')
        
        for q_key, config in SCORING_CONFIG["questions"].items():
            if q_key == q_id_from_frontend or q_key == f"q_{q_id_from_frontend}":
                q_config = config
                break
        
        if not q_config:
            continue
            
        cat = q_config["category"]
        selected = answer.get("selected_options", [])
        if not selected:
            continue

        # Helper: map display text or incoming code to canonical code used in scoring
        def map_option_to_code(qconf, text):
            # If client already sent a canonical code, use it
            if text in qconf["points"]:
                return text

            # Legacy exact mappings (common display strings -> codes)
            LEGACY_TEXT_TO_CODE = {
                # spend labels
                "I haven't shopped at an Hermes boutique yet": "no_shops",
                "I haven't shopped at an Hermès boutique": "no_shops",
                "< $5,000": "lt_5000",
                "$5,000 – $15,000": "5000_15000",
                "$5,000 - $15,000": "5000_15000",
                "$15,000 – $40,000": "15000_40000",
                "$15,000 - $40,000": "15000_40000",
                "$40,000+": "40000_plus",
                "1 USD to 5,000 USD": "lt_5000",
                "1 USD to 5,000 USD": "lt_5000",

                # tenure
                "Less than 6 months": "lt_6m",
                "6 – 24 months": "6_24m",
                "More than 2 years": "gt_2y",

                # switches
                "No switches": "no_switches",
                "1 – 2 switches": "1_2_switches",
                "3+ switches": "3_plus_switches",

                # purchase mix
                "Mostly accessories/SLGs": "mostly_accessories",
                "Leather goods + accessories": "leather_and_accessories",
                "Leather goods + RTW/shoes": "leather_and_rtw_shoes",
                "Leather + RTW + jewelry/home": "leather_rtw_jewelry_home",

                # visit frequency
                "1–2 times per year": "1_2_per_year",
                "A few times per year": "a_few_per_year",
                "Monthly": "monthly",
                "Weekly or more": "weekly_plus",
                "Haven't visited the boutique yet": "have_not_visited",

                # yes/no fields (explicit contexts)
                "Yes": "YES_PLACEHOLDER",
                "No": "NO_PLACEHOLDER",

                # cancellations/tester
                "Do you ask about cancellations/walk-in availability when visiting?": "ask_cancellations_yes",
            }

            if text in LEGACY_TEXT_TO_CODE and LEGACY_TEXT_TO_CODE[text] not in ("YES_PLACEHOLDER", "NO_PLACEHOLDER"):
                return LEGACY_TEXT_TO_CODE[text]

            # Heuristic: detect "haven't" phrasing
            if "haven't" in text.lower() or "haven t" in text.lower():
                return "no_shops"

            # Map generic Yes/No to the *_yes/_no key present in qconf if possible
            lowered = text.strip().lower()
            if lowered == "yes":
                # prefer an explicit *_yes key if present
                for k in qconf["points"].keys():
                    if k.endswith("_yes"):
                        return k
                # fallback: try keys that start with 'wishlist' or 'tester' or 'ask_cancellations'
                for candidate in ("wishlist_yes", "tester_yes", "ask_cancellations_yes"):
                    if candidate in qconf["points"]:
                        return candidate
            if lowered == "no":
                for k in qconf["points"].keys():
                    if k.endswith("_no"):
                        return k
                for candidate in ("wishlist_no", "tester_no", "ask_cancellations_no"):
                    if candidate in qconf["points"]:
                        return candidate

            # Heuristic: try to parse USD numbers from the label and map to thresholds
            import re
            nums = re.findall(r"\$?\s*([0-9]{1,3}(?:,[0-9]{3})*)", text)
            parsed = [int(n.replace(',', '')) for n in nums] if nums else []
            if parsed:
                # If this label contains two numbers, use the upper bound
                bound = parsed[-1]
                if bound < 5000:
                    return "lt_5000"
                if 5000 <= bound < 15000:
                    return "5000_15000"
                if 15000 <= bound < 40000:
                    return "15000_40000"
                return "40000_plus"

            # If label contains a plus sign
            if "+" in text:
                return "40000_plus"

            # Fallback: try to match common words
            lowered = text.lower()
            if "<" in text or "less" in lowered:
                return "lt_5000"
            if "—" in text or "–" in text or " to " in lowered or "-" in text:
                # ambiguous range — as a fallback assign middle bucket
                return "5000_15000"

            # As last resort return the text unchanged (will map to 0 by default)
            return text

        # Process all selected options (for multi-select questions, sum all points)
        for opt in selected:
            code = map_option_to_code(q_config, opt)
            points = q_config["points"].get(code, 0)
            category_scores[cat] += points
    
    total_score = 0
    category_contributions = {}
    for cat, weight_info in SCORING_CONFIG["categories"].items():
        if category_max[cat] > 0:
            # Normalize to weight (e.g. 15 points out of 25 normalized to 15% weight = 9 pts)
            contrib = (category_scores[cat] / category_max[cat]) * weight_info["weight"]
            category_contributions[cat] = round(contrib, 2)
            total_score += contrib
        else:
            category_contributions[cat] = 0
            
    # Round and clamp
    total_score = max(0, min(100, round(total_score)))
    
    # Find band
    band_name = "Beginner"
    for band in SCORING_CONFIG["bands"]:
        if band["min"] <= total_score <= band["max"]:
            band_name = band["name"]
            break
            
    return total_score, band_name, category_contributions

