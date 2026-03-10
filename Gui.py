import tkinter as tk
from tkinter import scrolledtext
import webbrowser

from sympy.codegen.fnodes import product_

import timber2 as bot
import os
import threading
import pyttsx3
from PIL import Image, ImageTk
import io
import requests
from PIL import Image, ImageTk
import requests
from io import BytesIO
from timber2 import selenium_search

# Paths

project_root = os.path.dirname(os.path.abspath(__file__))
# Load data
datastore = bot.load_json(os.path.join(project_root, "datastore.json"))
movies_data = bot.load_json(os.path.join(project_root, "movies.json")).get("movies", [])

# Initialize logging file path
log_file_path = os.path.join(project_root, "chat_log.txt")

# Setup TTS engine (reuse from Timber2)
tts_engine = pyttsx3.init()
voices = tts_engine.getProperty('voices')
tts_engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
tts_engine.setProperty('rate', 150)

# Setup Speech Recognizer


# Globals
voice_enabled = True
voice_listening = False

# --- Custom Themed Input Dialog ---
class CustomInputDialog(tk.Toplevel):
    def __init__(self, parent, title="Input", prompt="Please enter:"):
        super().__init__(parent)
        self.title(title)
        self.configure(bg="#2A1651")
        self.geometry("350x130")
        self.resizable(False, False)
        self.grab_set()  # Modal

        self.result = None

        label = tk.Label(self, text=prompt, bg="#2A1651", fg="white", font=("Segoe UI", 11))
        label.pack(pady=(15, 10), padx=10)

        self.entry = tk.Entry(self, font=("Segoe UI", 12), bg="#342D59", fg="white", insertbackground="white",
                              relief=tk.FLAT)
        self.entry.pack(fill=tk.X, padx=20, ipady=6)
        self.entry.focus()

        btn_frame = tk.Frame(self, bg="#2A1651")
        btn_frame.pack(pady=15)

        btn_ok = tk.Button(btn_frame, text="OK", width=10, bg="#00FFA3", fg="#1C1446",
                           font=("Segoe UI", 11, "bold"), relief=tk.FLAT, command=self.on_ok)
        btn_ok.pack(side=tk.LEFT, padx=10)

        btn_cancel = tk.Button(btn_frame, text="Cancel", width=10, bg="#FF5F5F", fg="white",
                               font=("Segoe UI", 11, "bold"), relief=tk.FLAT, command=self.on_cancel)
        btn_cancel.pack(side=tk.LEFT)

        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.on_cancel())

    def on_ok(self):
        self.result = self.entry.get().strip()
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

def custom_askstring(title, prompt):
    dlg = CustomInputDialog(root, title, prompt)
    root.wait_window(dlg)
    return dlg.result

# --- Custom Themed Message Dialog --
class CustomMessageDialog(tk.Toplevel):
    def __init__(self, parent, title="Message", message="", is_error=False):
        super().__init__(parent)
        self.title(title)
        self.configure(bg="#2A1651")
        self.geometry("350x130")
        self.resizable(False, False)
        self.grab_set()  # Modal

        fg_color = "#FF5F5F" if is_error else "white"

        label = tk.Label(self, text=message, bg="#2A1651", fg=fg_color, font=("Segoe UI", 12))
        label.pack(pady=(30, 20), padx=15)

        btn_ok = tk.Button(self, text="OK", width=10, bg="#00FFA3", fg="#1C1446",
                           font=("Segoe UI", 11, "bold"), relief=tk.FLAT, command=self.destroy)
        btn_ok.pack()

        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())

def custom_showinfo(title, message):
    dlg = CustomMessageDialog(root, title, message, is_error=False)
    root.wait_window(dlg)

def custom_showerror(title, message):
    dlg = CustomMessageDialog(root, title, message, is_error=True)
    root.wait_window(dlg)

# --- Main Window Setup ---
root = tk.Tk()
root.title("Timber Chatbot v2 - Ultimate")
root.geometry("900x650")
root.configure(bg="#2A1651")  # Dark purple background

# Frames
top_frame = tk.Frame(root, bg="#3D2C71", height=60)
top_frame.pack(fill=tk.X)

side_frame = tk.Frame(root, bg="#2A1651", width=180)
side_frame.pack(side=tk.LEFT, fill=tk.Y)

chat_frame = tk.Frame(root, bg="#1C1446")
chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Top frame content (welcome)
welcome_label = tk.Label(top_frame, text="Welcome to Timber Chatbot v2 - Ask me anything!", fg="white", bg="#3D2C71",
                         font=("Segoe UI", 14, "bold"))
welcome_label.pack(pady=10)

# Chat display
chat_window = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, font=("Segoe UI", 11),
                                        bg="#342D59", fg="white", insertbackground="white",
                                        relief=tk.FLAT)
chat_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
chat_window.tag_config("user", foreground="#FFD966")
chat_window.tag_config("bot", foreground="#00FFA3")
chat_window.tag_config("link", foreground="#4AD9D9", underline=True)

