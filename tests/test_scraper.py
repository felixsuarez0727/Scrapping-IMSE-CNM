"""
Basic tests for the IMSE-Scraper.
"""
import os
import pytest
from imse_scraper import IMSEScraperAdvanced


def test_scraper_initialization():
    """Test that the scraper can be initialized."""
    scraper = IMSEScraperAdvanced(output_dir="test_data")
    assert scraper is not None
    assert scraper.base_url == "http://www.imse-cnm.csic.es/"
    assert scraper.output_dir == "test_data"


def test_output_directory_creation():
    """Test that the output directory is created."""
    test_dir = "test_output_dir"
    if os.path.exists(test_dir):
        os.rmdir(test_dir)
    
    scraper = IMSEScraperAdvanced(output_dir=test_dir)
    assert os.path.exists(test_dir)
    
    # Clean up
    os.rmdir(test_dir)


@pytest.mark.skipif("CI" in os.environ, reason="Skipping network tests in CI")
def test_main_sections_extraction():
    """
    Test extraction of main sections.
    
    This test makes actual network requests, so it should be skipped in CI.
    """
    scraper = IMSEScraperAdvanced(output_dir="test_data")
    sections = scraper.extract_main_sections()
    
    assert isinstance(sections, list)
    assert len(sections) > 0
    
    # Check that section items have the required fields
    for section in sections:
        assert 'title' in section
        assert 'url' in section
        assert 'section_id' in section
        
        assert isinstance(section['title'], str)
        assert isinstance(section['url'], str)
        assert isinstance(section['section_id'], str)
        
        assert section['title']  # Title should not be empty
        assert section['url'].startswith('http')  # URL should be absolute