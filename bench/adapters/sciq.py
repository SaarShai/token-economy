import json

def load(path, n=None):
    with open(path, 'r') as f:
        data = json.load(f)
    result = []
    for idx, entry in enumerate(data):
        if not entry['support']:
            continue
        item = {
            'id': idx,
            'context': entry['support'],
            'question': entry['question'],
            'answer': entry['correct_answer'],
            'type': "multiple_choice",
            'meta': {'distractors': [entry[f'distractor{i}'] for i in range(1,4)]}
        }
        result.append(item)
        if n is not None and len(result) >= n:
            break
    return result
