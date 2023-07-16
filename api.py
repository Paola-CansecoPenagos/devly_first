from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from pdf_generator import generar_pdf
from calculator import statistical_calculator
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS, cross_origin

app = Flask(__name__)
app.config["MONGO_URI"] = 'mongodb://localhost:27017/Devly'
app.config["SECRET_KEY"] = 'oP1pHP_wI4GLcmBG7Kv-RoL020Fxjsl25Pi6e9HYEjg'
mongo = PyMongo(app)

CORS(app)


@app.route("/login", methods=["POST"])
@cross_origin(origin="http://localhost:3000", headers=["Content-Type"])
def login():
    username = request.json.get("username")
    password = request.json.get("password")

    # Buscar al usuario en la base de datos MongoDB
    user = mongo.db.users.find_one({"username": username})

    if user and check_password_hash(user["password"], password):
        # Generar el token JWT
        token = jwt.encode({"username": username}, app.config["SECRET_KEY"], algorithm="HS256")
        return jsonify({"token": token})

    return jsonify({"message": "Credenciales inválidas"}), 401


@app.route("/register", methods=["POST", "OPTIONS"])
@cross_origin(origin="http://localhost:3000", headers=["Content-Type"])
def register():
    email = request.json.get("email")
    username = request.json.get("username")
    password = request.json.get("password")

    # Verificar si el email ya existe en la base de datos
    existing_email = mongo.db.users.find_one({"email": email})
    if existing_email:
        return jsonify({"message": "Este email ya esta registrado"}), 400

    # Verificar si el usuario ya existe en la base de datos
    existing_user = mongo.db.users.find_one({"username": username})
    if existing_user:
        return jsonify({"message": "Pruebe un nuevo nombre de usuario, este ya esta registrado"}), 400

    # Generar un hash de la contraseña
    password_hash = generate_password_hash(password)

    # Crear un nuevo usuario en la base de datos
    new_user = {"email": email, "username": username, "password": password_hash}
    mongo.db.users.insert_one(new_user)

    return jsonify({"message": "Se registro exitosamente el usuario"}), 201


@app.route("/api/calcular", methods=["GET"])
def obtener_documentos():
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"message": "Token faltante"}), 401

    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        username = payload["username"]
        documentos = mongo.db.Datos.find()

        # Listas para almacenar los datos de los sensores
        campoTemperatura_output = []  # Temperatura
        campoHumedad_output = []  # Humedad
        campoLDR_output = []  # LDR
        campoTDS_output = []  # TDS
        campoPH_output = []  # pH
        campoDS18B20_output = []  # DS18B20

        for documento in documentos:
            campoTemperatura_output.append(documento["Temperatura"])
            campoHumedad_output.append(documento["Humedad"])
            campoLDR_output.append(documento["LDR"])
            campoTDS_output.append(documento["TDS"])
            campoPH_output.append(documento["pH"])
            campoDS18B20_output.append(documento["DS18B20"])

        # Realizar cálculos y generación de PDF para cada sensor
        resultados_campoTemperatura = statistical_calculator(campoTemperatura_output)
        resultados_campoHumedad = statistical_calculator(campoHumedad_output)
        resultados_campoLDR = statistical_calculator(campoLDR_output)
        resultados_campoTDS = statistical_calculator(campoTDS_output)
        resultados_campoPH = statistical_calculator(campoPH_output)
        resultados_campoDS18B20 = statistical_calculator(campoDS18B20_output)

        # Generar PDF para cada sensor
        generar_pdf(resultados_campoTemperatura, "Reporte_Temperatura.pdf")
        generar_pdf(resultados_campoHumedad, "Reporte_Humedad.pdf")
        generar_pdf(resultados_campoLDR, "Reporte_LDR.pdf")
        generar_pdf(resultados_campoTDS, "Reporte_TDS.pdf")
        generar_pdf(resultados_campoPH, "Reporte_PH.pdf")
        generar_pdf(resultados_campoDS18B20, "Reporte_DS18B20.pdf")

        return jsonify({
            "Humedad": campoHumedad_output,
            "Temperatura": campoTemperatura_output,
            "LDR": campoLDR_output,
            "TDS": campoTDS_output,
            "pH": campoPH_output,
            "DS18B20": campoDS18B20_output
        })

    except jwt.InvalidTokenError:
        return jsonify({"message": "Token inválido"}), 401


@app.route("/api/documentos/<id>", methods=["DELETE"])
def eliminar_documento(id):
    documento = mongo.db.Datos.find_one({"_id": id})
    if documento:
        mongo.db.Datos.delete_one({"_id": id})
        return jsonify({"mensaje": "Documento eliminado correctamente"})
    else:
        return jsonify({"mensaje": "Documento no encontrado"})


if __name__ == "__main__":
    app.run()
