import spacy
import sqlite3

# Load spaCy's English model
nlp = spacy.load('en_core_web_sm')

# Predefined categories
CATEGORIES = {
    "terrorism_protest_political_unrest_riot": ["terrorism", "protest", "riot", "unrest", "violence"],
    "positive_uplifting": ["achievement", "hope", "success", "inspire", "uplifting", "positive"],
    "natural_disasters": ["earthquake", "flood", "storm", "hurricane", "disaster", "wildfire"],
    "others": []  # Any content that doesn't fit the other categories will go here
}

# Function to classify article based on content
def classify_article_content(text):
    doc = nlp(text.lower())
    category_scores = {category: 0 for category in CATEGORIES}

    # Check for category keywords
    for token in doc:
        for category, keywords in CATEGORIES.items():
            if token.text in keywords:
                category_scores[category] += 1

    # Get the category with the highest score
    best_category = max(category_scores, key=category_scores.get)
    return best_category if category_scores[best_category] > 0 else "others"

# Function to process the article
def process_article(article):
    content = article['full_content']
    category = classify_article_content(content)

    # Update the article with the category
    article['category'] = category

    # Update the article in the database
    update_article_in_db(article)

# Function to update the article in the database with the new category
def update_article_in_db(article):
    try:
        conn = sqlite3.connect('news_articles.db')
        cursor = conn.cursor()

        # Update query to add category
        sql = ''' UPDATE articles
                  SET category = ?
                  WHERE link = ? '''
        cursor.execute(sql, (article['category'], article['link']))
        conn.commit()

        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
