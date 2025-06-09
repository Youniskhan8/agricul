import os
import pickle
import pandas as pd
import numpy as np
from datetime import timedelta, datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# === Flask setup ===
app = Flask(__name__)
CORS(app)
app.secret_key = "9796399435youniskhan"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db = SQLAlchemy(app)

# === Database Models ===
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100))
    occupation = db.Column(db.String(100))
    gender = db.Column(db.String(10))  # Optional
    phone = db.Column(db.String(15))   # Optional

class Sales(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    commodity = db.Column(db.String(100), nullable=False)
    variety = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    market = db.Column(db.String(100), nullable=False)
    price_date = db.Column(db.Date, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# === Load ML Model and Dataset ===
if os.path.exists("model.pkl"):
    with open("model.pkl", "rb") as model_file:
        model = pickle.load(model_file)
else:
    model = None

with open("label_encoders.pkl", "rb") as le_file:
    le_dict = pickle.load(le_file)

df = pd.read_csv("final_merged_dataset (1).csv", parse_dates=["Price Date"], dayfirst=True)

dropdown_values = {
    "commodities": sorted(df["Commodity"].dropna().unique()),
    "varieties": sorted(df["Variety"].dropna().unique()),
    "grades": sorted(df["Grade"].dropna().unique()),
    "districts": sorted(df["District Name"].dropna().unique()),
    "markets": sorted(df["Market Name"].dropna().unique())
}

# === Routes ===
@app.route("/")
def status():
    # return "Commodity Price Prediction API is running!"
    return redirect(url_for("home_page"))

@app.route("/home", endpoint="home_page")
def home():
    return render_template("home1.html")

# due to this route , graph is not uploading
@app.route("/api/commodities")
def get_commodities():
    return jsonify(sorted(df["Commodity"].dropna().unique().tolist()))


@app.route("/analysis")
def analysis():
    return render_template("analysis1.html", dropdowns=dropdown_values)

@app.route("/get_options", methods=["POST"])
def get_options():
    data = request.get_json()
    option_type = data.get("type")
    value = data.get("value")

    if option_type == "commodity":
        filtered_df = df[df["Commodity"] == value]
        varieties = sorted(filtered_df["Variety"].dropna().unique().tolist())
        return jsonify({"options": varieties})

    elif option_type == "variety":
        # Get both commodity and variety from the request
        commodity = data.get("commodity")
        variety = value

        # Filter using both commodity and variety
        filtered_df = df[(df["Commodity"] == commodity) & (df["Variety"] == variety)]
        grades = sorted(filtered_df["Grade"].dropna().unique().tolist())
        return jsonify({"options": grades})

    elif option_type == "district":
        filtered_df = df[df["District Name"] == value]
        markets = sorted(filtered_df["Market Name"].dropna().unique().tolist())
        return jsonify({"options": markets})

    return jsonify({"options":[]})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    required_fields = ["Commodity", "Variety", "Grade", "District Name", "Market Name", "Price Date", "Temperature"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    try:
        data_encoded = data.copy()
        for col in ["Commodity", "Variety", "Grade", "District Name", "Market Name"]:
            data_encoded[col] = le_dict[col].transform([data[col]])[0]

        date = pd.to_datetime(data["Price Date"])
        data_encoded["year"] = date.year
        data_encoded["month"] = date.month

        model_input = np.array([[data_encoded[col] for col in [
            "District Name", "Market Name", "Commodity", "Variety", "Grade", "year", "month", "Temperature"]]]) #sklearn expect input as 2d array

        prediction = model.predict(model_input)[0]
        return jsonify({"Predicted Modal Price": prediction})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/past_prices", methods=["GET"])
def get_past_prices():
    commodity = request.args.get("commodity")
    if not commodity:
        return jsonify({"error": "Please provide a commodity parameter."}), 400

    # Use the latest date from the dataset as 'today'
    latest_date = df["Price Date"].max()
    two_months_ago = latest_date - timedelta(days=60)

    filtered = df[(df["Commodity"].str.lower() == commodity.lower()) & (df["Price Date"] >= two_months_ago)]

    if filtered.empty:
        return jsonify({"message": "No data found for the given commodity."}), 404

    filtered = filtered.sort_values("Price Date")
    response = {
        "dates": filtered["Price Date"].dt.strftime('%Y-%m-%d').tolist(),
        "prices": filtered["Modal Price (Rs./Quintal)"].tolist()
    }
    return jsonify(response)

# === Auth Routes ===
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("home_page"))
        flash("Invalid email or password.")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        city = request.form["city"]
        occupation = request.form["occupation"]

        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
            return redirect(url_for("login"))

        new_user = User(full_name=full_name, email=email, password=password, city=city, occupation=occupation)
        db.session.add(new_user)
        db.session.commit()

        # Optional: set session to log them in automatically
        session["user_id"] = new_user.id  # if you're using session-based login

        flash("Account created successfully.")
        return redirect(url_for("home_page"))  # Redirect to home page after signup

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("home_page"))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.occupation = request.form.get('occupation')
        user.gender = request.form.get('gender')
        user.phone = request.form.get('phone')
        db.session.commit()
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

# === Sales Route ===
@app.route('/sales', methods=['GET', 'POST'])
def sales():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        new_sale = Sales(
            user_id=user_id,
            commodity=request.form['commodity'],
            variety=request.form['variety'],
            grade=request.form['grade'],
            district=request.form['district'],
            market=request.form['market'],
            price_date=datetime.strptime(request.form['price_date'], '%Y-%m-%d'),
            price=float(request.form['price'])
        )
        db.session.add(new_sale)
        db.session.commit()
        return redirect(url_for('sales'))

    user_sales = Sales.query.filter_by(user_id=user_id).order_by(Sales.timestamp.desc()).all()
    return render_template('sales.html', sales=user_sales)




# === Run App ===
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
