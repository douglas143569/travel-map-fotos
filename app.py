import json
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, request, redirect, url_for, send_from_directory, jsonify, render_template

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
METADATA_FILE = BASE_DIR / "photos.json"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

UPLOAD_FOLDER.mkdir(exist_ok=True)
if not METADATA_FILE.exists():
    METADATA_FILE.write_text("[]", encoding="utf-8")

# Lista completa de estados (UF) e algumas cidades de exemplo para o dropdown.
# Observação: cidades são apenas sugestões; o usuário pode selecionar e enviar qualquer uma.
STATES_CITIES = {
    # Para manter o MVP leve, aqui estão cidades-base (capitais + outras cidades).
    # Observação: incluir "todas as cidades" do Brasil (5.000+) exige uma base externa.
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



# Pontos iniciais para o mapa (continua com alguns pontos de demo).
# Se quiser, posso adicionar um ponto para cada estado (com capital) também.
MAP_POINTS = [
    {"state": "São Paulo", "city": "São Paulo", "lat": -23.5505, "lng": -46.6333},
    {"state": "Rio de Janeiro", "city": "Rio de Janeiro", "lat": -22.9068, "lng": -43.1729},
    {"state": "Minas Gerais", "city": "Belo Horizonte", "lat": -19.9167, "lng": -43.9345},
    {"state": "Bahia", "city": "Salvador", "lat": -12.9714, "lng": -38.5014},
    {"state": "Paraná", "city": "Curitiba", "lat": -25.4284, "lng": -49.2733},
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


@app.route("/")
def index():
    return render_template("index.html", states_cities=STATES_CITIES, map_points=MAP_POINTS)


@app.route("/upload", methods=["POST"])
def upload():
    photo = request.files.get("photo")
    state = request.form.get("state")
    city = request.form.get("city")
    date = request.form.get("date")
    caption = request.form.get("caption", "")

    if not photo or not allowed_file(photo.filename):
        return jsonify({"success": False, "message": "Arquivo inválido. Envie PNG, JPG, JPEG ou GIF."}), 400

    if not state or not city or not date:
        return jsonify({"success": False, "message": "Informe estado, cidade e data."}), 400

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{photo.filename.replace(' ', '_')}"
    filepath = UPLOAD_FOLDER / filename
    photo.save(filepath)

    photos = load_photos()
    photos.append({
        "filename": filename,
        "state": state,
        "city": city,
        "date": date,
        "caption": caption,
    })
    save_photos(photos)

    return jsonify({"success": True, "photo": photos[-1]})


@app.route("/photos")
def photos():
    return jsonify(load_photos())


@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True)
