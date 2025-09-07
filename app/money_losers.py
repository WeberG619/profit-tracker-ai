"""
Common money-losing job patterns for trades
"""

COMMON_MONEY_LOSERS = {
    # Plumbing
    "toilet": {
        "avg_loss": "$175",
        "reason": "Parts cost more than expected, takes longer than quoted",
        "fix": "Increase base rate by 40%"
    },
    "disposal": {
        "avg_loss": "$125", 
        "reason": "Hidden electrical work, disposal costs increased",
        "fix": "Always quote electrical separately"
    },
    "service call": {
        "avg_loss": "$200",
        "reason": "Drive time not factored, multiple trips needed",
        "fix": "Add minimum 2-hour charge"
    },
    "emergency": {
        "avg_loss": "$300",
        "reason": "After-hours costs not properly charged",
        "fix": "3x rate for nights/weekends"
    },
    
    # Electrical
    "outlet": {
        "avg_loss": "$95",
        "reason": "Old wiring requires extra work",
        "fix": "Add age-of-home multiplier"
    },
    "fixture": {
        "avg_loss": "$150",
        "reason": "Ceiling work takes 2x expected time",
        "fix": "Separate ceiling work pricing"
    },
    
    # General
    "repair": {
        "avg_loss": "$180",
        "reason": "Repairs unpredictable, often need multiple parts",
        "fix": "Switch to hourly + parts pricing"
    },
    "small job": {
        "avg_loss": "$225",
        "reason": "Setup/travel time same as big jobs",
        "fix": "$350 minimum for any job"
    }
}

def check_job_keywords(job_description):
    """Check if job contains money-losing keywords"""
    description_lower = job_description.lower()
    warnings = []
    
    for keyword, data in COMMON_MONEY_LOSERS.items():
        if keyword in description_lower:
            warnings.append({
                "keyword": keyword,
                "warning": f"⚠️ Jobs with '{keyword}' typically lose {data['avg_loss']}",
                "reason": data['reason'],
                "fix": data['fix']
            })
    
    return warnings