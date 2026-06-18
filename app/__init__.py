import os
import json
import glob
from flask import Flask, render_template

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        # Get path to the analyzed data
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        analyzed_dir = os.path.join(base_dir, 'data', 'analyzed')
        
        hotels = []
        
        # Read all JSON files in the analyzed directory
        if os.path.exists(analyzed_dir):
            file_paths = glob.glob(os.path.join(analyzed_dir, '*.json'))
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        hotels.append(data)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        
        # Sort hotels by averageSentimentScore in descending order
        hotels.sort(key=lambda x: x.get('averageSentimentScore', 0), reverse=True)
        
        # Add rank based on index
        for index, hotel in enumerate(hotels):
            hotel['rank'] = index + 1

        return render_template('index.html', hotels=hotels)

    return app
