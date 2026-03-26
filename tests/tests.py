"""
Tests for swim-analysis: import requests, swimcloud, swimphone scrapper
"""
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd

import importlib.util

# Paths to modules with non-standard filenames
BASE = Path(__file__).resolve().parent.parent
IMPORT_REQUESTS_PATH = BASE / "import requests.py"
SWIMPHONE_SCRAPPER_PATH = BASE / "swimphone scrapper.py"

# Load and execute "import requests.py" - mock requests first (module does HTTP on load)
def _mock_requests_for_import(url, *args, **kwargs):
    """Return valid HTML so import requests.py completes without error."""
    r = MagicMock()
    url_str = str(url)
    if "event_order" in url_str or "smid=" in url_str:
        r.text = """<html><body><table>
        <tr><th>Event</th><th>Prelims</th></tr>
        <tr>
            <td>1</td><td>M</td><td>100</td><td>Free</td><td>x</td>
            <td><a href="http://example.com/psych">Psych</a></td><td>x</td><td>x</td>
            <td><a href="http://example.com/prelims">Prelims</a></td>
        </tr>
        </table></body></html>"""
    elif "prelims" in url_str:
        # Prelims table: cells[0]=rank, cells[5]=time
        prelim_rows = "".join(
            f'<tr><td>{i+1}</td><td>x</td><td>x</td><td>x</td><td>x</td><td>51.{i:02d}</td></tr>'
            for i in range(25)
        )
        r.text = f"<html><body><table><tbody>{prelim_rows}</tbody></table></body></html>"
    else:
        # Psych table: cells[0]=rank, cells[3]=name, cells[4]=time
        psych_rows = "".join(
            f'<tr><td>{i+1}</td><td>x</td><td>x</td><td>Swimmer{i+1}</td><td>52.{i:02d}</td></tr>'
            for i in range(25)
        )
        r.text = f"<html><body><table><tbody>{psych_rows}</tbody></table></body></html>"
    return r

_import_spec = importlib.util.spec_from_file_location("swimphone_import", IMPORT_REQUESTS_PATH)
swimphone_import = importlib.util.module_from_spec(_import_spec)
sys.modules["swimphone_import"] = swimphone_import
with patch("requests.get", side_effect=_mock_requests_for_import):
    _import_spec.loader.exec_module(swimphone_import)

# Load "swimphone scrapper.py" module (executed lazily in tests to allow mocking)
_scrapper_spec = importlib.util.spec_from_file_location("swimphone_scrapper", SWIMPHONE_SCRAPPER_PATH)
swimphone_scrapper = importlib.util.module_from_spec(_scrapper_spec)


