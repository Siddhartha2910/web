from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Project, ProjectMember
from pydantic import BaseModel
from ..models import Project, ProjectMember, User
import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/projects", tags=["Projects"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- SCHEMAS FIRST ----------

class ProjectCreate(BaseModel):
    name: str
    description: str
    github_repo: str
    owner_id: int


class AddMember(BaseModel):
    project_id: int
    user_id: int


# ---------- ROUTES ----------

@router.post("/")
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    new_project = Project(
        name=project.name,
        description=project.description,
        github_repo=project.github_repo,
        owner_id=project.owner_id
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


@router.post("/add-member")
def add_member(data: AddMember, db: Session = Depends(get_db)):
    new_member = ProjectMember(
        project_id=data.project_id,
        user_id=data.user_id
    )

    db.add(new_member)
    db.commit()

    return {"message": "Member added successfully"}

@router.get("/")
def get_all_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return projects

@router.get("/{project_id}/members")
def get_project_members(project_id: int, db: Session = Depends(get_db)):
    members = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id
    ).all()

    return members

@router.get("/user/{user_id}")
def get_projects_by_user(user_id: int, db: Session = Depends(get_db)):
    memberships = db.query(ProjectMember).filter(
        ProjectMember.user_id == user_id
    ).all()

    project_ids = [m.project_id for m in memberships]

    projects = db.query(Project).filter(
        Project.id.in_(project_ids)
    ).all()

    return projects

@router.get("/{project_id}/github-health")
def project_github_health(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        return {"error": "Project not found"}

    parts = project.github_repo.rstrip("/").split("/")
    owner = parts[-2]
    repo = parts[-1]

    github_api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"

    token = os.getenv("GITHUB_TOKEN")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "CodeStylePolicemanApp"
    }

    response = requests.get(github_api_url, headers=headers)

    if response.status_code != 200:
        return {
            "status_code": response.status_code,
            "github_message": response.text
        }

    commits = response.json()

    members = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id
    ).all()

    user_ids = [m.user_id for m in members]

    users = db.query(User).filter(User.id.in_(user_ids)).all()

    team_names = [user.name for user in users]

    latest_commit_per_author = {}

    for commit in commits:
        if not commit.get("author"):
            continue

        author = commit["author"]["login"]
        date_str = commit["commit"]["author"]["date"]
        commit_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        if author not in latest_commit_per_author:
            latest_commit_per_author[author] = commit_date

    now = datetime.now(timezone.utc)

    health_status = []

    for author, commit_date in latest_commit_per_author.items():
        if author not in team_names:
            continue

        hours_diff = (now - commit_date).total_seconds() / 3600

        if hours_diff <= 24:
            status = "🟢 Active"
        elif hours_diff <= 48:
            status = "🟡 Moderate"
        else:
            status = "🔴 Inactive"

        health_status.append({
            "author": author,
            "last_commit": commit_date,
            "hours_since_last_commit": round(hours_diff, 2),
            "status": status
        })

    return health_status
