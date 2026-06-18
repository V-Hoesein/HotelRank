import os
import json
import glob
from flask import Flask, render_template
from .saw_algorithm import rank_hotels_with_saw

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
        
        # Apply SAW Algorithm for ranking
        ranked_hotels = rank_hotels_with_saw(hotels)

        return render_template('index.html', hotels=ranked_hotels)

    return app
