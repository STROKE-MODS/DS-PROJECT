from __future__ import annotations

import argparse

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Internship, Skill
from app.recommendation.semantic import get_embedding_model


def generate(force: bool = False) -> None:
    model = get_embedding_model()
    with SessionLocal() as session:
        skills = session.scalars(select(Skill).order_by(Skill.id)).all()
        internships = session.scalars(select(Internship).order_by(Internship.id)).all()
        skills_skipped = sum(bool(skill.embedding) for skill in skills) if not force else 0
        internships_skipped = sum(bool(item.description_embedding) for item in internships) if not force else 0
        skills_to_embed = [skill for skill in skills if force or not skill.embedding]
        internships_to_embed = [item for item in internships if force or not item.description_embedding]

        skill_texts = [f"{skill.name}. Aliases: {', '.join(skill.aliases or [])}" for skill in skills_to_embed]
        if skill_texts:
            vectors = model.encode(skill_texts, convert_to_numpy=True, normalize_embeddings=False, show_progress_bar=True)
            for skill, vector in zip(skills_to_embed, vectors, strict=True):
                skill.embedding = vector.astype(float).tolist()

        internship_texts = [f"{item.title}. {item.description or ''}" for item in internships_to_embed]
        if internship_texts:
            vectors = model.encode(internship_texts, convert_to_numpy=True, normalize_embeddings=False, show_progress_bar=True)
            for item, vector in zip(internships_to_embed, vectors, strict=True):
                item.description_embedding = vector.astype(float).tolist()

        session.commit()
        print(f"Skills embedded: {len(skills_to_embed)}")
        print(f"Skills skipped (already embedded): {skills_skipped}")
        print(f"Internships embedded: {len(internships_to_embed)}")
        print(f"Internships skipped (already embedded): {internships_skipped}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate cached semantic embeddings for InternAI data.")
    parser.add_argument("--force", action="store_true", help="Regenerate all embeddings, including populated rows.")
    generate(parser.parse_args().force)
