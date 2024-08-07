import cv2
from hitnet import HitNet, ModelType, draw_disparity
import numpy as np
import time

# DnD stands for Direction and Distance

# Camera module V2s focal length
# focal_length = 4.74 mm
focal_length = 1963.72 # pixels
# Current setup distance between camera module v2s
baseline = 25 / 1000 # meters
# No compass module for now so assume always facing 0 degrees North
# facing_angle = 0
# Camera Module v2s horizontal focal length
fov = 66
# load disparity model
model_path = "models/eth3d.pb"
model_type = ModelType.eth3d
hitnet_depth = HitNet(model_path, model_type)

def main():
    detect_personnel()

def detect_personnel(results, frame_1, frame_2, facing_angle = 0):

    # Get object disparity:
    disparity_map, disparity_img = disparity_calculation(frame_1, frame_2)

    # Convert disparity to depth
    depths, times = depth_from_disparity(disparity_map, results)

    # Get object directions:
    object_angles = angle_calculation(facing_angle, fov, results)

    # Get compass directions:
    compass_directions = compass_direction_32_point(object_angles)

    # Add compass directions and object angles to the plot
    img_ann = dir_ann(frame_1, compass_directions, object_angles, depths, results)

    # Concat annotated image with disparity image
    img_ann = np.concatenate((img_ann, disparity_img), axis=1)

    data = {'Compass Directions': compass_directions, 'Degrees from North': object_angles, 'Depths (m)': depths, 'Times': times}

    return data, img_ann
    

def angle_calculation(facing_angle, fov, results):
    angles = []

    for i in range(len(results)):
        # Calculate the center of the bounding box
        center_x = (results[i]['box']['x1'] + results[i]['box']['x2']) / 2

        # Calculate the angle of the object from the center of the camera
        angle = ((center_x) * fov / 640) - fov / 2
        if angle < 0:
            angle = 360 + angle

        # Calculate the direction of the object from the facing angle of the camera
        angle = facing_angle + angle
        if angle > 360:
            angle = angle - 360
        
        angle = round(angle, 2)
        angles.append(angle)

        # Print the direction of the object
        # print(f"Object {i} has a center at {center_x}")
        # print(f"Object {i} is at {angle} degrees")

    return angles

def compass_direction_32_point(object_angles):
    directions = []

    # 32 point compass
    compass = {0: 'N', 11.25: 'NbE', 22.5: 'NNE', 33.75: 'NEbN', 45: 'NE', 56.25: 'NEbe', 67.5: 'ENE', 78.75: 'EbN', 90: 'E',
               101.25: 'EbS', 112.5: 'ESE', 123.75: 'SEbE', 135: 'SE', 146.25: 'SEbS', 157.5: 'SSE', 168.75: 'SbE', 180: 'S',
               191.25: 'SbW', 202.5: 'SSW', 213.75: 'SWbS', 225: 'SW', 236.25: 'SWbW', 247.5: 'WSW', 258.75: 'WbS', 270: 'W',
               281.25: 'WbN', 292.5: 'WNW', 303.75: 'NWbW', 315: 'NW', 326.25: 'NWbN', 337.5: 'NNW', 348.75: 'NbW', 360: 'N'}
    
    # Find the closest compass direction
    for angle in object_angles:
        # round angle to nearest 11.25 degrees
        angle = round(angle / 11.25) * 11.25
        directions.append(compass[angle])

    return directions


def top_left_points(results):
    top_lefts = []

    for i in range(len(results)):
        top_left = results[i]['box']['x1'], results[i]['box']['y1']
        top_lefts.append(top_left)

    return top_lefts

def dir_ann(img, directions, angles, depths, results):

    top_lefts = [(round(results[i]['box']['x1']), round(results[i]['box']['y1'])) for i in range(len(results))]
    bottom_rights = [(round(results[i]['box']['x2']), round(results[i]['box']['y2'])) for i in range(len(results))]

    for i in range(len(directions)):
        text = (f"{directions[i]}, {angles[i]} degrees, {depths[i]} m")
        org = tuple(map(round, top_lefts[i]))
        img = cv2.rectangle(img, (org[0], org[1]-20), (org[0]+10*len(text), org[1]), (0, 0, 0), -1)
        img = cv2.rectangle(img, top_lefts[i], bottom_rights[i], (0, 255, 0), 2)
        org = org[0], org[1]-5
        img = cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    return img

def disparity_calculation(im1, im2):

    # show images
    # cv2.imshow('Stereo Images', im2)
    # cv2.waitKey(0)

    # Calculate disparity
    disparity = hitnet_depth(im1, im2)

    # Draw disparity
    disparity_img = draw_disparity(disparity)
    # cv2.imshow('Disparity', disparity_img)

    return disparity, disparity_img

def depth_from_disparity(disparity_map, results):
    depths = []
    times = []
    t = time.time()
    
    for i in range(len(results)):
        # Calculate the center of the bounding box
        center_x = (results[i]['box']['x1'] + results[i]['box']['x2']) / 2
        center_y = (results[i]['box']['y1'] + results[i]['box']['y2']) / 2
        coord = (round(center_x), round(center_y))
        disparity = disparity_map[coord[1]][coord[0]]

        # Calculate depth (in m)
        depth = focal_length * baseline / disparity
        depth = round(depth.item(), 2)
        print(f"Object {i} has a depth of {depth} m")
        depths.append(depth)

        times.append(t)

    return depths, times

if __name__ == '__main__':
    main()
