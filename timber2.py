import json
import random
import math
import requests
from difflib import get_close_matches
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import pint
import feedparser
import sympy
import pyttsx3
import os
import threading

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


ureg = pint.UnitRegistry()

# Initialize text-to-speech engine once here
tts_engine = pyttsx3.init()
voices = tts_engine.getProperty('voices')
# Default voice index (change as you want)
tts_engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
tts_engine.setProperty('rate', 150)

def speak(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

# Load & Save JSON safely
def load_json(file_path):
    try:


        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"questions": []}  # default empty structure


def save_json(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving JSON: {e}")

datastore = load_json("datastore.json")
movies = load_json("movies.json")




# Find best matching question from known questions
def find_best_match(user_question, questions):
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_answer(question, datastore):
    for q in datastore.get('questions', []):
        if q['question'].lower() == question.lower():
            return q['answer']
    return None

# Movie info features
def get_answer_for_movie(question, movies):
    for movie in movies:
        if movie['Title'].lower() == question.lower():
            return f"{movie['Title']} ({movie['Year']}) - {movie['Genre']} - Directed by {movie['Director']}"
    return None

def suggest_movies(movies, genre=None, number=3):
    filtered = [m for m in movies if genre.lower() in m['Genre'].lower()] if genre else movies
    filtered = sorted(filtered, key=lambda m: float(m.get('imdbRating', 0)), reverse=True)
    sample = random.sample(filtered, min(number, len(filtered)))
    return '\n'.join(f"- {m['Title']} (Rating: {m.get('imdbRating', 'N/A')})" for m in sample)

def best_movie(movies):
    best = max(movies, key=lambda m: float(m.get('imdbRating', 0)))
    return f"Best movie: {best['Title']} ({best['Year']}) - Rating: {best['imdbRating']}"

def compare_movies(movie1, movie2):
    r1, r2 = float(movie1.get('imdbRating', 0)), float(movie2.get('imdbRating', 0))
    if r1 > r2:
        return f"{movie1['Title']} is better ({r1})"
    elif r2 > r1:
        return f"{movie2['Title']} is better ({r2})"
    return f"Both are equal ({r1})"

# Mini games
def roll_dice():
    return f"You rolled a {random.randint(1, 6)}"

def flip_coin():
    return f"Result: {random.choice(['king', 'ketaba'])}"

def calc_expr(expr, mode):
    try:
        parsed_expr = sympy.sympify(expr)
        result = float(parsed_expr.evalf())
        return f"Result: {math.ceil(result) if mode == 'ceil' else result}"
    except Exception as e:
        return f"Error in calculation: {e}"

def rock_paper(user):
    choices = ['rock', 'paper', 'scissors']
    if user not in choices:
        return "Invalid choice."
    bot_choice = random.choice(choices)
    if user == bot_choice:
        return f"Both chose {bot_choice}. It's a tie!"
    wins = (user == 'rock' and bot_choice == 'scissors') or (user == 'paper' and bot_choice == 'rock') or (user == 'scissors' and bot_choice == 'paper')
    return f"Bot: {bot_choice}. {'You win!' if wins else 'You lose!'}"

def translate_text(text, lang):
    try:
        return GoogleTranslator(source='auto', target=lang).translate(text)
    except Exception as e:
        return f"Translation error: {e}"

def reaction_game():
    time.sleep(random.randint(2, 5))
    start = time.time()
    input("Press Enter NOW! ")
    reaction = time.time() - start
    return f"Reaction time: {reaction:.2f} seconds"

def fun_fact():
    facts = [
        "Honey never spoils.",
        "Octopuses have 3 hearts.",
        "Bananas are berries.",
        "Strawberries aren't berries."
    ]
    return random.choice(facts)

def convert_units(value, from_unit, to_unit):
    try:
        result = (float(value) * ureg(from_unit)).to(to_unit)
        return f"{value} {from_unit} = {result.magnitude:.2f} {to_unit}"
    except Exception as e:
        return f"Conversion error: {e}"
#DATA ACQ PROJECT
# scraping :)
def scrape_bbc_arabic(limit=5):
    r = requests.get("https://www.bbc.com/arabic")
    soup = BeautifulSoup(r.content, "html.parser")
    headlines = soup.find_all("h3")[:limit]
    return [h.get_text(strip=True) for h in headlines]

def scrape_reuters(limit=5):
    r = requests.get("https://www.reuters.com/")
    soup = BeautifulSoup(r.content, "html.parser")
    heads = soup.select("h2, h3")[:limit]
    return [h.get_text(strip=True) for h in heads]

def parse_rss_news(rss_url, limit=5):
    feed = feedparser.parse(rss_url)
    return [entry.title for entry in feed.entries[:limit]]

def get_latest_news_all(limit=25):
    try:
        bbc = scrape_bbc_arabic(limit)
        reuters = scrape_reuters(limit)
        rss = parse_rss_news("http://feeds.bbci.co.uk/news/rss.xml", limit)
        combined = list(dict.fromkeys(bbc + reuters + rss))
        return "Latest News:\n" + "\n".join([f"- {title}" for title in combined[:limit]])
    except Exception as e:
        return f"News fetch error: {e}"
def get_latest_products_from_aliexpress(query="", limit=10):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        url = f"https://www.aliexpress.com/wholesale?SearchText={query.replace(' ', '+')}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        # AliExpress is very dynamic, we try to find product titles and links
        product_tags = soup.select("a._3t7zg._2f4Ho")  # May need to update based on current structure

        products = []
        for tag in product_tags[:limit]:
            title = tag.get("title", "No Title")
            link = "https:" + tag.get("href", "#")
            products.append((title, link))

        if not products:
            return "⚠️ No products found. AliExpress may have changed the structure or blocked the request."

        return [(title, link) for title, link in products]

    except Exception as e:
        return f"AliExpress fetch error: {e}"




def log_search(query, file_path="search_stats.log"):
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"api: {query.strip().lower()}\n")
    except Exception as e:
        print(f"Logging error: {e}")


