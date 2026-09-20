from datetime import date

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import (
    CareerPath,
    Certificate,
    Internship,
    InternshipSkill,
    ProficiencyLevel,
    RequirementLevel,
    Skill,
    SkillSource,
    Student,
    StudentSkill,
    WorkMode,
)


CAREER_PATHS = [
    ("Data Analyst", "Turn business data into actionable insights."),
    ("Data Scientist", "Build predictive models and analytical solutions."),
    ("ML Engineer", "Productionize machine-learning systems at scale."),
]

SKILLS = [
    ("Python", "Programming", ["Py"]),
    ("SQL", "Programming", ["Structured Query Language"]),
    ("R", "Programming", ["R Language"]),
    ("JavaScript", "Programming", ["JS"]),
    ("Machine Learning", "Programming", ["ML", "Machine Intelligence"]),
    ("Statistics", "Analytical", ["Statistical Analysis"]),
    ("Data Visualization", "Analytical", ["Data Viz"]),
    ("Pandas", "Tool", ["Python Pandas"]),
    ("NumPy", "Tool", ["Numerical Python"]),
    ("Scikit-learn", "Tool", ["sklearn"]),
    ("TensorFlow", "Tool", ["TF"]),
    ("Git", "Tool", ["GitHub", "Version Control"]),
    ("Excel", "Tool", ["Microsoft Excel", "Spreadsheets"]),
    ("Tableau", "Tool", ["Tableau Desktop"]),
    ("Power BI", "Tool", ["Microsoft Power BI"]),
    ("Communication", "Soft Skill", ["Verbal Communication"]),
    ("Problem Solving", "Soft Skill", ["Analytical Thinking"]),
    ("Cloud Fundamentals", "Cloud", ["Cloud Computing"]),
]

STUDENTS = [
    {
        "name": "Aarav Mehta", "email": "aarav.mehta@example.com",
        "education_level": "Undergraduate", "degree": "B.Tech",
        "branch": "Computer Science", "year_of_study": 3, "location": "Bengaluru",
        "career": "Data Scientist",
        "interests": ["AI", "Data Science", "Machine Learning"],
        "preferences": {"location": "Bengaluru", "work_mode": "hybrid", "duration": "6 months"},
        "skills": [("Python", ProficiencyLevel.advanced), ("SQL", ProficiencyLevel.intermediate), ("Pandas", ProficiencyLevel.intermediate), ("Git", ProficiencyLevel.intermediate)],
    },
    {
        "name": "Maya Sharma", "email": "maya.sharma@example.com",
        "education_level": "Undergraduate", "degree": "B.Sc.",
        "branch": "Statistics", "year_of_study": 2, "location": "Pune",
        "career": "Data Analyst",
        "interests": ["Analytics", "Finance", "Visualization"],
        "preferences": {"location": "Pune", "work_mode": "onsite", "duration": "3 months"},
        "skills": [("Excel", ProficiencyLevel.advanced), ("Statistics", ProficiencyLevel.intermediate), ("Tableau", ProficiencyLevel.beginner), ("Communication", ProficiencyLevel.advanced)],
    },
    {
        "name": "Kabir Rao", "email": "kabir.rao@example.com",
        "education_level": "Undergraduate", "degree": "B.Tech",
        "branch": "Information Technology", "year_of_study": 4, "location": "Hyderabad",
        "career": "ML Engineer",
        "interests": ["AI", "Cloud", "Cybersecurity"],
        "preferences": {"location": "Remote", "work_mode": "remote", "duration": None},
        "skills": [("Python", ProficiencyLevel.advanced), ("Machine Learning", ProficiencyLevel.intermediate), ("TensorFlow", ProficiencyLevel.beginner), ("NumPy", ProficiencyLevel.advanced), ("Problem Solving", ProficiencyLevel.advanced)],
    },
]