class TestImportRequestsModule(unittest.TestCase):
    """Tests for import requests.py (swimphone meet event order scraper)"""

    def test_time_to_seconds_with_colon(self):
        """Convert MM:SS.ss format to seconds"""
        self.assertAlmostEqual(swimphone_import.time_to_seconds("2:22.66"), 142.66)
        self.assertAlmostEqual(swimphone_import.time_to_seconds("1:00.00"), 60.0)
        self.assertAlmostEqual(swimphone_import.time_to_seconds("0:52.34"), 52.34)

    def test_time_to_seconds_without_colon(self):
        """Convert SS.ss format to seconds"""
        self.assertAlmostEqual(swimphone_import.time_to_seconds("52.34"), 52.34)
        self.assertAlmostEqual(swimphone_import.time_to_seconds("23.45"), 23.45)

    def test_time_to_seconds_invalid(self):
        """Invalid/missing times return None"""
        self.assertIsNone(swimphone_import.time_to_seconds(""))
        self.assertIsNone(swimphone_import.time_to_seconds("DQ"))
        self.assertIsNone(swimphone_import.time_to_seconds("NT"))
        self.assertIsNone(swimphone_import.time_to_seconds(None))

    @patch("swimphone_import.requests.get")
    def test_get_psych_table(self, mock_get):
        """Test psych table parsing from HTML"""
        mock_response = MagicMock()
        mock_response.text = """
        <html><body><table>
        <tbody>
            <tr><td>1</td><td>x</td><td>x</td><td>Alice</td><td>52.34</td></tr>
            <tr><td>2</td><td>x</td><td>x</td><td>Bob</td><td>53.12</td></tr>
            <tr><td>3</td><td>x</td><td>x</td><td>Carol</td><td>54.00</td></tr>
        </tbody>
        </table></body></html>
        """
        mock_get.return_value = mock_response

        df = swimphone_import.get_psych_table("http://example.com/psych")

        self.assertEqual(len(df), 3)
        self.assertEqual(list(df.columns), ["Rank", "Name", "Seed Time"])
        self.assertEqual(df.iloc[0]["Name"], "Alice")
        self.assertEqual(df.iloc[0]["Seed Time"], "52.34")
        self.assertEqual(df.iloc[1]["Rank"], "2")
        mock_get.assert_called_once()

    @patch("swimphone_import.requests.get")
    def test_get_psych_table_empty(self, mock_get):
        """Test psych table with no tbody returns empty DataFrame"""
        mock_response = MagicMock()
        mock_response.text = "<html><body><table></table></body></html>"
        mock_get.return_value = mock_response

        df = swimphone_import.get_psych_table("http://example.com/empty")

        self.assertTrue(df.empty)
        self.assertEqual(list(df.columns), ["Rank", "Name", "Seed Time"])

    @patch("swimphone_import.requests.get")
    def test_get_prelims_table(self, mock_get):
        """Test prelims table parsing"""
        mock_response = MagicMock()
        mock_response.text = """
        <html><body><table>
        <tbody>
            <tr><td>1</td><td>x</td><td>x</td><td>x</td><td>x</td><td>51.00</td></tr>
            <tr><td>2</td><td>x</td><td>x</td><td>x</td><td>x</td><td>52.10</td></tr>
            <tr><td></td><td>x</td><td>x</td><td>x</td><td>x</td><td>53.20</td></tr>
        </tbody>
        </table></body></html>
        """
        mock_get.return_value = mock_response

        df = swimphone_import.get_prelims_table("http://example.com/prelims")

        self.assertEqual(len(df), 2)  # row with empty first cell is skipped
        self.assertEqual(list(df.columns), ["PrelimsTime"])
        self.assertEqual(df.iloc[0]["PrelimsTime"], "51.00")
        self.assertEqual(df.iloc[1]["PrelimsTime"], "52.10")


class TestSwimcloud(unittest.TestCase):
    """Tests for swimcloud.py"""

    def setUp(self):
        # Import swimcloud - normal module name
        if str(BASE) not in sys.path:
            sys.path.insert(0, str(BASE))
        import swimcloud as sc
        self.swimcloud = sc

    @patch("swimcloud.requests.get")
    def test_get_swim_links_success(self, mock_get):
        """Test extracting event links from meet page"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html><body>
        <a href="/286121?event=1">100 Free</a>
        <a href="/286121?event=2">200 Back</a>
        <a href="/286121?event=3">Swimoff 100 Free</a>
        <a href="/other/123">Other</a>
        </body></html>
        """
        mock_get.return_value = mock_response

        links = self.swimcloud.get_swim_links("https://www.swimcloud.com/results/286121/")

        self.assertIn("100 Free", links)
        self.assertIn("200 Back", links)
        self.assertNotIn("Swimoff 100 Free", links)  # Swimoff filtered out
        self.assertIn("https://www.swimcloud.com/286121?event=1", links["100 Free"])

    @patch("swimcloud.requests.get")
    def test_get_swim_links_failure(self, mock_get):
        """Test handling of failed HTTP request"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        links = self.swimcloud.get_swim_links("https://www.swimcloud.com/bad/")

        self.assertEqual(links, {})

    @patch("swimcloud.requests.get")
    def test_find_scoring_events(self, mock_get):
        """Test extracting prelims times for ranks 8, 16, 24"""
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
        <div>Preliminaries</div>
        <table>
        <tr><th>Name</th><th>x</th><th>Time</th></tr>
        <tr><td>1st</td><td>x</td><td>48.00</td></tr>
        <tr><td>2nd</td><td>x</td><td>48.10</td></tr>
        <tr><td>3rd</td><td>x</td><td>48.20</td></tr>
        <tr><td>4th</td><td>x</td><td>48.30</td></tr>
        <tr><td>5th</td><td>x</td><td>48.40</td></tr>
        <tr><td>6th</td><td>x</td><td>48.50</td></tr>
        <tr><td>7th</td><td>x</td><td>48.60</td></tr>
        <tr><td>8th</td><td>x</td><td>48.70</td></tr>
        <tr><td>9th</td><td>x</td><td>48.80</td></tr>
        <tr><td>10th</td><td>x</td><td>48.90</td></tr>
        <tr><td>11th</td><td>x</td><td>49.00</td></tr>
        <tr><td>12th</td><td>x</td><td>49.10</td></tr>
        <tr><td>13th</td><td>x</td><td>49.20</td></tr>
        <tr><td>14th</td><td>x</td><td>49.30</td></tr>
        <tr><td>15th</td><td>x</td><td>49.40</td></tr>
        <tr><td>16th</td><td>x</td><td>49.50</td></tr>
        <tr><td>17th</td><td>x</td><td>49.60</td></tr>
        <tr><td>18th</td><td>x</td><td>49.70</td></tr>
        <tr><td>19th</td><td>x</td><td>49.80</td></tr>
        <tr><td>20th</td><td>x</td><td>49.90</td></tr>
        <tr><td>21st</td><td>x</td><td>50.00</td></tr>
        <tr><td>22nd</td><td>x</td><td>50.10</td></tr>
        <tr><td>23rd</td><td>x</td><td>50.20</td></tr>
        <tr><td>24th</td><td>x</td><td>50.30</td></tr>
        </table>
        </body></html>
        """
        mock_get.return_value = mock_response

        results = self.swimcloud.find_scoring_events("https://www.swimcloud.com/event/123/")

        self.assertEqual(results[8], "48.70")
        self.assertEqual(results[16], "49.50")
        self.assertEqual(results[24], "50.30")

    @patch("swimcloud.requests.get")
    def test_find_scoring_events_no_prelims(self, mock_get):
        """Test when no Preliminaries section exists"""
        mock_response = MagicMock()
        mock_response.text = "<html><body><div>Finals</div></body></html>"
        mock_get.return_value = mock_response

        results = self.swimcloud.find_scoring_events("https://www.swimcloud.com/event/123/")

        self.assertEqual(results, {0: "No prelims"})


