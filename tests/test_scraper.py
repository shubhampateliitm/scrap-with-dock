"""
Unit tests for the scraper module.
"""

import pytest
from python_project.scrape_sentiments.scraper import scrape_data

def test_scrape_data():
    """Test for the scrape_data function."""
    sample_url = "http://example.com"
    result = scrape_data(sample_url)
    assert isinstance(result, dict), "The scrape_data function should return a dictionary."
    assert "data" in result, "The result dictionary should contain a 'data' key."