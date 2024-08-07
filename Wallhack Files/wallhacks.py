import requests
import AR_render
import time
import cv2
from utils import img_decode

server_ip = '127.0.0.1'
# img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)

def main():
    cap = cv2.VideoCapture(0)
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
                ret, frame = cap.read()
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                facing_angle = 0

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
        cap.release()
        cv2.destroyAllWindows
        print("Keyboard Interrupt")

if __name__ == '__main__':
    main()