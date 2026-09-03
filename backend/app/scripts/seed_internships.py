from __future__ import annotations

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models import CareerPath, Internship, InternshipSkill, Skill, WorkMode
from app.models.enums import RequirementLevel

TARGET_COUNTS = {
    "Software Development": 39,
    "Data Analytics": 39,
    "Data Science": 39,
    "AI/ML": 39,
    "Cybersecurity": 39,
    "Cloud": 39,
    "Web Development": 38,
    "App Development": 38,
    "Finance": 38,
    "Marketing": 38,
    "Healthcare": 38,
    "Agriculture": 38,
    "Manufacturing": 38,
}

# These are deliberately fictional names. Each sector gets a distinct pool so
# title/company pairs remain unique across repeated runs.
COMPANIES = {
    sector: [f"{prefix}{suffix}" for prefix, suffix in zip(
        prefixes,
        (" Labs", " Systems", " Works", " Digital", " Technologies", " Collective", " Innovations", " Networks"),
    )]
    for sector, prefixes in {
        "Software Development": ["Nexora", "CodeHarbor", "BrightForge", "StackMosaic", "DevCrest", "LogicSpring", "ByteTrail", "SoftPeak"],
        "Data Analytics": ["MetricNest", "InsightArc", "QuantHaven", "DataLoom", "SignalRoot", "DashCraft", "Vizora", "TrendMint"],
        "Data Science": ["PredictiveBay", "Statwise", "ModelCove", "PatternPilot", "DataVerge", "CausalGrid", "ForecastLane", "Analytica"],
        "AI/ML": ["NeuralCrest", "Cognivault", "LearnSphere", "VisionMesh", "AxiomMind", "ModelSpring", "Intellecta", "DeepHarbor"],
        "Cybersecurity": ["ShieldArc", "CipherNest", "SecureVista", "TrustLayer", "FortiMesh", "ThreatHarbor", "KeyStoneX", "SentinelWorks"],
        "Cloud": ["CloudWeave", "SkyGrid", "NimbusTrail", "InfraCove", "ScaleSpring", "CloudHarbor", "OrbitStack", "AeroCompute"],
        "Web Development": ["WebCanvas", "PagePilot", "SiteMosaic", "BrowserBay", "FrontlineWeb", "PixelHarbor", "WebNest", "RenderRoot"],
        "App Development": ["AppOrbit", "MobileCove", "TapTrail", "PocketForge", "AppSpring", "NativeNest", "ScreenPilot", "MobileMint"],
        "Finance": ["LedgerLeaf", "FinCrest", "CapitalArc", "MoneyMesh", "VaultSpring", "FiscalNest", "TradeHarbor", "BalanceWorks"],
        "Marketing": ["BrandLoom", "MarketCove", "GrowthArc", "ReachSpring", "CampaignNest", "StoryGrid", "AudienceWorks", "SignalBrand"],
        "Healthcare": ["MediLattice", "CareCrest", "HealthHarbor", "WellnessGrid", "ClinicSpring", "BioSignal", "CarePilot", "VitalNest"],
        "Agriculture": ["AgriWeave", "FieldCrest", "CropHarbor", "FarmSignal", "GreenSpring", "HarvestGrid", "SoilWorks", "TerraNest"],
        "Manufacturing": ["FactoryArc", "ForgeCrest", "PlantHarbor", "MakersGrid", "ProcessSpring", "AssemblyWorks", "IndustryNest", "BuildSignal"],
    }.items()
}

