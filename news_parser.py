import feedparser
import requests
from bs4 import BeautifulSoup
import hashlib
import sqlite3
from celery_config import classify_article # Import Celery app for task queuing


# List of RSS feeds to parse
rss_feeds = [
    'http://rss.cnn.com/rss/cnn_topstories.rss',
    'https://qz.com/rss',
    'http://feeds.foxnews.com/foxnews/politics',
    'http://feeds.feedburner.com/NewshourWorld',
    'https://feeds.bbci.co.uk/news/world/asia/india/rss.xml'
]

# Function to extract full content from article URL (using BeautifulSoup)
def extract_content_from_article(article_url):
    try:
        response = requests.get(article_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find('article')
        if content:
            return content.get_text(separator='\n', strip=True)
        return "No content found, possibly a video article."
    except Exception as e:
        return f"Error fetching content: {str(e)}"

# Function to extract content from an RSS entry (if available in the 'content' tag)
def extract_content_from_tag(entry):
    if 'content' in entry or 'content:encoded' in entry:
        html_content = entry.content[0].value
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator='\n', strip=True)
    return None

# Function to extract full content (fallback to manual scraping from article's URL)
def extract_full_content(article_url):
    try:
        response = requests.get(article_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Customize based on the website's HTML structure
        content = soup.find('div', class_='live-story__items') or \
                  soup.find('div', class_='article__content') or \
                  soup.find('div', class_='js_post-content')
        if content:
            return content.get_text(separator='\n', strip=True)
        return "Content not found"
    except Exception as e:
        return f"Error fetching content: {str(e)}"



# Function to generate a hash for article URLs to track duplicates
def get_article_hash(article_link):
    return hashlib.md5(article_link.encode('utf-8')).hexdigest()

# Function to parse RSS feed and extract articles
def parse_rss_feed(feed_url, seen_articles):
    feed = feedparser.parse(feed_url)
    articles = []

    for entry in feed['items']:
        title = entry.get('title', 'No title')
        link = entry.get('link', 'No link')
        pub_date = entry.get('published', 'No publication date')
        summary = entry.get('summary', 'No summary')

        # Try to extract content
        full_content = None
        if feed_url == 'https://feeds.bbci.co.uk/news/world/asia/india/rss.xml':
            full_content = extract_content_from_article(link)

        if not full_content:
            full_content = extract_content_from_tag(entry)

        # Generate unique hash for article based on the 'link'
        article_hash = get_article_hash(link)

        # Skip duplicates based on article hash
        if article_hash in seen_articles:
            continue

        if not full_content:
            # Fallback to extract content directly from the article URL
            full_content = extract_full_content(link)

        # Add the article to the list and mark it as seen
        articles.append({
            'title': title,
            'link': link,
            'pub_date': pub_date,
            'summary': summary,
            'full_content': full_content
        })

        seen_articles.add(article_hash)

    return articles

# Function to insert article into the SQLite database
def insert_article(conn, article):
    sql = '''INSERT OR IGNORE INTO articles(title, link, pub_date, summary, full_content)
             VALUES(?, ?, ?, ?, ?)'''
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (article['title'], article['link'], article['pub_date'], article['summary'], article['full_content']))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error inserting article: {e}")
        return None

# Create SQLite connection
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

# Create articles table if it doesn't exist
def create_table(conn):
    sql_create_articles_table = '''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT UNIQUE,
            pub_date TEXT,
            summary TEXT,
            full_content TEXT,
            category TEXT
        );
    '''
    try:
        cursor = conn.cursor()
        cursor.execute(sql_create_articles_table)
        conn.commit()
    except sqlite3.Error as e:
        print(e)



def main():
    seen_articles = set() 
    database = "news_articles.db"

    conn = create_connection(database)
    if conn is not None:
        create_table(conn)
    else:
        print("Error! cannot create the database connection.")
        return

    # Parse each RSS feed
    for feed_url in rss_feeds:
        print(f"Parsing feed: {feed_url}")
        articles = parse_rss_feed(feed_url, seen_articles)


        for article in articles:
            print(f"Title: {article['title']}")
            print(f"Link: {article['link']}")
            print(f"Publication Date: {article['pub_date']}")
            print(f"Summary: {article['summary']}")
            full_content = article.get('full_content', 'No full content available.')
            print(f"Full Content: {full_content[:200]}...")

            print('-' * 80)
            

            article_id = insert_article(conn, article)
            if article_id is not None:
                print(f"Inserted article: {article['title']} (ID: {article_id})")


            classify_article.send(article) 
    conn.close()

if __name__ == "__main__":
    main()