def google_search_api(query):
    log_search(query)

    API_KEY = "66eb55ebb8f0e9b575977e83a0b0822c0c461c5bcc9d212f2a32bbd164a8e81e"
    url = f"https://serpapi.com/search.json?q={query}&api_key={API_KEY}"
    try:
        r = requests.get(url)
        results = r.json().get("organic_results", [])
        if not results:
            return "No results found."

        return [(res.get("title", "No Title"), res.get("link", "#")) for res in results[:5]]
    except Exception as e:
        return f"Search error: {e}"



from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.keys import Keys
import numpy as np
import math
import matplotlib.pyplot as plt



def selenium_search(query):
    try:
        # Setup Chrome options
        options = Options()
        # options.add_argument("--headless")  # eftkr enk  Disable this to show browser
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation flags
        options.add_argument("--disable-gpu")  # Optional on Windows (avoids bugs in headless mode)
        options.add_experimental_option('prefs', {
            "profile.default_content_setting_values.notifications": 2,  # 2 = Block notifications
            "profile.default_content_setting_values.cookies": 2,  # 2 = Block cookies (can help skip cookie banners)
            "profile.default_content_setting_values.popups": 2,  # 2 = Block popups (like "subscribe" modals)
            "credentials_enable_service": False,  # Disable Chrome credential service
            "profile.password_manager_enabled": False  # Disable password manager popup
        })
        service = Service(r"C:\Users\Omar\Downloads\chromedriver-win64 (2)\chromedriver-win64\chromedriver.exe")
        driver = webdriver.Chrome(service=service, options=options)

        driver.get("https://www.google.com/")
        time.sleep(3)

        # Search
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.submit()
        time.sleep(5)

        # Scroll and Get Results
        last = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(3)
            new = driver.execute_script("return document.body.scrollHeight")
            if new == last:
                break
            last = new

        results = driver.find_elements(By.CSS_SELECTOR, 'div.tF2Cxc')[:5]
        output = []
        X, Y = [], []

        for i, result in enumerate(results, 1):
            try:
                title = result.find_element(By.TAG_NAME, 'h3').text
                link = result.find_element(By.TAG_NAME, 'a').get_attribute('href')
                output.append((title, link))

                # Convert title into coordinates:
                title_length = len(title)
                word_count = len(title.split())
                X.append(title_length)
                Y.append(word_count)

            except Exception as e:
                output.append((f"{i}. Error parsing result", str(e)))

        driver.quit()



        return output if output else "No search results found."

    except Exception as e:
        return f"Selenium Error: {e}"

import networkx as nx