SECTOR_PROFILES = {
    "Software Development": {
        "titles": ["Backend Engineering", "Software QA", "Platform Engineering", "Developer Tools", "Systems Programming"],
        "description": "Build, test, and improve reliable software services with an engineering team.",
        "education": "B.Tech/B.E. in Computer Science or related field", "skills": ["Python", "Git", "Problem Solving", "SQL", "JavaScript"],
    },
    "Data Analytics": {
        "titles": ["Business Analytics", "Product Analytics", "Operations Analytics", "Reporting Analytics", "Customer Insights"],
        "description": "Turn operational data into clear dashboards, metrics, and recommendations for decision makers.",
        "education": "B.Tech/B.Sc. in a quantitative discipline", "skills": ["SQL", "Excel", "Data Visualization", "Statistics", "Power BI"],
    },
    "Data Science": {
        "titles": ["Applied Data Science", "Research Data Science", "Predictive Analytics", "Experimentation Science", "Data Modeling"],
        "description": "Explore datasets, design experiments, and develop statistical models for practical business questions.",
        "education": "B.Tech/B.Sc./M.Sc. in a quantitative discipline", "skills": ["Python", "Statistics", "Pandas", "Machine Learning", "Scikit-learn"],
    },
    "AI/ML": {
        "titles": ["Machine Learning Research", "Computer Vision", "NLP Engineering", "Applied AI", "Model Evaluation"],
        "description": "Prototype and evaluate machine-learning systems for real-world products and decision support.",
        "education": "B.Tech/M.Tech/M.Sc. in Computer Science or AI", "skills": ["Python", "Machine Learning", "TensorFlow", "NumPy", "Problem Solving"],
    },
    "Cybersecurity": {
        "titles": ["Security Operations", "Application Security", "Threat Research", "Cloud Security", "Security Testing"],
        "description": "Help identify risks, investigate security signals, and strengthen systems through practical controls.",
        "education": "B.Tech in Computer Science, IT, or Cybersecurity", "skills": ["Linux", "Cybersecurity", "Network Security", "Python", "Git"],
    },
    "Cloud": {
        "titles": ["Cloud Engineering", "Site Reliability", "Cloud Automation", "Infrastructure Operations", "Platform Reliability"],
        "description": "Support scalable cloud infrastructure, deployment automation, and reliable service operations.",
        "education": "B.Tech in Computer Science, IT, or related field", "skills": ["Cloud Fundamentals", "Docker", "Linux", "Git", "Kubernetes"],
    },
    "Web Development": {
        "titles": ["Frontend Development", "Full Stack Web", "Web Accessibility", "UI Engineering", "Web Performance"],
        "description": "Create accessible, responsive web experiences and contribute to a modern product codebase.",
        "education": "B.Tech/BCA in Computer Science or related field", "skills": ["JavaScript", "HTML/CSS", "React", "Git", "Problem Solving"],
    },
    "App Development": {
        "titles": ["Android Development", "iOS Development", "Cross-Platform Apps", "Mobile UI Engineering", "App Testing"],
        "description": "Build and test mobile experiences while learning product, performance, and release workflows.",
        "education": "B.Tech/BCA in Computer Science or related field", "skills": ["JavaScript", "Mobile Development", "Git", "UI/UX", "Problem Solving"],
    },
    "Finance": {
        "titles": ["Financial Analysis", "Risk Analytics", "Investment Research", "Financial Operations", "FinTech Product"],
        "description": "Support financial analysis and reporting with careful research, structured models, and clear communication.",
        "education": "B.Com/BBA/Economics or quantitative degree", "skills": ["Excel", "Financial Modeling", "Statistics", "SQL", "Communication"],
    },
    "Marketing": {
        "titles": ["Digital Marketing", "Content Marketing", "Growth Analytics", "Brand Strategy", "Market Research"],
        "description": "Help plan campaigns, understand audiences, and measure marketing performance across digital channels.",
        "education": "BBA/BA in Marketing, Communications, or related field", "skills": ["Marketing Analytics", "Content Strategy", "SEO", "Data Visualization", "Communication"],
    },
    "Healthcare": {
        "titles": ["Healthcare Analytics", "Clinical Data", "Health Product", "Public Health Research", "Medical Operations"],
        "description": "Use structured analysis and thoughtful research to improve healthcare operations and patient-focused products.",
        "education": "B.Tech/B.Sc./MPH in a relevant discipline", "skills": ["Healthcare Analytics", "Statistics", "SQL", "Data Visualization", "Communication"],
    },
    "Agriculture": {
        "titles": ["AgriTech Analytics", "Crop Data", "Precision Agriculture", "Farm Operations", "Agricultural Research"],
        "description": "Work with field, weather, and crop data to support more efficient and sustainable agricultural decisions.",
        "education": "B.Sc. Agriculture, Engineering, or related field", "skills": ["Agricultural Science", "GIS", "Python", "Data Visualization", "Statistics"],
    },
    "Manufacturing": {
        "titles": ["Manufacturing Analytics", "Industrial Engineering", "Quality Engineering", "Automation Engineering", "Supply Planning"],
        "description": "Improve production workflows through process analysis, quality measurement, and practical engineering support.",
        "education": "B.Tech in Mechanical, Industrial, Electrical, or related field", "skills": ["Lean Manufacturing", "Quality Control", "CAD", "Excel", "Problem Solving"],
    },
}

LOCATIONS = ["Bengaluru", "Mumbai", "Delhi", "Pune", "Hyderabad", "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Kochi", "Noida", "Gurugram", "Indore", "Coimbatore", "Remote"]
WORK_MODES = [WorkMode.hybrid, WorkMode.onsite, WorkMode.remote]
STIPENDS = ["₹18,000/month", "₹22,000/month", "₹28,000/month", "₹32,000/month", "₹38,000/month", "₹45,000/month"]

EXTRA_SKILLS = [
    ("Cybersecurity", "Security", ["Information Security"]), ("Linux", "Tool", ["GNU/Linux"]),
    ("Network Security", "Security", ["Network Defense"]), ("Docker", "Tool", ["Containerization"]),
    ("Kubernetes", "Tool", ["K8s"]), ("HTML/CSS", "Programming", ["HTML", "CSS"]),
    ("React", "Programming", ["React.js"]), ("Mobile Development", "Programming", ["App Development"]),
    ("UI/UX", "Design", ["User Experience"]), ("Financial Modeling", "Finance", ["Financial Model"]),
    ("Marketing Analytics", "Marketing", ["Marketing Data"]), ("Content Strategy", "Marketing", ["Content Planning"]),
    ("SEO", "Marketing", ["Search Engine Optimization"]), ("Healthcare Analytics", "Healthcare", ["Health Data"]),
    ("Agricultural Science", "Agriculture", ["Agronomy"]), ("GIS", "Tool", ["Geographic Information Systems"]),
    ("Lean Manufacturing", "Manufacturing", ["Lean Operations"]), ("Quality Control", "Manufacturing", ["Quality Assurance"]),
    ("CAD", "Manufacturing", ["Computer-Aided Design"]),
]