# Entry frame
entry_frame = tk.Frame(chat_frame, bg="#1C1446")
entry_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

entry = tk.Entry(entry_frame, font=("Segoe UI", 12), bg="#2E2753", fg="white", insertbackground="white",
                 relief=tk.FLAT)
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=6)

send_btn = tk.Button(entry_frame, text="Send", bg="#00FFA3", fg="#1C1446", font=("Segoe UI", 11, "bold"),
                     relief=tk.FLAT)
send_btn.pack(side=tk.LEFT)

# Side panel commands list
commands_label = tk.Label(side_frame, text="Commands List", bg="#2A1651", fg="white", font=("Segoe UI", 12, "bold"))
commands_label.pack(pady=10)

commands_text = tk.Text(side_frame, bg="#342D59", fg="white", font=("Segoe UI", 10), relief=tk.FLAT, height=25, width=22)
commands_text.pack(padx=10)
commands_text.insert(tk.END,
"""\

- Suggest movie
- Drama movies
- Action movies
- Best movie
- Compare movie1 movie2
- Roll dice mn 1 ly 6
- Flip coin malk w ketaba
- Calculate 
- Rock paper scissors
- Translate 
- Reaction game
- Fun fact 
- Convert units
- News
- Links
-Api search
-selenium
- Quit
""")
commands_text.config(state=tk.DISABLED)

# Clear chat button
def clear_chat():
    chat_window.config(state=tk.NORMAL)
    chat_window.delete("1.0", tk.END)
    chat_window.config(state=tk.DISABLED)

clear_btn = tk.Button(side_frame, text="Clear Chat", bg="#FF5F5F", fg="white", font=("Segoe UI", 11, "bold"),
                      relief=tk.FLAT, command=clear_chat)
clear_btn.pack(pady=10)

# Voice toggle button


# Log chat function
def log_chat(user_text, bot_text):
    try:
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(f"User: {user_text}\nBot: {bot_text}\n{'-'*40}\n")
    except Exception as e:
        print(f"Logging error: {e}")

# Insert message in chat window
def insert_message(text, sender="bot", clickable_links=None):
    chat_window.config(state=tk.NORMAL)
    tag = "user" if sender == "user" else "bot"
    chat_window.insert(tk.END, f"{sender.capitalize()}: ", tag)
    if clickable_links:
        # clickable_links = list of (text, url)
        for text_part, url in clickable_links:
            link_tag = f"link{url}"
            chat_window.insert(tk.END, text_part + "\n", link_tag)
            chat_window.tag_config(link_tag, foreground="#4AD9D9", underline=True)
            chat_window.tag_bind(link_tag, "<Button-1>", lambda e, link=url: webbrowser.open(link))
    else:
        chat_window.insert(tk.END, text + "\n")
    chat_window.config(state=tk.DISABLED)
    chat_window.yview(tk.END)




# Voice speaking wrapper (non-blocking)
def speak_async(text):
    if voice_enabled:
        threading.Thread(target=bot.speak, args=(text,), daemon=True).start()

# Main handler
def handle_input(event=None):
    user_text = entry.get().strip()
    if not user_text:
        return
    insert_message(user_text, sender="user")
    entry.delete(0, tk.END)

    # Get bot response
    response = get_response(user_text)
    if isinstance(response, list):
        insert_message("", sender="Timber", clickable_links=response)
        speak_async("Here are some links for you.")
    else:
        insert_message(response, sender="bot")
        speak_async(response)

    # Log conversation
    log_chat(user_text, response)




def insert_image_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        img = Image.open(BytesIO(response.content))
        img = img.resize((300, 200))  # Resize to fit chat
        img_tk = ImageTk.PhotoImage(img)

        chat_window.image_create(tk.END, image=img_tk)
        chat_window.image = img_tk  # Prevent garbage collection
        chat_window.insert(tk.END, "\n")
        chat_window.yview(tk.END)
    except Exception as e:
        insert_message(f"Failed to load image: {e}", sender="bot")



