from ultralytics import YOLO
import cv2
import requests
import base64
from picamera2 import Picamera2
import py_qmc5883l
import time
import sys


sensor = py_qmc5883l.QMC5883L()
sensor.calibration = [[1.0069612445723946, -0.026856596958531938, 2080.8507846050597], [-0.02685659695853194, 1.103613196274312, -674.0433673794105], [0.0, 0.0, 1.0]]
ncnn_model = YOLO('thermal_yolov8n_6_4_24_ncnn_model')
server_ip = '172.20.10.10'
picam2_1 = Picamera2(0)
picam2_2 = Picamera2(1)
config = picam2_1.create_preview_configuration()
picam2_1.configure(config)
picam2_1.start()
config = picam2_2.create_preview_configuration()
picam2_2.configure(config)
picam2_2.start()

def main():
    try:
        if len(sys.argv)-1 == 0:
            server_ip = input("Input server ip: ")
        else:
            server_ip = sys.argv[1]
        
        while True:
            time.sleep(1)
            facing_angle = sensor.get_bearing()
            facing_angle = facing_angle + 20 # offset
            print(facing_angle)
            f1 = picam2_1.capture_array()
            f2 = picam2_2.capture_array()
            f1 = cv2.rotate(f1, cv2.ROTATE_180)
            f2 = cv2.rotate(f2, cv2.ROTATE_180)
            f1 = cv2.cvtColor(f1, cv2.COLOR_BGRA2RGB)
            f2 = cv2.cvtColor(f2, cv2.COLOR_BGRA2RGB)


            results = ncnn_model.predict(f1, classes=[0])

            if results[0].boxes:

                # Convert results to JSON-friendly format
                results_json = results[0].tojson()

                # Convert frame to base64
                f1_base64 = convert_frame_to_base64(f1)
                f2_base64 = convert_frame_to_base64(f2)

                # Prepare data to send
                data = {
                    'results': results_json,
                    'frame_1': f1_base64,
                    'frame_2': f2_base64,
                    'facing_angle': facing_angle,
                    'detector_lat': 35.111481,
                    'detector_lon': -78.999123
                }

                url = f'http://{server_ip}:5000'
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, json=data, headers=headers)

                if response.status_code == 200:
                    print("Data sent successfully")
                else:
                    print(f"Failed to send data: {response.status_code}, {response.text}")
    except KeyboardInterrupt:
        print("Exiting Program")
        pass

def convert_frame_to_base64(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    return frame_base64

if __name__ == '__main__':
    main()