def get_or_create_skill(session, name: str, category: str, aliases: list[str]) -> Skill:
    skill = session.scalar(select(Skill).where(Skill.name == name))
    if skill is None:
        skill = Skill(name=name, category=category, aliases=aliases)
        session.add(skill)
        session.flush()
    return skill


def remap_legacy_sectors(session) -> None:
    legacy_to_target = {
        "Analytics": "Data Analytics", "AI": "AI/ML", "Research": "Data Science", "Consulting": "Marketing", "Technology": "Manufacturing",
    }
    for old_sector, new_sector in legacy_to_target.items():
        session.query(Internship).filter(Internship.sector == old_sector, Internship.is_demo_data.is_(True)).update({"sector": new_sector}, synchronize_session=False)


def add_skill_links(session, internship: Internship, skill_map: dict[str, Skill], required: list[str], preferred: list[str]) -> None:
    existing = {link.skill_id for link in internship.skills}
    for name in required:
        if skill_map[name].id not in existing:
            session.add(InternshipSkill(internship=internship, skill=skill_map[name], requirement_level=RequirementLevel.required))
    for name in preferred:
        if skill_map[name].id not in existing:
            session.add(InternshipSkill(internship=internship, skill=skill_map[name], requirement_level=RequirementLevel.preferred))


def seed_internships() -> None:
    with SessionLocal() as session:
        for name, category, aliases in EXTRA_SKILLS:
            get_or_create_skill(session, name, category, aliases)
        session.flush()
        skill_map = {skill.name: skill for skill in session.scalars(select(Skill)).all()}
        career_paths = {path.name: path.id for path in session.scalars(select(CareerPath)).all()}
        sector_career_paths = {
            "Software Development": career_paths["ML Engineer"], "Data Analytics": career_paths["Data Analyst"],
            "Data Science": career_paths["Data Scientist"], "AI/ML": career_paths["ML Engineer"],
            "Cybersecurity": career_paths["ML Engineer"], "Cloud": career_paths["ML Engineer"],
            "Web Development": career_paths["Data Analyst"], "App Development": career_paths["Data Analyst"],
            "Finance": career_paths["Data Analyst"], "Marketing": career_paths["Data Analyst"],
            "Healthcare": career_paths["Data Scientist"], "Agriculture": career_paths["Data Scientist"],
            "Manufacturing": career_paths["ML Engineer"],
        }
        remap_legacy_sectors(session)
        session.flush()

        existing_count = session.scalar(select(func.count()).select_from(Internship).where(Internship.is_demo_data.is_(True))) or 0
        created = 0
        sequence = 0
        for sector, target_count in TARGET_COUNTS.items():
            current = session.scalar(select(func.count()).select_from(Internship).where(Internship.is_demo_data.is_(True), Internship.sector == sector)) or 0
            profile = SECTOR_PROFILES[sector]
            while current < target_count and existing_count + created < 500:
                title_index = (current + sequence) % len(profile["titles"])
                company_index = (current + sequence) % len(COMPANIES[sector])
                title = f"{profile['titles'][title_index]} Intern"
                company = COMPANIES[sector][company_index]
                # The deterministic sequence makes this safe to rerun; skip any
                # pair already present rather than creating a literal duplicate.
                if session.scalar(select(Internship.id).where(Internship.title == title, Internship.company == company)):
                    sequence += 1
                    continue
                required = profile["skills"][:3]
                preferred = profile["skills"][3:5]
                internship = Internship(
                    title=title, company=company, description=profile["description"], sector=sector,
                    education_required=profile["education"], min_year=2 + ((sequence + current) % 3),
                    location=LOCATIONS[(sequence * 3 + current) % len(LOCATIONS)],
                    work_mode=WORK_MODES[(sequence + current) % len(WORK_MODES)],
                    duration=["3 months", "4 months", "6 months"][sequence % 3],
                    stipend=STIPENDS[(sequence + current) % len(STIPENDS)],
                    experience_required=["No prior experience", "Coursework preferred", "Relevant projects preferred"][sequence % 3],
                    career_path_id=sector_career_paths[sector],
                    is_demo_data=True,
                )
                session.add(internship)
                session.flush()
                add_skill_links(session, internship, skill_map, required, preferred)
                current += 1
                created += 1
                sequence += 1
        session.commit()
        final_count = session.scalar(select(func.count()).select_from(Internship).where(Internship.is_demo_data.is_(True)))
        print(f"Internship seed complete: created={created}, total_demo_internships={final_count}, sectors={len(TARGET_COUNTS)}.")


if __name__ == "__main__":
    seed_internships()
