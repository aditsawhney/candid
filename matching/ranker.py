from matching.scorer import score_candidates


def rank_candidates(job_id, min_match=25):
    results = score_candidates(job_id)
    ranked = []

    for r in results:
        required_total = r["required_total"] or 0
        required_matched = r["required_matched"] or 0
        skill_score = r["skill_score"] or 0
        match_pct = round(required_matched / required_total * 100, 1) if required_total > 0 else 0

        if match_pct < min_match:
            continue

        ranked.append({
            "rank": len(ranked) + 1,
            "id": r["id"],
            "name": r["name"],
            "email": r["email"],
            "skill_score": skill_score,
            "required_match": f"{required_matched}/{required_total}",
            "match_percentage": match_pct,
            "matched_skills": r["matched_skills"] or [],
            "missing_skills": r["missing_skills"] or [],
        })

    return ranked