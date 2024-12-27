import json
from flask import Flask, jsonify, render_template, request, redirect, url_for, g, session
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3

app = Flask(__name__)

DATABASE = 'database.db'
SECRET_KEY = 'your_secret_key'
app.config['SECRET_KEY'] = SECRET_KEY
app.config['DATABASE'] = DATABASE

nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    doc = nlp(text.lower())
    keywords = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]
    return ' '.join(keywords)

def find_most_similar_question(user_question, data):
    questions = list(data.keys())
    processed_questions = [extract_keywords(question) for question in questions]
    processed_user_question = extract_keywords(user_question)

    vectorizer = TfidfVectorizer().fit_transform(processed_questions + [processed_user_question])
    vectors = vectorizer.toarray()

    cosine_similarities = cosine_similarity(vectors[-1:], vectors[:-1])
    most_similar_index = cosine_similarities.argmax()

    return questions[most_similar_index]

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        cur = db.cursor()
        cur.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = cur.fetchone()
        
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return redirect(url_for('register', username=username, password=password))
    
    return render_template('login.html', error=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            db.commit()
            session['username'] = username
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Username already exists')
    
    username = request.args.get('username', '')
    password = request.args.get('password', '')
    return render_template('register.html', username=username, password=password, error=None)

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/get_bot_response", methods=["POST"])
def get_bot_response():
    message = request.json["message"].lower() 
    with open("data2.json", "r") as f:
        data = json.load(f)
    
    most_similar_question = find_most_similar_question(message, data)
    response = data.get(most_similar_question, "I'm sorry, I don't understand.")
    
    if response == "I'm sorry, I don't understand.":
        keywords = extract_keywords(message)
        suggestions = []
        for key in data.keys():
            if any(keyword in key.lower() for keyword in keywords.split()):  # Convert key to lowercase
                suggestions.append(key)
                
        if len(suggestions) > 0:
            buttons = []
            for suggestion in suggestions:
                buttons.append({
                    "title": suggestion,
                    "payload": suggestion
                })
                
            response = {
                "text": "Suggestions:-",
                "quick_replies": buttons
            }
    
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)
