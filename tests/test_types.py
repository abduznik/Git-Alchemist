import pytest
from src.types import RepoMetadata, Topic

def test_repometadata_valid_parsing():
    data = {
        "name": "my-repo",
        "description": "A test repo",
        "url": "https://github.com/test",
        "isPrivate": True,
        "isArchived": False,
        "stargazerCount": 42,
        "repositoryTopics": [{"name": "python"}, {"name": "testing"}]
    }
    repo = RepoMetadata.from_dict(data)
    assert repo.name == "my-repo"
    assert repo.description == "A test repo"
    assert repo.url == "https://github.com/test"
    assert repo.isPrivate is True
    assert repo.isArchived is False
    assert repo.stargazerCount == 42
    assert len(repo.repositoryTopics) == 2
    assert repo.repositoryTopics[0].name == "python"

def test_repometadata_missing_name():
    with pytest.raises(ValueError, match="valid 'name' string"):
        RepoMetadata.from_dict({"description": "missing name"})

def test_repometadata_invalid_type_stargazer():
    with pytest.raises(TypeError, match="must be an integer"):
        RepoMetadata.from_dict({"name": "test", "stargazerCount": "forty-two"})

def test_repometadata_invalid_type_private():
    with pytest.raises(TypeError, match="must be a boolean"):
        RepoMetadata.from_dict({"name": "test", "isPrivate": "yes"})

def test_repometadata_default_values():
    repo = RepoMetadata.from_dict({"name": "minimal"})
    assert repo.name == "minimal"
    assert repo.description is None
    assert repo.url == ""
    assert repo.isPrivate is False
    assert repo.isArchived is False
    assert repo.stargazerCount == 0
    assert repo.repositoryTopics is None
