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
            "points": {
                "< $5,000": 0,
                "$5,000 – $15,000": 10,
                "$15,000 – $40,000": 20,
                "$40,000+": 30,
            },
            "max_points": 30
        },
        "q_sa_tenure": {
            "category": "sa_loyalty",
            "points": {
                "Less than 6 months": 0,
                "6 – 24 months": 10,
                "More than 2 years": 15,
            },
            "max_points": 15
        },
        "q_sa_switches": {
            "category": "sa_loyalty",
            "points": {
                "No switches": 5,
                "1 – 2 switches": 0,
                "3+ switches": -5,
            },
            "max_points": 5
        },
        "q_purchase_mix": {
            "category": "purchase_mix",
            "points": {
                "Mostly accessories/SLGs": 5,
                "Leather goods + accessories": 10,
                "Leather goods + RTW/shoes": 15,
                "Leather + RTW + jewelry/home": 20,
            },
            "max_points": 20
        },
        "q_visit_frequency": {
            "category": "visit_engagement",
            "points": {
                "1–2 times per year": 0,
                "A few times per year": 5,
                "Monthly": 10,
                "Weekly or more": 15,
            },
            "max_points": 15
        },
        "q_wishlist_active": {
            "category": "visit_engagement",
            "points": {
                "Yes": 5,
                "No": 0,
            },
            "max_points": 5
        },
        "q_tester_bag": {
            "category": "visit_engagement",
            "points": {
                "Yes": 5,
                "No": 0,
            },
            "max_points": 5
        },
        "q_store_vibe": {
            "category": "behavior",
            "points": {
                "Direct & transactional": 0,
                "Friendly & chatty": 5,
                "Patient & engaged": 10,
            },
            "max_points": 10
        },
        "q_cancellations": {
            "category": "behavior",
            "points": {
                "Yes": 5,
                "No": 0,
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
            
        # For single select, we take the first option
        opt = selected[0]
        points = q_config["points"].get(opt, 0)
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

