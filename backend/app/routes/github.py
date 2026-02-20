from fastapi import APIRouter
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
load_dotenv()

router = APIRouter(prefix="/github", tags=["GitHub"])

token = os.getenv("GITHUB_TOKEN")

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "User-Agent": "CodeStylePolicemanApp"
}

@router.get("/contributors")
def get_contributors(repo_url: str):
    try:
        parts = repo_url.rstrip("/").split("/")
        owner = parts[-2]
        repo = parts[-1]

        github_api_url = f"https://api.github.com/repos/{owner}/{repo}/contributors"

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

        data = response.json()

        contributors = [
            {
                "username": contributor["login"],
                "contributions": contributor["contributions"]
            }
            for contributor in data
        ]

        return contributors

    except Exception as e:
        return {"error": str(e)}

@router.get("/recent-activity")
def get_recent_activity(repo_url: str):
    try:
        parts = repo_url.rstrip("/").split("/")
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

        data = response.json()

        activity = []

        for commit in data[:30]:  # last 30 commits
            activity.append({
                "author": commit["commit"]["author"]["name"],
                "date": commit["commit"]["author"]["date"],
                "message": commit["commit"]["message"]
            })

        return activity

    except Exception as e:
        return {"error": str(e)}
@router.get("/health")
def get_contributor_health(repo_url: str):
    try:
        parts = repo_url.rstrip("/").split("/")
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

        latest_commit_per_author = {}

        # Get latest commit per author
        for commit in commits:
            author = commit["commit"]["author"]["name"]
            date_str = commit["commit"]["author"]["date"]
            commit_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

            if author not in latest_commit_per_author:
                latest_commit_per_author[author] = commit_date

        now = datetime.now(timezone.utc)

        health_status = []

        for author, commit_date in latest_commit_per_author.items():
            hours_diff = (now - commit_date).total_seconds() / 3600

            if hours_diff <= 48:
                status = "🟢 Active"
            elif hours_diff <= 6000:
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

    except Exception as e:
        return {"error": str(e)}

@router.get("/user-repos")
def get_user_repos(username: str):
    try:
        token = os.getenv("GITHUB_TOKEN")

        github_api_url = f"https://api.github.com/users/{username}/repos"

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

        repos = response.json()

        result = []

        for repo in repos:
            result.append({
                "name": repo["name"],
                "full_name": repo["full_name"],
                "private": repo["private"],
                "language": repo["language"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"]
            })

        return result

    except Exception as e:
        return {"error": str(e)}
