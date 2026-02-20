from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Project, ProjectMember
from pydantic import BaseModel

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
