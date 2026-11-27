"""Original synthetic examples authored for this project. No scraped code."""
import json
from pathlib import Path

TASKS = [
 ("remove duplicates from a Python list while preserving order", "Use a set to track hashable values already seen. The empty list stays empty.", "python", "def unique(items):\n    seen = set()\n    result = []\n    for item in items:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result"),
 ("count words in a Python string", "Split on whitespace and count each token. Punctuation is preserved.", "python", "from collections import Counter\n\ndef word_counts(text):\n    return dict(Counter(text.split()))"),
 ("check whether a Python string is a palindrome ignoring case and punctuation", "Normalize to lowercase alphanumeric characters, then compare with the reverse. An empty normalized string is a palindrome.", "python", "def is_palindrome(text):\n    cleaned = ''.join(c.lower() for c in text if c.isalnum())\n    return cleaned == cleaned[::-1]"),
 ("find the largest value in a Python list", "Reject an empty input explicitly, then use max.", "python", "def largest(values):\n    if not values:\n        raise ValueError('values must not be empty')\n    return max(values)"),
 ("chunk a Python list into groups of a given size", "Validate a positive integer size. The last chunk may be shorter.", "python", "def chunks(items, size):\n    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:\n        raise ValueError('size must be a positive integer')\n    return [items[i:i + size] for i in range(0, len(items), size)]"),
 ("flatten a Python list by one level", "A nested comprehension flattens exactly one level.", "python", "def flatten(groups):\n    return [item for group in groups for item in group]"),
 ("compute factorial in Python", "Validate a nonnegative integer and multiply iteratively. Zero factorial is one.", "python", "def factorial(n):\n    if not isinstance(n, int) or isinstance(n, bool) or n < 0:\n        raise ValueError('n must be a nonnegative integer')\n    result = 1\n    for i in range(2, n + 1):\n        result *= i\n    return result"),
 ("check if an integer is prime in Python", "Try divisors up to the square root. Integers below two are not prime.", "python", "def is_prime(n):\n    if n < 2:\n        return False\n    d = 2\n    while d * d <= n:\n        if n % d == 0:\n            return False\n        d += 1\n    return True"),
 ("search a sorted Python list with binary search", "Maintain inclusive bounds. Return minus one if the target is absent.", "python", "def binary_search(values, target):\n    left, right = 0, len(values) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if values[mid] == target:\n            return mid\n        if values[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1"),
 ("read a UTF-8 JSON file in Python", "A context manager closes the file. File and JSON errors propagate to the caller.", "python", "import json\n\ndef read_json(path):\n    with open(path, encoding='utf-8') as file:\n        return json.load(file)"),
 ("sort Python dictionaries by age", "Use a key function. Each dictionary must contain an age value of a comparable type.", "python", "def sort_by_age(people):\n    return sorted(people, key=lambda person: person['age'])"),
 ("group Python records by their category", "Accumulate lists per category. Each record must contain the category key.", "python", "def group_by_category(records):\n    groups = {}\n    for record in records:\n        groups.setdefault(record['category'], []).append(record)\n    return groups"),
 ("fix a Python function using a mutable default list", "Use None as the default so independent calls do not share a list.", "python", "def add_item(item, items=None):\n    if items is None:\n        items = []\n    items.append(item)\n    return items"),
 ("remove even values from a Python list safely", "Build a new list rather than mutating the list while iterating.", "python", "def remove_even(values):\n    return [value for value in values if value % 2 != 0]"),
 ("deduplicate a JavaScript array", "Set preserves insertion order and removes duplicate primitive values. Objects compare by reference.", "javascript", "function unique(items) {\n  return [...new Set(items)];\n}"),
 ("fetch JSON in JavaScript and handle HTTP errors", "fetch does not reject on HTTP error statuses, so check response.ok.", "javascript", "async function fetchJSON(url) {\n  const response = await fetch(url);\n  if (!response.ok) {\n    throw new Error(`HTTP ${response.status}`);\n  }\n  return response.json();\n}"),
 ("debounce a JavaScript function", "Reset the timer on each call. A normal function preserves the caller's this value.", "javascript", "function debounce(fn, delay) {\n  let timer;\n  return function (...args) {\n    clearTimeout(timer);\n    timer = setTimeout(() => fn.apply(this, args), delay);\n  };\n}"),
 ("sort numbers numerically in JavaScript", "Provide a numeric comparator. Copy the array to avoid mutating the input.", "javascript", "function sortNumbers(values) {\n  return [...values].sort((a, b) => a - b);\n}"),
 ("sum a JavaScript array", "Use reduce with an initial zero so an empty array works. Inputs should be numbers.", "javascript", "function sum(values) {\n  return values.reduce((total, value) => total + value, 0);\n}"),
 ("use a parameterized SQLite query in Python", "Pass values separately from SQL. This prevents values from being interpreted as SQL syntax.", "python", "def find_user(connection, name):\n    return connection.execute(\n        'SELECT id, name FROM users WHERE name = ?',\n        (name,)\n    ).fetchone()"),
 # Held-out tasks: no paraphrases of these enter training.
 ("calculate the mean of a Python list", "Reject an empty input to avoid division by zero.", "python", "def mean(values):\n    if not values:\n        raise ValueError('values must not be empty')\n    return sum(values) / len(values)"),
 ("reverse words in a Python string", "Split on whitespace, reverse the words, and join them with single spaces.", "python", "def reverse_words(text):\n    return ' '.join(text.split()[::-1])"),
 ("get the intersection of two Python lists", "Convert to sets for unique common values. The output has no guaranteed order.", "python", "def intersection(a, b):\n    return list(set(a) & set(b))"),
 ("capitalize the first character of a JavaScript string", "Handle an empty string before accessing the first character.", "javascript", "function capitalize(text) {\n  return text ? text[0].toUpperCase() + text.slice(1) : '';\n}"),
]

def main():
    root = Path(__file__).parent
    for split, tasks in [('train', TASKS[:20]), ('validation', TASKS[20:])]:
        rows = []
        for task, explanation, language, code in tasks:
            for prefix in ['Please ', 'Show me how to ', 'Help me ']:
                prompt = prefix + task + '.'
                if 'mutable default' in task:
                    prompt += '\nFix this function and explain the bug:\ndef add_item(item, items=[]):\n    items.append(item)\n    return items'
                    explanation = 'Python creates default argument objects once when the function is defined. The default list is therefore shared across calls. Use None as the default and create a fresh list inside the function. A caller-supplied list is still updated in place.'
                if 'remove even' in task:
                    prompt += '\nFix this code:\nfor value in values:\n    if value % 2 == 0:\n        values.remove(value)'
                if 'numerically' in task:
                    prompt += '\nFix this code: const result = values.sort();'
                rows.append({'prompt': prompt, 'response': explanation + '\n\n```' + language + '\n' + code + '\n```'})
        (root / (split + '.jsonl')).write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
        print(split, len(rows))

if __name__ == '__main__':
    main()
