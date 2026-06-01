from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.orm import Candidate, Skill, CandidateSkill, Experience, Education
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def get_or_create_skill(session, name, category):
    skill = session.query(Skill).filter_by(name=name.lower()).first()
    if not skill:
        skill = Skill(name=name.lower(), category=category)
        session.add(skill)
        session.flush()
    return skill


def load_resume(parsed, extracted):
    """Insert a parsed/extracted resume into the DB. Skips duplicates by file hash."""
    session = Session()
    try:
        existing = session.query(Candidate).filter_by(file_hash=parsed["file_hash"]).first()
        if existing:
            print(f"Skipping {parsed['filename']}, already in DB.")
            return existing

        candidate = Candidate(
            name=extracted.get("name"),
            email=extracted.get("email"),
            phone=extracted.get("phone"),
            raw_text=parsed["raw_text"],
            file_hash=parsed["file_hash"],
        )
        session.add(candidate)
        session.flush()

        for s in extracted.get("skills", []):
            if not s.get("name"):
                continue
            skill = get_or_create_skill(session, s["name"], s.get("category", "unknown"))
            session.add(CandidateSkill(
                candidate_id=candidate.id,
                skill_id=skill.id,
                confidence=s.get("confidence", 1.0),
            ))

        for exp in extracted.get("experiences", []):
            session.add(Experience(
                candidate_id=candidate.id,
                title=exp.get("title"),
                company=exp.get("company"),
                start_date=exp.get("start_date"),
                end_date=exp.get("end_date"),
                years_calculated=exp.get("years_calculated"),
                description=exp.get("description"),
            ))

        for edu in extracted.get("education", []):
            session.add(Education(
                candidate_id=candidate.id,
                degree=edu.get("degree"),
                field=edu.get("field"),
                institution=edu.get("institution"),
                graduation_year=edu.get("graduation_year"),
            ))

        session.commit()
        print(f"Loaded {extracted.get('name')} from {parsed['filename']}")
        return candidate

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()