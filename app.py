from flask import Flask, render_template, request, jsonify, Response
import numpy as np
import json, os, io, qrcode

app = Flask(__name__)

# === SETUP DATABASE JSON ===
DATA_FILE = 'data/progress.json'
os.makedirs('data', exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# === HALAMAN UTAMA ===
@app.route('/')
def index():
    return render_template('index.html')

# === GRAFIK POLINOMIAL ===
@app.route("/graph", methods=["GET", "POST"])
def graph():
    if request.method == "POST":
        data = request.get_json()
        func = data["function"]

        # Buat rentang x
        x_values = np.linspace(-10, 10, 200)

        y_values = []
        for x in x_values:
            try:
                # tambahkan lingkungan aman agar x dan np dikenali
                y = eval(func, {"x": x, "np": np})
            except:
                y = None
            y_values.append(y)

        # Simpan progres
        with open(DATA_FILE, 'r+') as f:
            file_data = json.load(f)
            file_data.append({
                "type": "graph",
                "function": func,
                "x_min": -10,
                "x_max": 10,
                "description": "Visualisasi grafik fungsi polynomial"
            })
            f.seek(0)
            json.dump(file_data, f, indent=2)

        return jsonify({"x": x_values.tolist(), "y": y_values})

    return render_template("graph.html")

@app.route("/limit", methods=["GET", "POST"])
def limit():
    if request.method == "POST":
        data = request.get_json()
        func = data["function"]
        a = float(data["a"])

        # x untuk grafik
        x_values = np.linspace(a - 2, a + 2, 100)
        y_values = []

        # Hitung y untuk grafik
        for x in x_values:
            try:
                y = eval(func, {"x": x, "np": np})
            except:
                y = None
            y_values.append(y)

        # --- Hitung limit kiri & kanan ---
        h = 1e-7  # sangat kecil untuk pendekatan limit

        try:
            left = eval(func, {"x": a - h, "np": np})
        except:
            left = None

        try:
            right = eval(func, {"x": a + h, "np": np})
        except:
            right = None

        # --- Pembulatan agar nilai stabil (1 angka decimal) ---
        if left is not None:
            left_rounded = round(left, 1)
        else:
            left_rounded = None

        if right is not None:
            right_rounded = round(right, 1)
        else:
            right_rounded = None

        # --- Hitung limit dua sisi ---
        if left_rounded is not None and right_rounded is not None:
            limit_val = round((left_rounded + right_rounded) / 2, 1)
        else:
            limit_val = None

        # --- Simpan ke progress.json ---
        with open(DATA_FILE, 'r+') as f:
            file_data = json.load(f)
            file_data.append({
                "type": "limit",
                "function": func,
                "a": a,
                "left": left_rounded,
                "right": right_rounded,
                "limit_value": limit_val
            })
            f.seek(0)
            json.dump(file_data, f, indent=2)

        # --- Kirim ke frontend ---
        return jsonify({
            "x": x_values.tolist(),
            "y": y_values,
            "left": left_rounded,
            "right": right_rounded,
            "limit": limit_val
        })

    return render_template("limit.html")

@app.route("/derivative", methods=["GET", "POST"])
def derivative():
    if request.method == "POST":
        data = request.get_json()
        func = data["function"]

        # Jika user tidak mengisi a → default 0
        a = float(data["a"]) if data["a"] != "" else 0.0

        # Rentang grafik
        x_values = np.linspace(a - 5, a + 5, 200)

        # Hitung f(x)
        y_values = []
        for x in x_values:
            try:
                y = eval(func, {"x": x, "np": np})
            except:
                y = None
            y_values.append(y)

        # Hitung turunan numerik f'(x)
        h = 1e-5
        derivative_values = []
        for x in x_values:
            try:
                fp = (eval(func, {"x": x + h, "np": np}) -
                      eval(func, {"x": x - h, "np": np})) / (2*h)
            except:
                fp = None
            derivative_values.append(fp)

        # Turunan di titik a
        try:
            fp_a = (eval(func, {"x": a + h, "np": np}) -
                    eval(func, {"x": a - h, "np": np})) / (2*h)
            fx = eval(func, {"x": a, "np": np})
        except:
            fp_a = None
            fx = None

        # Garis singgung
        tangent = [fp_a * (x - a) + fx for x in x_values]

        return jsonify({
            "x": x_values.tolist(),
            "y": y_values,
            "dy": derivative_values,   # grafik turunan
            "tangent": tangent,
            "derivative_at_a": fp_a,
            "fx": fx
        })

    return render_template("derivative.html")

# === INTEGRAL ===
@app.route("/integral", methods=["GET", "POST"])
def integral():
    if request.method == "POST":
        data = request.get_json()
        func = data["function"]
        a = float(data["a"])
        b = float(data["b"])

        x_values = np.linspace(a, b, 200)
        y_values = []
        for x in x_values:
            try:
                y = eval(func)
            except:
                y = None
            y_values.append(y)

        area = np.trapz(y_values, x_values)

        # ✅ simpan hasil ke progress.json
        with open(DATA_FILE, 'r+') as f:
            file_data = json.load(f)
            file_data.append({
                "type": "integral",
                "function": func,
                "a": a,
                "b": b,
                "area": area
            })
            f.seek(0)
            json.dump(file_data, f, indent=2)

        return jsonify({"x": x_values.tolist(), "y": y_values, "area": area})
    return render_template("integral.html")

# === APLIKASI REAL-WORLD ===
@app.route("/application", methods=["GET", "POST"])
def application():
    if request.method == "POST":
        data = request.get_json()
        app_type = data["type"]
        params = data.get("params", {})

        # nilai default
        tmax = params.get("tmax", 10)
        x = np.linspace(0, tmax, 100).tolist()

        if app_type == "velocity":
            y = [t**2 for t in x]
            title = "Kecepatan Benda Bergerak"
            desc = "Grafik posisi s(t) = t². Kamu bisa ubah rentang waktu untuk melihat pergerakan benda."
            formula = "s(t) = t², v(t) = 2t"
            label = "Posisi s(t)"

        elif app_type == "growth":
            P0 = params.get("P0", 100)
            k = params.get("k", 0.3)
            y = [P0 * np.exp(k*t) for t in x]
            title = "Pertumbuhan Populasi"
            desc = "Perubahan populasi mengikuti model eksponensial."
            formula = f"P(t) = {P0}e^({k}t)"
            label = "Populasi P(t)"

        elif app_type == "area":
            a = params.get("a", 0)
            b = params.get("b", 10)
            x = np.linspace(a, b, 100).tolist()
            y = [t**2 for t in x]
            title = "Luas Area di Bawah Kurva"
            desc = f"Menunjukkan f(x) = x² dari x={a} ke x={b}."
            formula = "∫ x² dx = (1/3)x³ + C"
            label = "f(x) = x²"

        elif app_type == "cost":
            a = params.get("a", 1)
            b = params.get("b", -10)
            c = params.get("c", 30)
            y = [a*t**2 + b*t + c for t in x]
            title = "Biaya Minimum Produksi"
            desc = "Fungsi biaya kuadrat dengan koefisien yang dapat diubah."
            formula = f"C(x) = {a}x² + {b}x + {c}"
            label = "C(x)"

        elif app_type == "cooling":
            T0 = params.get("T0", 100)
            Tenv = params.get("Tenv", 30)
            k = params.get("k", 0.2)
            y = [Tenv + (T0 - Tenv)*np.exp(-k*t) for t in x]
            title = "Pendinginan Suhu (Hukum Newton)"
            desc = "Menunjukkan perubahan suhu benda terhadap waktu."
            formula = f"T(t) = {Tenv} + ({T0}-{Tenv})e^(-{k}t)"
            label = "T(t)"
        else:
            y, title, desc, formula, label = [], "Tidak diketahui", "", "", ""

        # ✅ Simpan hasil ke progress.json
        with open(DATA_FILE, 'r+') as f:
            file_data = json.load(f)
            file_data.append({
                "type": "application",
                "category": app_type,
                "description": desc,
                "formula": formula
            })
            f.seek(0)
            json.dump(file_data, f, indent=2)

        return jsonify({
            "x": x,
            "y": y,
            "title": title,
            "desc": desc,
            "formula": formula,
            "label": label
        })

    return render_template("application.html")


# === OPTIMIZATION ===
@app.route("/optimization", methods=["GET", "POST"])
def optimization():
    if request.method == "POST":
        data = request.get_json()
        func = data["function"]
        mode = data.get("mode", "all")  
        x_min = float(data.get("x_min", -10))
        x_max = float(data.get("x_max", 10))

        # GRID
        x_values = np.linspace(x_min, x_max, 600)

        # HITUNG f(x)
        y_values = []
        for x in x_values:
            try:
                y = eval(func, {"x": x, "np": np})
            except:
                y = None
            y_values.append(y)

        # HITUNG TURUNAN f'(x) secara numerik
        derivative_values = []
        h = 1e-5
        for x in x_values:
            try:
                fp = (eval(func, {"x": x + h, "np": np}) - eval(func, {"x": x - h, "np": np})) / (2*h)
            except:
                fp = None
            derivative_values.append(fp)

        y_arr = np.array(y_values)
        der_arr = np.array(derivative_values)

        # --- CARI TITIK KRITIS (f'(x) = 0) ---
        critical_points = []
        for i in range(1, len(der_arr)):
            if der_arr[i-1] * der_arr[i] < 0:  # pergantian tanda
                critical_points.append(float(x_values[i]))

        # --- MINIMUM & MAKSIMUM ---
        min_point = max_point = None

        if mode in ["all", "min", "extrema"]:
            try:
                idx = np.nanargmin(y_arr)
                min_point = {
                    "x": float(x_values[idx]),
                    "y": float(y_arr[idx])
                }
            except:
                pass

        if mode in ["all", "max", "extrema"]:
            try:
                idx = np.nanargmax(y_arr)
                max_point = {
                    "x": float(x_values[idx]),
                    "y": float(y_arr[idx])
                }
            except:
                pass

        # simpan history
        with open(DATA_FILE, 'r+') as f:
            file_data = json.load(f)
            file_data.append({
                "type": "optimization",
                "function": func,
                "mode": mode,
                "domain": [x_min, x_max],
                "minimum": min_point,
                "maximum": max_point,
                "critical_points": critical_points
            })
            f.seek(0)
            json.dump(file_data, f, indent=2)

        return jsonify({
            "x": x_values.tolist(),
            "y": y_values,
            "dy": derivative_values,
            "min": min_point,
            "max": max_point,
            "critical": critical_points
        })

    return render_template("optimization.html")


# === MULTIPLE FUNCTION (TAMPILAN SAJA) ===
@app.route("/multiple", methods=["GET", "POST"])
def multiple():
    if request.method == "POST":
        data = request.get_json()
        functions = data["functions"]
        x_min = float(data["x_min"])
        x_max = float(data["x_max"])

        x_values = np.linspace(x_min, x_max, 200).tolist()
        results = []

        for func in functions:
            y_vals = []
            for x in x_values:
                try:
                    y = eval(func, {"x": x, "np": np})
                except:
                    y = None
                y_vals.append(y)

            results.append({
                "function": func,
                "y": y_vals
            })

        # Simpan progres
        with open(DATA_FILE, 'r+') as f:
            file_data = json.load(f)
            file_data.append({
                "type": "multiple_plot",
                "functions": functions,
                "x_min": x_min,
                "x_max": x_max
            })
            f.seek(0)
            json.dump(file_data, f, indent=2)

        return jsonify({
            "x": x_values,
            "results": results
        })

    # GET → buka halaman multiple.html
    return render_template("multiple.html")

# === QUIZ ===
@app.route("/quiz")
def quiz():
    return render_template("quiz.html")

import random

@app.route("/quiz-data")
def quiz_data():
    quiz_file = "data/quiz.json"

    # --- Ambil soal dari file quiz.json ---
    with open(quiz_file, "r") as f:
        questions = json.load(f)

    # --- Acak urutan soal ---
    random.shuffle(questions)

    # --- Ambil sejumlah soal (misal 5 soal acak) ---
    selected = questions[:5]

    # --- Acak pilihan jawaban di setiap soal ---
    for q in selected:
        random.shuffle(q["options"])

    return jsonify(selected)

# === SIMPAN DATA MANUAL ===
@app.route('/save', methods=['POST'])
def save():
    progress = request.json
    with open(DATA_FILE, 'r+') as f:
        data = json.load(f)
        data.append(progress)
        f.seek(0)
        json.dump(data, f, indent=2)
    return jsonify({'status': 'saved'})

# === QRCODE IDENTITAS ===
@app.route("/qrcode.png")
def qrcode_png():
    qr_text = (
        "📘 *KALKULUS - Calculus Visualizer*\n\n"
        "👥 Anggota Kelompok:\n"
        "1. Ach. Jauhari Khalif (240210101038)\n"
        "2. Rafino Navisa Arvidiansa (240210101055)\n"
        "3. Irfina Eka Norlaili (240210101075)\n\n"
        "🏫 Pendidikan Matematika, FKIP, Universitas Jember\n"
        "🔗 Repository: https://github.com/username/Calculus_Visualizer"
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")

# === MENJALANKAN SERVER ===
if __name__ == '__main__':
    app.run(debug=True)
