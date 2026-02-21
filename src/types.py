from typing import List, Optional, Any
from dataclasses import dataclass

@dataclass
class Topic:
    name: str

    @classmethod
    def from_dict(cls, data: Any) -> 'Topic':
        if not isinstance(data, dict):
            raise TypeError("Topic must be a dictionary")
        name = data.get('name')
        if not isinstance(name, str):
            raise TypeError("Topic 'name' must be a string")
        return cls(name=name)

@dataclass
class RepoMetadata:
    name: str
    description: Optional[str] = None
    url: str = ''
    isPrivate: bool = False
    isArchived: bool = False
    stargazerCount: int = 0
    repositoryTopics: Optional[List[Topic]] = None

    @classmethod
    def from_dict(cls, data: Any) -> 'RepoMetadata':
        if not isinstance(data, dict):
            raise TypeError("RepoMetadata must be a dictionary")
        
        name = data.get('name')
        if not isinstance(name, str) or not name:
            raise ValueError("Repository must have a valid 'name'")
            
        description = data.get('description')
        if description is not None and not isinstance(description, str):
            description = str(description)

        url = data.get('url', '')
        isPrivate = bool(data.get('isPrivate', False))
        isArchived = bool(data.get('isArchived', False))
        
        stargazerCount = data.get('stargazerCount', 0)
        if isinstance(stargazerCount, str) and stargazerCount.isdigit():
            stargazerCount = int(stargazerCount)
        elif not isinstance(stargazerCount, int):
            stargazerCount = 0

        raw_topics = data.get('repositoryTopics')
        topics = None
        if raw_topics is not None:
            if isinstance(raw_topics, list):
                topics = [Topic.from_dict(t) for t in raw_topics if isinstance(t, dict)]
            else:
                topics = []

        return cls(
            name=name,
            description=description,
            url=url,
            isPrivate=isPrivate,
            isArchived=isArchived,
            stargazerCount=stargazerCount,
            repositoryTopics=topics
        )
