from pydantic import BaseModel, Field
from typing import List, Optional

class GitHubUser(BaseModel):
    login: str

class PullRequestModel(BaseModel):
    number: int
    title: str
    html_url: str
    user: GitHubUser

class RepositoryModel(BaseModel):
    full_name: str

class PullRequestPayload(BaseModel):
    action: str
    pull_request: PullRequestModel
    repository: RepositoryModel

class PRFile(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None