class TestSwimphoneScrapper(unittest.TestCase):
    """Tests for swimphone scrapper.py (swimmers by club)"""

    def test_swimphone_table_parsing_logic(self):
        """Test the parsing logic: sort by Club and value_counts"""
        # Simulates what pd.read_html would return for swimphone swimmers page
        html = """
        <table>
        <thead><tr><th>Name</th><th>Club</th><th>Age</th></tr></thead>
        <tbody>
        <tr><td>Alice</td><td>Team B</td><td>18</td></tr>
        <tr><td>Bob</td><td>Team A</td><td>17</td></tr>
        <tr><td>Carol</td><td>Team A</td><td>16</td></tr>
        <tr><td>Dan</td><td>Team B</td><td>19</td></tr>
        <tr><td>Eve</td><td>Team A</td><td>18</td></tr>
        </tbody>
        </table>
        """
        tables = pd.read_html(StringIO(html))
        tables[0] = tables[0].sort_values(by="Club")
        club_counts = tables[0]["Club"].value_counts()

        self.assertEqual(club_counts["Team A"], 3)
        self.assertEqual(club_counts["Team B"], 2)
        self.assertEqual(club_counts.sum(), 5)

    @patch("requests.get")
    def test_swimphone_full_flow(self, mock_get):
        """Test full flow with mocked HTTP response"""
        mock_response = MagicMock()
        mock_response.text = """
        <table>
        <thead><tr><th>Name</th><th>Club</th><th>Other</th></tr></thead>
        <tbody>
        <tr><td>A</td><td>Alpha</td><td>1</td></tr>
        <tr><td>B</td><td>Beta</td><td>2</td></tr>
        <tr><td>C</td><td>Alpha</td><td>3</td></tr>
        </tbody>
        </table>
        """
        mock_get.return_value = mock_response

        # Execute the scrapper - must load with patch active (patch requests.get globally)
        sys.modules["swimphone_scrapper"] = swimphone_scrapper
        _scrapper_spec.loader.exec_module(swimphone_scrapper)

        # Verify request was made with correct headers
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("swimphone.com", call_args[0][0])
        self.assertIn("User-Agent", call_args[1]["headers"])


if __name__ == "__main__":
    unittest.main()
