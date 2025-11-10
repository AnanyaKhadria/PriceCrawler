from flask import Flask, jsonify
import subprocess

app = Flask(__name__)


@app.route('/')
def home():
    return "Flask API is running!"


# Endpoint to trigger cashify scraping
@app.route('/scrape/cashify', methods=['GET'])
def scrape_cashify():
    try:
        result = subprocess.run(["python", "cashifymultiprocessing.py"], capture_output=True, text=True)
        return jsonify({"status": "success", "output": result.stdout, "error": result.stderr})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Endpoint to trigger cashmen scraping
@app.route('/scrape/cashmen', methods=['GET'])
def scrape_cashmen():
    try:
        result = subprocess.run(["python", "cashmenmultiprocessing.py"], capture_output=True, text=True)
        return jsonify({"status": "success", "output": result.stdout, "error": result.stderr})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Endpoint to trigger quickmobile scraping
@app.route('/scrape/quickmobile', methods=['GET'])
def scrape_quickmobile():
   try:
        result = subprocess.run(["python", "quickmobilemultiprocessing.py"], capture_output=True, text=True)
        return jsonify({"status": "success", "output": result.stdout, "error": result.stderr})
   except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Endpoint to trigger instacash scraping
@app.route('/scrape/instacash', methods=['GET'])
def scrape_instacash():
    try:
        result = subprocess.run(["python", "instacashmultiprocessing.py"], capture_output=True, text=True)
        return jsonify({"status": "success", "output": result.stdout, "error": result.stderr})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
