import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import os
import google.generativeai as genai

# --- Main Application Class ---
class BitByBitChatbot(tk.Tk):
    BG_COLOR = "#E8EAFE"
    TEXT_COLOR_LIGHT = "#ffffff"
    TEXT_COLOR_DARK = "#000000"
    AI_BUBBLE_COLOR = "#F2F2F7"
    USER_BUBBLE_COLOR = "#A18BFF"
    HEADER_COLOR = "#A18BFF"
    INPUT_BG = "#ffffff"

    def __init__(self, initial_prompt=None):
        super().__init__()

        # <<< FIX: This line forces the window to be always on top.
        self.attributes('-topmost', True)

        self.title("Bit by Bit - AI Assistant")
        self.geometry("450x800")
        self.configure(bg=self.BG_COLOR)

        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.chat_session = None

        self.create_widgets()

        if not self.api_key:
            self.set_input_state("disabled")
            self.add_ai_message("API Key not found. Please set the GEMINI_API_KEY environment variable.")
        else:
            self.initialize_ai_model()
            if initial_prompt:
                self.add_ai_message("I see you're working on a challenge! How can I help with this?")
                threading.Thread(target=self.get_ai_response, args=(initial_prompt,), daemon=True).start()
            else:
                self.add_ai_message("Hi! I'm your AI assistant. How can I help you?")

    def create_widgets(self):
        header = tk.Frame(self, bg=self.HEADER_COLOR, height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        close_btn = tk.Label(header, text="X", bg=self.HEADER_COLOR, fg="white", font=("Arial", 12, "bold"), cursor="hand2")
        close_btn.pack(side=tk.RIGHT, padx=10)
        close_btn.bind("<Button-1>", lambda e: self.destroy())
        title = tk.Label(header, text="AI ASSISTANT", bg=self.HEADER_COLOR, fg="white", font=("Arial", 14, "bold"))
        title.pack(pady=10)

        avatar_frame = tk.Frame(self, bg=self.BG_COLOR)
        avatar_frame.pack(pady=20)
        try:
            self.avatar_img = tk.PhotoImage(file="avatar.png")
            tk.Label(avatar_frame, image=self.avatar_img, bg=self.BG_COLOR).pack()
        except tk.TclError:
            tk.Label(avatar_frame, text="🤖", font=("Arial", 50), bg=self.BG_COLOR).pack()

        self.chat_window = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, bg=self.BG_COLOR, fg=self.TEXT_COLOR_DARK, font=("Inter", 11),
            borderwidth=0, highlightthickness=0
        )
        self.chat_window.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_window.config(state='disabled')

        self.chat_window.tag_configure("user_bubble", background=self.USER_BUBBLE_COLOR, foreground=self.TEXT_COLOR_LIGHT,
                                       relief='raised', borderwidth=2, lmargin1=100, lmargin2=100,
                                       rmargin=10, spacing3=15, wrap='word', font=("Inter", 11))
        self.chat_window.tag_configure("ai_bubble", background=self.AI_BUBBLE_COLOR, foreground=self.TEXT_COLOR_DARK,
                                       relief='raised', borderwidth=2, lmargin1=10, lmargin2=10,
                                       rmargin=100, spacing3=15, wrap='word', font=("Inter", 11))

        input_frame = tk.Frame(self, bg=self.BG_COLOR)
        input_frame.pack(fill=tk.X, pady=10)
        self.input_field = ttk.Entry(input_frame, font=("Arial", 12), cursor="xterm")
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.input_field.bind("<Return>", self.process_input_event)
        self.input_field.focus_set()
        send_button = tk.Label(input_frame, text="▶", font=("Arial", 14), bg=self.BG_COLOR, cursor="hand2")
        send_button.pack(side=tk.RIGHT, padx=10)
        send_button.bind("<Button-1>", self.process_input_event)

    def initialize_ai_model(self):
        try:
            genai.configure(api_key=self.api_key)
            self.chat_session = genai.GenerativeModel("gemini-1.5-flash").start_chat(history=[])
        except Exception as e:
            self.add_ai_message(f"Could not initialize AI model: {e}")
            self.set_input_state("disabled")

    def process_input_event(self, event=None):
        user_input = self.input_field.get().strip()
        if user_input:
            self.input_field.delete(0, tk.END)
            self.add_user_message(user_input)
            self.set_input_state("disabled")
            threading.Thread(target=self.get_ai_response, args=(user_input,), daemon=True).start()

    def get_ai_response(self, prompt):
        try:
            response = self.chat_session.send_message(prompt)
            self.add_ai_message(response.text)
        except Exception as e:
            self.add_ai_message(f"Error: {e}")
        finally:
            self.set_input_state("normal")

    def add_user_message(self, message):
        self._add_message(f"\n{message}\n", "user_bubble")

    def add_ai_message(self, message):
        self._add_message(f"\n{message}\n", "ai_bubble")

    def _add_message(self, message, tag):
        self.chat_window.config(state='normal')
        self.chat_window.insert(tk.END, message, tag)
        self.chat_window.config(state='disabled')
        self.chat_window.yview(tk.END)

    def set_input_state(self, state):
        self.input_field.config(state=state)

def run_chatbot_app(initial_prompt=None):
    app = BitByBitChatbot(initial_prompt=initial_prompt)
    app.mainloop()

if __name__ == "__main__":
    run_chatbot_app("I need help with Python variables.")