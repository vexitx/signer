from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the e-signing backend!"

@app.route('/sign', methods=['POST'])
def sign_document():
    data = request.get_json()
    # Process the document signing here
    return jsonify({"message": "Document signed successfully!"})

if __name__ == '__main__':
    app.run(debug=True)