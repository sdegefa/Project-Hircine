import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, render_template, jsonify
import Detect
import json
from utils import ll_to_cart, cart_to_ll, get_obj_coords, img_decode, img_toHTML, convert_frame_to_base64
import cv2
from Flask_Server_Code.pytak_interface import main
from asyncio import run
import time

app = Flask(__name__)

data_store = {
    'obj_data': {'Compass Directions': ['NW', 'NW', 'NW'], 'Degrees from North': [270, 260, 280], 'Depths (m)': [20, 20, 20], 'Times': [time.time()-30, time.time()-100, time.time()]},
    'img': convert_frame_to_base64(cv2.imread('Wallhack Files/red.png')),
    'detector_lat': 35.111481,
    'detector_lon': -78.99123,
    'depth_feed': cv2.imread('output.png'),
    'results':  [
                {
                    "name": "person",
                    "class": 0,
                    "confidence": 0.82462,
                    "box": {
                    "x1": 164.15746,
                    "y1": 208.79135,
                    "x2": 573.1994,
                    "y2": 477.65894
                    }
                },
                {
                    "name": "person",
                    "class": 0,
                    "confidence": 0.82462,
                    "box": {
                    "x1": 164.15746,
                    "y1": 208.79135,
                    "x2": 573.1994,
                    "y2": 477.65894
                    }
                },
                {
                    "name": "person",
                    "class": 0,
                    "confidence": 0.82462,
                    "box": {
                    "x1": 164.15746,
                    "y1": 208.79135,
                    "x2": 573.1994,
                    "y2": 477.65894
                    }
                }
                ]

}

render_store = {}

detect_counter = 0

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':
        req_data = request.get_json()
        results = json.loads(req_data['results'])
        # print(results)
        frame_1 = img_decode(req_data['frame_1'])
        frame_2 = img_decode(req_data['frame_2'])
        facing_angle = req_data['facing_angle']

        # Process the data using your Detect module
        data, frame = Detect.detect_personnel(results, frame_1, frame_2, facing_angle)

        # store essential data
        data_store['obj_data'] = data
        data_store['img'] = req_data['frame_1']
        data_store['detector_lat'] = req_data['detector_lat']
        data_store['detector_lon'] = req_data['detector_lon']
        data_store['depth_feed'] = frame
        data_store['results'] = results

        
        # Render the template with the data and image
        return jsonify({'status':'success'})
    else:
        if render_store == {}:
            return jsonify([])
        else:
            return jsonify(render_store['obj_data'], render_store['detector_lat'], render_store['detector_lon'], render_store['results'], render_store['img'])

@app.route('/depth_feed', methods=['GET'])
def depth_feed():
    data_html = data_store['obj_data']
    image_data = img_toHTML(data_store['depth_feed'])
    return render_template('index.html', data_html=data_html, image_data=image_data)

@app.route('/depth_vid', methods=['GET'])
def depth_video():
    return jsonify(convert_frame_to_base64(data_store['depth_feed']), data_store['obj_data'])

@app.route('/lat_lon', methods=['GET'])
def lat_lon():
    global render_store

    if render_store == {}:
        render_store = data_store.copy()
    else:
        for rs_key in render_store['obj_data'].keys():
            render_store['obj_data'][rs_key] += data_store['obj_data'][rs_key]
        render_store["results"] += data_store["results"]

    pi_coords = ll_to_cart(data_store['detector_lat'], data_store['detector_lon'])
    lats = []
    lons = []
    if data_store['obj_data']:
        coords = get_obj_coords(pi_coords, data_store['obj_data']['Depths (m)'], data_store['obj_data']['Degrees from North'])
        lats, lons = cart_to_ll(coords)
    else: 
        depths = [3, 4, 5]
        angles = [90, 110, 130]
        coords = get_obj_coords(pi_coords, depths, angles)
        lats, lons = cart_to_ll(coords)
    # print(lat, lon)
    # for idx, lat in enumerate(lats):
    #     run(main(latitude=lat, longitude=lons[idx], marker_name=f"test_{idx}"))

    return jsonify(lats, lons) 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)