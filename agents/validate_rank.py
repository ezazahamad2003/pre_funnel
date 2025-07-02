def validate_and_rank(profiles, goal, company_info):
    # MOCK: Deduplicate (by name) and rank; in real use, use Gemini
    seen = set()
    unique = []
    for p in profiles:
        if p['name'] not in seen:
            seen.add(p['name'])
            p['score'] = 1.0  # placeholder score
            unique.append(p)
    # Sort by score (highest first)
    return sorted(unique, key=lambda x: x['score'], reverse=True) 