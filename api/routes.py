import shutil
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from groq import Groq

from models.orm import Job, JobRequirement, Skill, Candidate, Experience, Education
from ingestion.parser import parse_resume
from ingestion.extractor import extract_resume
from ingestion.loader import load_resume
from ingestion.jd_extractor import extract_jd
from matching.ranker import rank_candidates
from config import DATABASE_URL, GROQ_API_KEY

app = FastAPI()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


@app.post("/candidates")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDFs accepted")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        parsed = parse_resume(tmp_path)
        extracted = extract_resume(parsed["raw_text"])
        load_resume(parsed, extracted)
        return {"status": "ok", "name": extracted.get("name"), "skills_found": len(extracted.get("skills", []))}
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@app.get("/candidates")
async def list_candidates():
    session = Session()
    try:
        candidates = session.query(Candidate).order_by(Candidate.created_at.desc()).all()
        return [{"id": c.id, "name": c.name, "email": c.email} for c in candidates]
    finally:
        session.close()


@app.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: int):
    session = Session()
    try:
        candidate = session.query(Candidate).filter_by(id=candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Not found")

        experiences = session.query(Experience).filter_by(candidate_id=candidate_id).all()
        education = session.query(Education).filter_by(candidate_id=candidate_id).all()

        return {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "experiences": [
                {
                    "title": e.title,
                    "company": e.company,
                    "start_date": e.start_date,
                    "end_date": e.end_date,
                    "years_calculated": e.years_calculated,
                    "description": e.description,
                }
                for e in experiences
            ],
            "education": [
                {
                    "degree": e.degree,
                    "field": e.field,
                    "institution": e.institution,
                    "graduation_year": e.graduation_year,
                }
                for e in education
            ],
        }
    finally:
        session.close()


@app.post("/candidates/{candidate_id}/summary")
async def candidate_summary(candidate_id: int, payload: dict):
    session = Session()
    try:
        candidate = session.query(Candidate).filter_by(id=candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Not found")

        job_id = payload.get("job_id")
        results = rank_candidates(job_id) if job_id else []
        match = next((r for r in results if r["id"] == candidate_id), None)

        prompt = (
            f"Write 2 sentences about this candidate for a recruiter. "
            f"Skills they have: {match['matched_skills'] if match else []}. "
            f"Skills they're missing: {match['missing_skills'] if match else []}. "
            f"Match: {match['match_percentage'] if match else 0}%. "
            f"Be direct, no filler phrases, no 'this candidate' opener."
        )

        client = Groq(api_key=GROQ_API_KEY)
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return {"summary": res.choices[0].message.content.strip()}
    finally:
        session.close()


@app.post("/jobs/parse")
async def parse_jd(payload: dict):
    jd_text = payload.get("text", "").strip()
    if not jd_text:
        raise HTTPException(status_code=400, detail="No text provided")
    return extract_jd(jd_text)


@app.post("/jobs")
async def create_job(payload: dict):
    session = Session()
    try:
        job = Job(title=payload["title"], description=payload.get("description", ""))
        session.add(job)
        session.flush()

        for required, items in [(True, payload.get("required_skills", [])), (False, payload.get("nice_to_have", []))]:
            for item in items:
                skill = session.query(Skill).filter_by(name=item["skill"].lower()).first()
                if not skill:
                    skill = Skill(name=item["skill"].lower(), category="unknown")
                    session.add(skill)
                    session.flush()
                session.add(JobRequirement(
                    job_id=job.id,
                    skill_id=skill.id,
                    weight=item.get("weight", 1),
                    required=required,
                ))

        session.commit()
        return {"status": "ok", "job_id": job.id, "title": job.title}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.get("/jobs")
async def list_jobs():
    session = Session()
    try:
        jobs = session.query(Job).order_by(Job.created_at.desc()).all()
        return [{"id": j.id, "title": j.title, "created_at": str(j.created_at)} for j in jobs]
    finally:
        session.close()


@app.get("/jobs/{job_id}/matches")
async def get_matches(job_id: int):
    try:
        return {"job_id": job_id, "candidates": rank_candidates(job_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")