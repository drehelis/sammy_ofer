from unittest.mock import MagicMock, patch

import pytest

from web_scrape import WebScrape


@pytest.fixture
def mock_response():
    """Create a mock response for requests.get reflecting Elementor widgets"""
    mock = MagicMock()
    mock.text = """
    <div class="elementor-element elementor-element-1234567 elementor-widget elementor-widget-text-editor">
        <div class="elementor-widget-container"><p>ליגת העל</p></div>
    </div>
    <div class="elementor-element elementor-element-2345678 elementor-widget elementor-widget-text-editor">
        <div class="elementor-widget-container"><p>מכבי חיפה</p></div>
    </div>
    <div class="elementor-element elementor-element-3456789 elementor-widget elementor-widget-text-editor is-mac">
        <div class="elementor-widget-container"><p>20-03-2024</p><p>20:30</p></div>
    </div>
    <div class="elementor-element elementor-element-4567890 elementor-widget elementor-widget-text-editor">
        <div class="elementor-widget-container"><p>הפועל חיפה</p></div>
    </div>
    """
    mock.raise_for_status.return_value = None
    return mock


@patch("requests.get")
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
