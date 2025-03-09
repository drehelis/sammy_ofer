import pytest
from unittest.mock import patch, MagicMock
from web_scrape import WebScrape

@pytest.fixture
def mock_response():
    """Create a mock response for requests.get"""
    mock = MagicMock()
    mock.text = """
    <div class="elementor-element elementor-element-1234567 elementor-widget elementor-widget-text-editor">
        <div><p>ליגת העל</p></div>
        <div><p>מכבי חיפה</p></div>
        <div><p>20-03-2024 20:30</p></div>
        <div><p>הפועל חיפה</p></div>
    </div>
    """
    mock.raise_for_status.return_value = None
    return mock

@patch('requests.get')
def test_scrape(mock_get, mock_response):
    """Test the scrape method of WebScrape class"""
    mock_get.return_value = mock_response
    
    scraper = WebScrape()
    result = scraper.scrape()

    print(result)
    
    assert isinstance(result, dict)
    assert "game_1" in result
    assert len(result["game_1"]) == 4
    assert result["game_1"][0] == "ליגת העל"
    assert result["game_1"][1] == "מכבי חיפה"
    assert result["game_1"][2] == "20-03-2024 20:30"
    assert result["game_1"][3] == "הפועל חיפה"
