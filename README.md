# ❤️ Heart Disease Chatbot

## 📌 Description

This project is an AI-powered Heart Disease Chatbot that helps users get information about heart-related conditions such as symptoms, prevention, diet, medications, and lifestyle.

The chatbot uses a Large Language Model (LLM) via Groq API and also includes a built-in knowledge base for fallback responses.

---

## 🚀 Features

* 👤 User Authentication (Signup & Login)
* 💬 AI Chatbot using Groq API (LLaMA model)
* 📚 Built-in knowledge base for heart health
* 🕘 Chat history storage using SQLite
* 🔐 Secure API key handling using `.env`

---

## 🛠️ Technologies Used

* Python (Flask)
* HTML, CSS, JavaScript
* SQLite Database
* Groq API (LLaMA 3.3 70B)
* dotenv for environment variables

---

## 📂 Project Structure

* `app.py` → Backend (Flask API)
* `index.html` → Main chatbot UI
* `login.html` → Login page
* `signup.html` → Signup page
* `users.db` → Database (local use only)
* `.env` → API key (not uploaded to GitHub)

---

## ▶️ How to Run

1. Clone the repository:

   ```
   git clone https://github.com/your-username/heart-disease-chatbot.git
   ```

2. Navigate to project folder:

   ```
   cd heart-disease-chatbot
   ```

3. Install dependencies:

   ```
   pip install flask flask-cors bcrypt python-dotenv groq
   ```

4. Create a `.env` file:

   ```
   GROQ_API_KEY=your_api_key_here
   ```

5. Run the application:

   ```
   python app.py
   ```

6. Open in browser:

   ```
   http://127.0.0.1:5000/
   ```

---

## 🔐 Security

* API keys are stored using environment variables
* `.env` file is excluded from GitHub using `.gitignore`

---

## 📌 Future Improvements

* Voice-based chatbot (speech-to-speech)
* Better UI/UX design
* Deployment on cloud (AWS/Render)
* Integration with real medical datasets

---

## 👩‍💻 Author

Kavya
