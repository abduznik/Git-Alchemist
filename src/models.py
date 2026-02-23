from typing import List, Optional, Any
from dataclasses import dataclass, field

@dataclass
class Topic:
    name: str

    @classmethod
    def from_dict(cls, data: Any) -> 'Topic':
        if not isinstance(data, dict):
            raise TypeError("Topic must be a dict")
        name = data.get('name')
        if not isinstance(name, str):
            raise TypeError("Topic name must be a string")
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
            raise TypeError("RepoMetadata data must be a dictionary")
        
        name = data.get('name')
        if not isinstance(name, str) or not name:
            raise ValueError("Repository must have a valid 'name' string")
            
        description = data.get('description')
        if description is not None and not isinstance(description, str):
            raise TypeError("Repository 'description' must be a string if provided")

        url = data.get('url')
        if url is not None and not isinstance(url, str):
             raise TypeError("Repository 'url' must be a string if provided")
        url = url or ''

        isPrivate = data.get('isPrivate', False)
        if not isinstance(isPrivate, bool):
             raise TypeError("Repository 'isPrivate' must be a boolean")

        isArchived = data.get('isArchived', False)
        if not isinstance(isArchived, bool):
             raise TypeError("Repository 'isArchived' must be a boolean")
        
        stargazerCount = data.get('stargazerCount', 0)
        if not isinstance(stargazerCount, int):
            raise TypeError("Repository 'stargazerCount' must be an integer")

        raw_topics = data.get('repositoryTopics')
        topics = None
        if raw_topics is not None:
            if not isinstance(raw_topics, list):
                raise TypeError("Repository 'repositoryTopics' must be a list if provided")
            topics = [Topic.from_dict(t) for t in raw_topics]

        return cls(
            name=name,
            description=description,
            url=url,
            isPrivate=isPrivate,
            isArchived=isArchived,
            stargazerCount=stargazerCount,
            repositoryTopics=topics
        )
