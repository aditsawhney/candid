from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.orm import Job, JobRequirement, Skill
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def create_job(title: str, description: str, required_skills: list, nice_to_have: list = []):
    session = Session()
    try:
        job = Job(title=title, description=description)
        session.add(job)
        session.flush()

        def add_skills(skill_list, required):
            for skill_name, weight in skill_list:
                skill = session.query(Skill).filter_by(name=skill_name.lower()).first()
                if not skill:
                    skill = Skill(name=skill_name.lower(), category="unknown")
                    session.add(skill)
                    session.flush()
                session.add(JobRequirement(job_id=job.id, skill_id=skill.id, weight=weight, required=required))

        add_skills(required_skills, required=True)
        add_skills(nice_to_have, required=False)

        session.commit()
        print(f"Created job '{title}' with ID {job.id}")
        return job.id

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    create_job(
        title="ML Engineer",
        description="Looking for an ML engineer with Python and NLP experience.",
        required_skills=[
            ("python", 3),
            ("ml", 3),
            ("nlp", 2),
            ("flask", 2),
        ],
        nice_to_have=[
            ("docker", 1),
            ("aws", 1),
        ]
    )