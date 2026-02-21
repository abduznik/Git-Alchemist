from typing import TypedDict, List, Optional

class Topic(TypedDict):
    name: str

class RepoMetadata(TypedDict):
    name: str
    description: Optional[str]
    url: str
    isPrivate: bool
    isArchived: bool
    stargazerCount: int
    repositoryTopics: Optional[List[Topic]]
