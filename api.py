from flask import Flask, jsonify, request

app = Flask(__name__)

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime

uri = "mongodb+srv://EaterOfWorlds:HL6WvxdYVp6vxgFj@clustersensor.oruf8.mongodb.net/?retryWrites=true&w=majority&appName=ClusterSensor"
client = MongoClient(uri)
db = client['MyDatabase'] 
my_collections = db['SensorData']

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

@app.route('/sensor', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.json  # Ambil data dari ESP32
        data["timestamp"] = datetime.datetime.utcnow()  
        
        my_collections.insert_one(data)
        
        return jsonify({"message": "Data berhasil disimpan", "status": "success"}), 200
    except Exception as e:
        return jsonify({"message": str(e), "status": "error"}), 500
    

@app.route('/sensors', methods=['GET'])
def get_sensor_data():
    try:
        data = list(my_collections.find({}, {"_id": 0}))  
        return jsonify({"message": "Data berhasil didapatkan", "status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"message": str(e), "status": "error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)