def net(num_nodes, node_names_str, edges_str):
    try:
        num_nodes = int(num_nodes)
    except ValueError:
        return "Invalid number of nodes."

    nodes = [n.strip() for n in node_names_str.split(",")]
    if len(nodes) != num_nodes:
        return f"Expected {num_nodes} nodes but got {len(nodes)}."

    # Parse and clean edges
    edges_input = edges_str.replace("(", "").replace(")", "").split(",")
    raw_edges = [(edges_input[i].strip(), edges_input[i+1].strip()) for i in range(0, len(edges_input)-1, 2)]

    valid_edges = set()
    invalid_edges = []

    for n1, n2 in raw_edges:
        if n1 in nodes and n2 in nodes:
            edge = tuple(sorted((n1, n2)))
            valid_edges.add(edge)
        else:
            invalid_edges.append((n1, n2))

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(valid_edges)

    # Draw graph
    plt.figure(figsize=(6, 4))
    nx.draw_networkx(G, with_labels=True, node_color='lightblue')
    plt.title("Graph Visualization")
    plt.tight_layout()
    plt.show()

    output = ""

    for i, node in enumerate(G.nodes):
        d = G.degree[node]
        output += f'Node: {node} >>> Degree: {d}\n'

    a = nx.betweenness_centrality(G, normalized=False)
    output += f"Non-normalized Betweenness Centrality: {a}\n"

    x = nx.betweenness_centrality(G)
    values = list(x.values())
    output += f"Normalized Betweenness Values: {values}\n"

    if values:
        mx = max(values)
        output += f"Max Betweenness Centrality: {mx}\n"
        i = values.index(mx)
        output += f"Node with Max Betweenness: {list(G.nodes)[i]}\n"
    else:
        output += "No centrality data available.\n"

    result = f"Nodes: {list(G.nodes)}\nEdges: {list(G.edges)}"
    if invalid_edges:
        result += "\nInvalid edges skipped: " + ", ".join([f"({a},{b})" for a, b in invalid_edges])

    return output + "\n" + result




def kde_distance_based(d, R):
    if d <= R:
        return (1 - (d / R) ** 2) ** 2
    else:
        return 0

# Heatmap Plot Function
def plot_kde_heatmap(X, Y, R=4, search_label="Search Result"):
    x_vals = np.linspace(0, 100, 100)
    y_vals = np.linspace(0, 30, 100)
    heatmap = np.zeros((len(y_vals), len(x_vals)))

    for i, x in enumerate(x_vals):
        for j, y in enumerate(y_vals):
            total_density = 0
            for xi, yi in zip(X, Y):
                d = math.sqrt((x - xi) ** 2 + (y - yi) ** 2)
                total_density += kde_distance_based(d, R)
            heatmap[j, i] = total_density

    plt.figure(figsize=(12, 8))
    plt.imshow(heatmap, extent=(0, 100, 0, 30), origin="lower", cmap="hot", interpolation="nearest")
    plt.colorbar(label="Density")
    plt.scatter(X, Y, color="blue", label="Results", edgecolors="black")
    plt.title("Search Result Density Heatmap")
    plt.xlabel(f"X Axis - {search_label}")
    plt.ylabel(f"Y Axis - {search_label}")
    plt.legend()
    plt.show()



def selenium(query):
    try:
        # Setup Chrome options
        options = Options()
        # options.add_argument("--headless")  # eftkr enk  Disable this to show browser
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation flags
        options.add_argument("--disable-gpu")  # Optional on Windows (avoids bugs in headless mode)
        options.add_experimental_option('prefs', {
            "profile.default_content_setting_values.notifications": 2,  # 2 = Block notifications
            "profile.default_content_setting_values.cookies": 2,  # 2 = Block cookies (can help skip cookie banners)
            "profile.default_content_setting_values.popups": 2,  # 2 = Block popups (like "subscribe" modals)
            "credentials_enable_service": False,  # Disable Chrome credential service
            "profile.password_manager_enabled": False
        })
        service = Service(r"C:\Users\Omar\Downloads\chromedriver-win64 (2)\chromedriver-win64")
        driver = webdriver.Chrome(service=service, options=options)

        driver.get("https://www.google.com/")
        time.sleep(3)

        # Search
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.submit()
        time.sleep(5)

        # Scroll and Get Results
        last = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(3)
            new = driver.execute_script("return document.body.scrollHeight")
            if new == last:
                break
            last = new

        results = driver.find_elements(By.CSS_SELECTOR, 'div.tF2Cxc')[:5]
        output = []
        X, Y = [], []

        for i, result in enumerate(results, 1):
            try:
                title = result.find_element(By.TAG_NAME, 'h3').text
                link = result.find_element(By.TAG_NAME, 'a').get_attribute('href')
                output.append((title, link))

                # Convert title into coordinates:
                title_length = len(title)
                word_count = len(title.split())
                X.append(title_length)
                Y.append(word_count)
            except Exception as e:
                output.append((f"{i}. Error parsing result", str(e)))
        driver.quit()
        if X and Y:
            plot_kde_heatmap(X, Y)
        return output if output else "No search results found."
    except Exception as e:
        return f"Selenium Error: {e}"




