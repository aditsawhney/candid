from sqlalchemy import Column, Integer, String, Float, Boolean, Text, Date, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    raw_text = Column(Text)
    file_hash = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    skills = relationship("CandidateSkill", back_populates="candidate")
    experiences = relationship("Experience", back_populates="candidate")
    education = relationship("Education", back_populates="candidate")


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    category = Column(String)


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))
    confidence = Column(Float)

    candidate = relationship("Candidate", back_populates="skills")
    skill = relationship("Skill")


class Experience(Base):
    __tablename__ = "experiences"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    title = Column(String)
    company = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    years_calculated = Column(Float)
    description = Column(Text)

    candidate = relationship("Candidate", back_populates="experiences")


class Education(Base):
    __tablename__ = "education"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    degree = Column(String)
    field = Column(String)
    institution = Column(String)
    graduation_year = Column(Integer)

    candidate = relationship("Candidate", back_populates="education")


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    requirements = relationship("JobRequirement", back_populates="job")


class JobRequirement(Base):
    __tablename__ = "job_requirements"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))
    weight = Column(Integer, default=1)
    required = Column(Boolean, default=True)

    job = relationship("Job", back_populates="requirements")
    skill = relationship("Skill")