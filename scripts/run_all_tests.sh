#!/bin/bash
set -e

echo "Running tests..."

python3 -m unittest discover -s tests -p 'test_*.py'

for test_file in projects/semdiff/tests/test_*.py; do
    echo "Running $test_file..."
    PYTHONPATH="$PWD/projects/semdiff" python3 "$test_file" >/tmp/token-economy-test.log
done

echo "All tests passed."
exit 0