def get_response(user_input):
    inp = user_input.lower()

    if inp == "quit":
        custom_showinfo("Goodbye", "See you next time!")
        root.quit()
        return "Goodbye!"
    elif "suggest" in inp and "movie" in inp:
        return bot.suggest_movies(movies_data)
    elif "drama" in inp:
        return bot.suggest_movies(movies_data, genre="drama")
    elif "action" in inp:
        return bot.suggest_movies(movies_data, genre="action")
    elif "best" in inp or "top" in inp:
        return bot.best_movie(movies_data)
    elif "compare" in inp:
        found = [m for m in movies_data if m["Title"].lower() in inp]
        if len(found) >= 2:
            return bot.compare_movies(found[0], found[1])
        else:
            return "Please mention two movie titles to compare."
    elif "dice" in inp:
        return bot.roll_dice()
    elif any(op in inp for op in ['+', '-', '*', '/', '%']):
        mode = custom_askstring("Calculation mode", "float or ceil?")
        return bot.calc_expr(user_input, mode)
    elif "coin" in inp:
        return bot.flip_coin()
    elif "rock" in inp and "paper" in inp:
        choice = custom_askstring("Game", "rock, paper, or scissors?")
        return bot.rock_paper(choice)
    elif "translate" in inp:
        txt = custom_askstring("Translate", "Enter text:")
        lang = custom_askstring("Language", "To language (e.g. en, fr):")
        return bot.translate_text(txt, lang)
    elif "reaction" in inp:
        return bot.reaction_game()
    elif "fact" in inp:
        return bot.fun_fact()
    elif "convert" in inp:
        val = custom_askstring("Convert units", "Enter value:")
        from_u = custom_askstring("From unit", "From unit:")
        to_u = custom_askstring("To unit", "To unit:")
        return bot.convert_units(val, from_u, to_u)
 #Data acq projecttttttttt

    elif "news" in inp.lower():
        return bot.get_latest_news_all()

    elif "net" in inp or "network" in inp:

        num = custom_askstring("Network", "Enter number of nodes:")

        names = custom_askstring("Network", "Enter node names (comma-separated):")
        edges = custom_askstring("Network", "Enter edges like (A,B),(B,C):")

        if not (num and names and edges):
            return "Missing input."

        return bot.net(num, names, edges)

    elif "links" in inp:
        return [
            (" BBC Arabic", "https://www.bbc.com/arabic"),
            (" Reuters", "https://www.reuters.com"),
            (" BBC RSS Feed", "http://feeds.bbci.co.uk/news/rss.xml")
            ]

    elif "aliexpress" in inp:
        query = custom_askstring("AliExpress Search", "What product are you looking for?")
        if query:
            return bot.get_latest_products_from_aliexpress(query)
        return "No query provided."

    elif "sel" in inp or "google" in inp:
        query = custom_askstring("Google Search", "Enter your search query:")
        if not query:

            return "No query provided."
        sel =  bot.selenium_search(query)
        if isinstance(sel, list):
                return[( title, link)for title, link in sel]
        return sel

    elif "heat" in inp:
        query = custom_askstring("Selenium Search", "Enter your search query:")
        if query:
            from timber2 import selenium  # import here to avoid circular import
            try:
                result = selenium(query)
                if isinstance(result, list):
                    return "\n".join([f" {title}\n {link}" for title, link in result])
                else:
                    return result
            except Exception as e:
                return f" Error: {str(e)}"
        return " No query provided."



    elif "search" in inp or "google" in inp:
        query = custom_askstring("Search", "What do you want to search?")
        if not query:
            return "No query provided."

        result = bot.google_search_api(query)

        if isinstance(result, list):
            return [( title, link) for title, link in result]

        return result  # If it's a string (like "Search error" or "No results"), return it as is

        sample_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Artificial_Intelligence_logo.svg/600px-Artificial_Intelligence_logo.svg.png"
        insert_image(sample_image_url)
        speak_async("Here are the top results.")
        return ""  # Don’t repeat text
    elif "show ai image" in inp:
        img_url = "https://upload.wikimedia.org/wikipedia/commons/6/69/Artificial_Intelligence_%26_AI_%26_Machine_Learning_-_30212411048.jpg"
        insert_message("Here is an AI image:", sender="bot")
        insert_image_from_url(img_url)
        return "Here's what I found!"

    #Fallback Q&A
    all_q = [q["question"] for q in datastore.get("questions", [])] + [m["Title"] for m in movies_data]
    best = bot.find_best_match(user_input, all_q)

    if best:
        ans = bot.get_answer(best, datastore) or bot.get_answer_for_movie(best, movies_data)
        return ans or "I found something but no answer is available."
    else:
        # Ask user to provide answer for new questions
        new = custom_askstring("New question", "I don't know this one. Please provide the answer:")
        if new:  # ← THIS WAS WRONGLY INDENTED
            datastore["questions"].append({"question": user_input, "answer": new})
            bot.save_json(os.path.join(project_root, "datastore.json"), datastore)
            custom_showinfo("Thanks!", "I've learned something new.")
            return "Thanks! I've learned something new."
        return "Sorry, I don't have an answer for that."  # ← THIS TOO



# Bind Enter key to send message
entry.bind("<Return>", handle_input)
send_btn.config(command=handle_input)

# Auto-start voice recognition every 10 seconds (passive mode)
def show_graph_popup(pil_image, title="Graph Visualization"):
    popup = tk.Toplevel(root)
    popup.title(title)
    popup.geometry("600x450")
    popup.configure(bg="#1C1446")
    popup.grab_set()

    img = ImageTk.PhotoImage(pil_image)
    img_label = tk.Label(popup, image=img, bg="#1C1446")
    img_label.image = img  # Prevent GC
    img_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    close_btn = tk.Button(popup, text="Close", command=popup.destroy, bg="#FF5F5F", fg="white",
                          font=("Segoe UI", 11, "bold"), relief=tk.FLAT)
    close_btn.pack(pady=10)



root.mainloop()