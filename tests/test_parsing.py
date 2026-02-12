import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import parse_json_response

def test_parse_clean_json():
    text = '{"key": "value"}'
    assert parse_json_response(text) == {"key": "value"}

def test_parse_markdown_json():
    text = 'Here is the json:\n```json\n{"key": "value"}\n```'
    assert parse_json_response(text) == {"key": "value"}

def test_parse_markdown_no_lang():
    text = '```\n{"key": "value"}\n```'
    assert parse_json_response(text) == {"key": "value"}

def test_parse_with_surrounding_text():
    text = 'Here is the response:\n```json\n{"key": "value"}\n```\nHope this helps!'
    assert parse_json_response(text) == {"key": "value"}

def test_parse_invalid_json():
    text = 'Not a json'
    assert parse_json_response(text) is None

def test_parse_list():
    text = '[1, 2, 3]'
    assert parse_json_response(text) == [1, 2, 3]

if __name__ == "__main__":
    tests = [
        test_parse_clean_json,
        test_parse_markdown_json,
        test_parse_markdown_no_lang,
        test_parse_with_surrounding_text,
        test_parse_invalid_json,
        test_parse_list
    ]
    
    success = 0
    for test in tests:
        try:
            test()
            print(f"PASSED: {test.__name__}")
            success += 1
        except AssertionError as e:
            print(f"FAILED: {test.__name__}")
            # print details
    
    print(f"\n{success}/{len(tests)} tests passed.")
    if success != len(tests):
        sys.exit(1)
