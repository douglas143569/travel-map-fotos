import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, request, redirect, url_for, send_from_directory, jsonify, render_template, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
METADATA_FILE = BASE_DIR / "photos.json"
USERS_FILE = BASE_DIR / "users.json"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao-por-algo-seguro")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

UPLOAD_FOLDER.mkdir(exist_ok=True)
if not METADATA_FILE.exists():
    METADATA_FILE.write_text("[]", encoding="utf-8")
if not USERS_FILE.exists():
    USERS_FILE.write_text("[]", encoding="utf-8")

# ---------------------------------------------------------------------------
# Flask-Login setup
# ---------------------------------------------------------------------------

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Faça login para acessar o mapa."
login_manager.login_message_category = "info"


class User(UserMixin):
    def __init__(self, data):
        self.id = data["id"]
        self.username = data["username"]
        self.email = data["email"]
        self.password_hash = data["password_hash"]


def load_users():
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_users(data):
    USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find_user_by_id(user_id):
    for u in load_users():
        if u["id"] == user_id:
            return User(u)
    return None


def find_user_by_username(username):
    for u in load_users():
        if u["username"].lower() == username.lower():
            return User(u)
    return None


def find_user_by_email(email):
    for u in load_users():
        if u["email"].lower() == email.lower():
            return User(u)
    return None


@login_manager.user_loader
def load_user(user_id):
    return find_user_by_id(user_id)


# ---------------------------------------------------------------------------
# Dados do app
# ---------------------------------------------------------------------------

STATES_CITIES = {
    "Acre": ["Rio Branco", "Cruzeiro do Sul", "Sena Madureira"],
    "Alagoas": ["Maceió", "Arapiraca", "Palmeira dos Índios"],
    "Amapá": ["Macapá", "Santana", "Laranjal do Jari"],
    "Amazonas": ["Manaus", "Parintins", "Itacoatiara"],
    "Bahia": ["Salvador", "Feira de Santana", "Vitória da Conquista"],
    "Ceará": ["Fortaleza", "Caucaia", "Juazeiro do Norte"],
    "Distrito Federal": ["Brasília"],
    "Espírito Santo": ["Vitória", "Vila Velha", "Serra"],
    "Goiás": ["Goiânia", "Anápolis", "Rio Verde"],
    "Maranhão": ["São Luís", "Imperatriz", "Caxias"],
    "Mato Grosso": ["Cuiabá", "Várzea Grande", "Rondonópolis"],
    "Mato Grosso do Sul": ["Campo Grande", "Dourados", "Três Lagoas"],
    "Minas Gerais": ["Belo Horizonte", "Uberlândia", "Juiz de Fora"],
    "Pará": ["Belém", "Ananindeua", "Santarém"],
    "Paraíba": ["João Pessoa", "Campina Grande", "Cabedelo"],
    "Paraná": ["Curitiba", "Londrina", "Maringá"],
    "Pernambuco": ["Recife", "Olinda", "Caruaru"],
    "Piauí": ["Teresina", "Parnaíba", "Picos"],
    "Rio de Janeiro": ["Rio de Janeiro", "Niterói", "Duque de Caxias"],
    "Rio Grande do Norte": ["Natal", "Mossoró", "Parnamirim"],
    "Rio Grande do Sul": ["Porto Alegre", "Caxias do Sul", "Santa Maria"],
    "Rondônia": ["Porto Velho", "Ji-Paraná", "Ariquemes"],
    "Roraima": ["Boa Vista", "Rorainópolis", "Caracaraí"],
    "Santa Catarina": ["Florianópolis", "Joinville", "Blumenau"],
    "São Paulo": ["São Paulo", "Campinas", "Santos"],
    "Sergipe": ["Aracaju", "Nossa Senhora do Socorro", "Lagarto"],
    "Tocantins": ["Palmas", "Araguaína", "Gurupi"],
}

MAP_POINTS = [
    {"state": "São Paulo", "lat": -23.5505, "lng": -46.6333},
    {"state": "Rio de Janeiro", "lat": -22.9068, "lng": -43.1729},
    {"state": "Minas Gerais", "lat": -19.9167, "lng": -43.9345},
    {"state": "Bahia", "lat": -12.9714, "lng": -38.5014},
    {"state": "Paraná", "lat": -25.4284, "lng": -49.2733},
]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_photos():
    try:
        return json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_photos(data):
    METADATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Rotas de autenticação
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = find_user_by_username(username)
        if not user or not check_password_hash(user.password_hash, password):
            flash("Usuário ou senha incorretos.", "error")
            return render_template("login.html")

        login_user(user, remember=request.form.get("remember") == "on")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("index"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Preencha todos os campos.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "error")
            return render_template("register.html")

        if password != confirm:
            flash("As senhas não coincidem.", "error")
            return render_template("register.html")

        if find_user_by_username(username):
            flash("Nome de usuário já está em uso.", "error")
            return render_template("register.html")

        if find_user_by_email(email):
            flash("E-mail já cadastrado.", "error")
            return render_template("register.html")

        users = load_users()
        users.append({
            "id": str(uuid.uuid4()),
            "username": username,
            "email": email,
            "password_hash": generate_password_hash(password),
        })
        save_users(users)

        flash("Conta criada com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da conta.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Rotas principais (protegidas)
# ---------------------------------------------------------------------------

@app.route("/")
@login_required
def index():
    return render_template("index.html", states_cities=STATES_CITIES, map_points=MAP_POINTS)


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    photo = request.files.get("photo")
    state = request.form.get("state")
    date = request.form.get("date")
    caption = request.form.get("caption", "")

    if not photo or not allowed_file(photo.filename):
        return jsonify({"success": False, "message": "Arquivo inválido. Envie PNG, JPG, JPEG ou GIF."}), 400

    if not state or not date:
        return jsonify({"success": False, "message": "Informe estado e data."}), 400

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{photo.filename.replace(' ', '_')}"
    filepath = UPLOAD_FOLDER / filename
    photo.save(filepath)

    photos = load_photos()
    photos.append({
        "filename": filename,
        "state": state,
        "date": date,
        "caption": caption,
        "user": current_user.username,
    })
    save_photos(photos)

    return jsonify({"success": True, "photo": photos[-1]})


@app.route("/photos")
@login_required
def photos():
    return jsonify(load_photos())


@app.route("/uploads/<path:filename>")
@login_required
def uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True)
