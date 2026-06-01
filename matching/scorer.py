from sqlalchemy import create_engine, text
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)


def score_candidates(job_id):
    """Score all candidates against a job's required skills."""
    query = text("""
        SELECT
            c.id,
            c.name,
            c.email,
            SUM(jr.weight) FILTER (WHERE cs.skill_id IS NOT NULL) AS skill_score,
            COUNT(cs.skill_id) FILTER (WHERE jr.required = true) AS required_matched,
            COUNT(jr.id) FILTER (WHERE jr.required = true) AS required_total,
            ARRAY_AGG(s.name) FILTER (WHERE cs.skill_id IS NOT NULL AND jr.required = true) AS matched_skills,
            ARRAY_AGG(s.name) FILTER (WHERE cs.skill_id IS NULL AND jr.required = true) AS missing_skills
        FROM candidates c
        CROSS JOIN job_requirements jr
        JOIN jobs j ON j.id = jr.job_id AND j.id = :job_id
        JOIN skills s ON s.id = jr.skill_id
        LEFT JOIN candidate_skills cs ON cs.candidate_id = c.id AND cs.skill_id = jr.skill_id
        GROUP BY c.id, c.name, c.email
        ORDER BY skill_score DESC NULLS LAST
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"job_id": job_id}).mappings().all()

    return [dict(row) for row in rows]