import requests
import AR_render
import time
import cv2
from utils import img_decode
from picamera2 import Picamera2
import py_qmc5883l

server_ip = '192.168.204.94'
# img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
sensor = py_qmc5883l.QMC5883L()
sensor.calibration = [[1.0069612445723946, -0.026856596958531938, 2080.8507846050597], [-0.02685659695853194, 1.103613196274312, -674.0433673794105], [0.0, 0.0, 1.0]]
sensor.declination = -90 # offset

def main():
    cam = Picamera2(0)
    config = cam.create_preview_configuration()
    cam.configure(config)
    cam.start()
    
    try:
        while True:
            # fetch data
            print("Fetching Data")
            response = requests.get(f'http://{server_ip}:5000')
            check = False
            if response.status_code == 200:
                data = response.json()
                if not data == []:
                    detection_data = data[0]
                    object_distance = detection_data['Depths (m)']
                    object_angle = detection_data['Degrees from North']
                    object_time = detection_data['Times']
                    detector_lat = data[1]
                    detector_lon = data[2]
                    results = data[3]
                    img = img_decode(data[4])
                    check = True
                
            else:
                print('Failed to fetch data')

            # initialize times
            current_time = time.time()
            next_time = current_time + 5

            while current_time < next_time:
                frame = cam.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                facing_angle = sensor.get_bearing()

                # print(object_distance)
                img = cv2.imread('red.png', cv2.IMREAD_UNCHANGED)
                
                if check:
                    frame = AR_render.render(frame, detector_lat, detector_lon, object_distance, object_angle, img, results, object_time, facing_angle=facing_angle)
                # time.sleep(0.1)
                current_time = time.time()

                
                img = cv2.putText(frame, "Facing: " + str(round(facing_angle)), (15, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

                cv2.imshow('Wallhacks', frame)
                if (cv2.waitKey(30) == 27):  # ESC key to break loop
                    break
                

    except KeyboardInterrupt:
        cam.stop()
        cv2.destroyAllWindows
        print("Keyboard Interrupt")

if __name__ == '__main__':
    main()
