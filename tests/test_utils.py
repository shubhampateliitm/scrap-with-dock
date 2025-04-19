"""
Unit tests for the utils module.
"""

import pytest
from python_project.scrape_sentiments.utils import example_utility_function

def test_example_utility_function():
    """Test for the example_utility_function."""
    result = example_utility_function("input")
    assert result == "expected_output", "The utility function did not return the expected output."