import requests
from utils import img_decode
import cv2

server_ip = '172.20.10.10'

def main():
    try:
        while True:
                # fetch data
                print("Fetching Data")
                response = requests.get(f'http://{server_ip}:5000/depth_vid')

                if response.status_code == 200:
                    data = response.json()
                    img = img_decode(data[0])
                    print(data[1])
                    cv2.imshow('depth feed', img)
                    if (cv2.waitKey(30) == 27):  # ESC key to break loop
                        break

    except KeyboardInterrupt:
        cv2.destroyAllWindows
        print("Keyboard Interrupt")

if __name__ == '__main__':
    main()