INTERNSHIPS = [
    ("Data Analyst Intern", "InsightWorks", "Analyze product metrics and build dashboards.", "Analytics", "B.Tech/B.Sc.", 2, "Bengaluru", WorkMode.hybrid, "6 months", "₹25,000/month", "No prior experience", "Data Analyst", [("SQL", RequirementLevel.required), ("Excel", RequirementLevel.required), ("Tableau", RequirementLevel.preferred)]),
    ("Business Intelligence Intern", "MarketLens", "Support reporting and business intelligence projects.", "Analytics", "Any quantitative degree", 2, "Mumbai", WorkMode.onsite, "3 months", "₹20,000/month", "No prior experience", "Data Analyst", [("SQL", RequirementLevel.required), ("Power BI", RequirementLevel.required), ("Communication", RequirementLevel.preferred)]),
    ("Product Analytics Intern", "AppSpring", "Measure user behavior and communicate product insights.", "Technology", "B.Tech/BBA", 3, "Remote", WorkMode.remote, "6 months", "₹30,000/month", "Coursework in analytics", "Data Analyst", [("SQL", RequirementLevel.required), ("Statistics", RequirementLevel.required), ("Data Visualization", RequirementLevel.preferred)]),
    ("Junior Data Scientist Intern", "ForecastIQ", "Develop experiments and predictive models with the research team.", "AI", "B.Tech/M.Sc.", 3, "Delhi", WorkMode.hybrid, "6 months", "₹35,000/month", "Projects preferred", "Data Scientist", [("Python", RequirementLevel.required), ("Machine Learning", RequirementLevel.required), ("Scikit-learn", RequirementLevel.required)]),
    ("Applied ML Intern", "Visionary Labs", "Prototype computer vision and NLP models.", "AI", "B.Tech/M.Tech", 3, "Remote", WorkMode.remote, "4 months", "₹40,000/month", "ML coursework", "Data Scientist", [("Python", RequirementLevel.required), ("TensorFlow", RequirementLevel.preferred), ("Machine Learning", RequirementLevel.required)]),
    ("Research Data Intern", "CivicData", "Clean public datasets and support statistical research.", "Research", "B.Sc./B.A.", 2, "Chennai", WorkMode.onsite, "3 months", "₹18,000/month", "No prior experience", "Data Scientist", [("R", RequirementLevel.required), ("Statistics", RequirementLevel.required), ("Data Visualization", RequirementLevel.preferred)]),
    ("ML Engineering Intern", "ScaleStack", "Help deploy and monitor machine-learning services.", "Cloud", "B.Tech", 3, "Hyderabad", WorkMode.hybrid, "6 months", "₹45,000/month", "Software projects preferred", "ML Engineer", [("Python", RequirementLevel.required), ("Machine Learning", RequirementLevel.required), ("Cloud Fundamentals", RequirementLevel.preferred), ("Git", RequirementLevel.required)]),
    ("MLOps Intern", "ModelForge", "Build reproducible training and deployment workflows.", "AI", "B.Tech", 3, "Pune", WorkMode.remote, "6 months", "₹42,000/month", "Programming experience", "ML Engineer", [("Python", RequirementLevel.required), ("Git", RequirementLevel.required), ("Cloud Fundamentals", RequirementLevel.required)]),
    ("Data Platform Intern", "QueryWorks", "Improve data pipelines and warehouse reliability.", "Cloud", "B.Tech", 3, "Bengaluru", WorkMode.hybrid, "5 months", "₹38,000/month", "SQL projects preferred", "ML Engineer", [("SQL", RequirementLevel.required), ("Python", RequirementLevel.preferred), ("Cloud Fundamentals", RequirementLevel.required)]),
    ("AI Solutions Intern", "BrightCompute", "Collaborate on practical AI solutions for enterprise clients.", "Consulting", "Any engineering degree", 2, "Remote", WorkMode.remote, "4 months", "₹28,000/month", "Coursework or projects", "Data Scientist", [("Python", RequirementLevel.required), ("Communication", RequirementLevel.required), ("Problem Solving", RequirementLevel.required)]),
]


def get_or_create(session, model, lookup: dict, values: dict | None = None):
    instance = session.scalar(select(model).filter_by(**lookup))
    if instance is None:
        instance = model(**lookup, **(values or {}))
        session.add(instance)
        session.flush()
    return instance


def seed() -> None:
    with SessionLocal() as session:
        paths = {name: get_or_create(session, CareerPath, {"name": name}, {"description": description}) for name, description in CAREER_PATHS}
        paths["Data Analyst"].next_step = paths["Data Scientist"]
        paths["Data Scientist"].next_step = paths["ML Engineer"]

        skills = {name: get_or_create(session, Skill, {"name": name}, {"category": category, "aliases": aliases}) for name, category, aliases in SKILLS}

        for student_data in STUDENTS:
            student = get_or_create(
                session, Student, {"email": student_data["email"]},
                {**{key: student_data[key] for key in ("name", "education_level", "degree", "branch", "year_of_study", "location", "interests", "preferences")}, "career_goal": paths[student_data["career"]]},
            )
            student.interests = student_data["interests"]
            student.preferences = student_data["preferences"]
            for skill_name, proficiency in student_data["skills"]:
                if session.scalar(select(StudentSkill).filter_by(student_id=student.id, skill_id=skills[skill_name].id)) is None:
                    session.add(StudentSkill(student=student, skill=skills[skill_name], proficiency=proficiency, source=SkillSource.manual))
            if student.email == "aarav.mehta@example.com" and not student.certificates:
                session.add(Certificate(student=student, name="Google Data Analytics Certificate", issuing_organization="Google", issue_date=date(2024, 8, 15), credential_url="https://example.com/credentials/aarav-data", extracted_from_resume=False))

        for title, company, description, sector, education, min_year, location, work_mode, duration, stipend, experience, career, required_skills in INTERNSHIPS:
            internship = get_or_create(session, Internship, {"title": title, "company": company}, {"description": description, "sector": sector, "education_required": education, "min_year": min_year, "location": location, "work_mode": work_mode, "duration": duration, "stipend": stipend, "experience_required": experience, "career_path": paths[career], "is_demo_data": True})
            for skill_name, requirement_level in required_skills:
                if session.scalar(select(InternshipSkill).filter_by(internship_id=internship.id, skill_id=skills[skill_name].id)) is None:
                    session.add(InternshipSkill(internship=internship, skill=skills[skill_name], requirement_level=requirement_level))

        session.commit()
        print(f"Seed complete: {len(CAREER_PATHS)} career paths, {len(SKILLS)} skills, {len(STUDENTS)} students, 1 certificate, {len(INTERNSHIPS)} internships.")


if __name__ == "__main__":
    seed()
