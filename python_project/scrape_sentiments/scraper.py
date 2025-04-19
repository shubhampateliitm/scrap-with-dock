"""
Web scraping logic for the scrape_sentiments project.
"""
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from .config import SELENIUM_OPTIONS
import pandas as pd
import time
import random
from retrying import retry
import logging

# Configure logging
log_level = logging.INFO  # Default log level
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class BaseScraper(ABC):
    """Abstract base class for web scrapers."""

    def __init__(self, date, search_terms=None):
        self.date = date
        self.search_terms = search_terms
        self.driver = None

    def setup_driver(self):
        """Set up the Selenium WebDriver with options. If Chrome is not available, attempt to set it up."""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument(SELENIUM_OPTIONS["headless"])
            options.add_argument(SELENIUM_OPTIONS["disable_gpu"])
            options.add_argument(SELENIUM_OPTIONS["window_size"])
            options.add_argument(SELENIUM_OPTIONS["lang"])
            options.add_argument(SELENIUM_OPTIONS["disable_blink_features"])
            options.add_argument(SELENIUM_OPTIONS["user_agent"])
            self.driver = webdriver.Chrome(options=options)
        except Exception as e:
            logging.error("Chrome WebDriver setup failed: %s", str(e))
            logging.info("Attempting to set up Chrome WebDriver.")
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            options = webdriver.ChromeOptions()
            options.add_argument(SELENIUM_OPTIONS["headless"])
            options.add_argument(SELENIUM_OPTIONS["disable_gpu"])
            options.add_argument(SELENIUM_OPTIONS["window_size"])
            options.add_argument(SELENIUM_OPTIONS["lang"])
            options.add_argument(SELENIUM_OPTIONS["disable_blink_features"])
            options.add_argument(SELENIUM_OPTIONS["user_agent"])
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def close_driver(self):
        """Close the Selenium WebDriver."""
        if self.driver:
            self.driver.quit()

    @abstractmethod
    def scrape(self):
        """Abstract method to scrape data. Must be implemented by subclasses."""
        pass

class YourStoryScraper(BaseScraper):
    """Scraper for YourStory website."""

    def __init__(self, date, search_terms):
        super().__init__(date, search_terms)
        logging.info("Initialized YourStoryScraper with date: %s and search terms: %s", date, search_terms)

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=3000)
    def fetch_article_urls(self, page_source, target_date):
        logging.info("Fetching article URLs for target date: %s", target_date)
        time.sleep(random.uniform(1, 3))  # Random delay to avoid bot detection
        soup = BeautifulSoup(page_source, "html.parser")
        story_div = soup.find("div", class_="storyItem")
        if not story_div:
            logging.warning("No story items found on the page.")
            return []

        nested_divs = story_div.find_all(class_="sc-68e2f78-2 bLuPDa")
        base_url = self.driver.current_url
        final_urls_with_dates = []

        for div in nested_divs:
            li_items = div.find_all("li", class_="sc-c9f6afaa-0")
            for li in li_items:
                a_tag = li.find("a")
                date_of_article = li.find("span", class_="sc-36431a7-0 dpmmXH").get_text(strip=True)
                if a_tag and a_tag.get("href"):
                    relative_url = a_tag["href"]
                    absolute_url = urljoin(base_url, relative_url)
                    final_urls_with_dates.append((date_of_article, absolute_url))

        logging.info("Fetched %d article URLs for target date: %s", len(final_urls_with_dates), target_date)

        # Filter URLs by the target date
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        filtered_urls_with_dates = [
            (date, url) for (date, url) in final_urls_with_dates
            if datetime.strptime(date, "%d/%m/%Y") == target_date_obj
        ]

        if not filtered_urls_with_dates:
            logging.warning("No articles found for the given date: %s", target_date)
            return []

        # Limit to no more than 5 URLs
        return filtered_urls_with_dates[:5]

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=3000)
    def fetch_article_content(self, article_url):
        logging.info("Fetching content for article URL: %s", article_url)
        try:
            self.setup_driver()
            time.sleep(random.uniform(1, 3))  # Random delay to avoid bot detection
            self.driver.get(article_url)

            # Wait for the article container to load
            WebDriverWait(self.driver, 120).until(
                EC.visibility_of_element_located((By.ID, "article_container"))
            )

            # Scrape article details
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            article = soup.find("div", id="article_container").get_text(separator=" ", strip=True)
            header = soup.find("h1").get_text(separator=" ", strip=True)
            tagline = soup.find("h2").get_text(separator=" ", strip=True)

            logging.info("Successfully fetched content for article URL: %s", article_url)
            return article, header, tagline
        except Exception as e:
            logging.error("Error fetching content for article URL: %s. Error: %s", article_url, str(e))
            logging.error("Page source at the time of error: %s", self.driver.page_source[:100])
            logging.info("Re-setting up Selenium WebDriver due to failure.")
            self.close_driver()
            self.setup_driver()
            raise
        finally:
            self.close_driver()

    def get_scraped_results(self, article_urls):
        """Fetch and return scraped results for a list of article URLs as a pandas DataFrame, including sentiment scores."""
        from .sentiment_analysis import analyze_sentiment

        results = []
        for article_date, article_url in article_urls:
            # Fetch article content
            article, header, tagline = self.fetch_article_content(article_url)

            # Analyze sentiment
            sentiment_score = analyze_sentiment(article)

            # Append result
            results.append({
                "date": article_date,
                "url": article_url,
                "article": article,
                "header": header,
                "tagline": tagline,
                "sentiment_score": sentiment_score,
            })

        # Convert results to a pandas DataFrame
        return pd.DataFrame(results)

    def scrape(self):
        logging.info("Starting scraping process.")
        all_results = []
        try:
            logging.info("WebDriver setup completed.")
            for search_term in self.search_terms:
                try:
                    self.setup_driver()
                    logging.info("Scraping articles for search term: %s", search_term)
                    base_url = f"https://yourstory.com/search?q={search_term}&page=1"
                    self.driver.get(base_url)

                # Wait for the element with class 'storyItem' to be visible
                    WebDriverWait(self.driver, 120).until(
                        EC.visibility_of_element_located((By.CLASS_NAME, "storyItem"))
                    )
                    page_source = self.driver.page_source
                    article_urls = self.fetch_article_urls(page_source, self.date)
                except:
                    raise("fail to fetch")
                finally:
                    self.close_driver()
                # Use a separate function to get scraped results
                results = self.get_scraped_results(article_urls)
                all_results.append(results)
        except TimeoutException:
            logging.error("Timeout while waiting for the page to load.")
        except Exception as e:
            logging.error("An error occurred during scraping: %s", str(e))
        finally:
            self.close_driver()
            logging.info("WebDriver closed.")

        # Combine all results into a single DataFrame
        if all_results:
            logging.info("Combining all scraped results into a single DataFrame.")
            return pd.concat(all_results, ignore_index=True)
        else:
            logging.warning("No results to combine. Returning an empty DataFrame.")
            return pd.DataFrame()

class FinshotsScraper(BaseScraper):
    """Scraper for Finshots website."""

    def __init__(self, date, search_terms):
        super().__init__(date, search_terms)

    def scrape(self):
        """Scrape data from Finshots."""
        # Add logic to scrape data from Finshots
        print(f"Scraping Finshots for date: {self.date}")