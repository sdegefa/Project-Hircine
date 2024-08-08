import cv2
from utils import ll_to_cart, get_obj_coords, fov_check, get_scales, overlay_detections, angle_conv

# Assumptions that would be gathered from pi or other sensors
# ususally would get positions in lat and lon but using preset distances for now
viewer_distance = 7  # in meters
viewer_angle = (90 - 350) % 360  # degrees from detector
fov = 72.2 # fov of vierwer

def render(frame, pi_lat, pi_lon, object_distances, object_angles, overlay, results, times, facing_angle = 215): 
    
    # convert facing angle of viewer to cartesian (0 is east)
    facing_angle = angle_conv([facing_angle])[0]

    # convert all object angles to traditional cartesian (0 is east)
    object_angles = angle_conv(object_angles)

    # Convert pi lat and lon to cartesian to figure relative positions of objects and viewer
    pi_coords = ll_to_cart(pi_lat, pi_lon)

    # Get coordinates of viewer and objects
    viewer_coords = get_obj_coords(pi_coords, [viewer_distance], [viewer_angle])[0]
    object_coords = get_obj_coords(pi_coords, object_distances, object_angles)

    # dx, dy = viewer_coords[0]-pi_coords[0], viewer_coords[1] - pi_coords[1]
    # print("Viewer Distance " + str(np.sqrt(dx**2 + dy**2)))
    # print("Viewer Angle " + str(np.degrees(np.arctan2(dy, dx)) % 360))
    # Check if objects are in fov of viewer and get angle from viewers pov
    in_fov, obj_angle_from_viewer, obj_distance_from_viewer = fov_check(viewer_coords, facing_angle, fov, object_coords)

    # Get render scales using bbox size
    scales = get_scales(object_distances, obj_distance_from_viewer, results)

    # Render objects given an overlay png
    overlay_detections(frame, overlay, in_fov, obj_angle_from_viewer, scales, fov, times)

    # print(f'Pi: {pi_coords}, \nViewer: {viewer_coords}, \nObject: {object_coords}')

    return frame
    
if __name__ == '__main__':
        # Example usage
    cap = cv2.VideoCapture(0)
    re, frame = cap.read()
    pi_lat, pi_lon = 0,0  # Example latitude and longitude
    object_distances = [10, 10, 10]  # Example distances in m
    object_angles = [90, 180, 270]  # Example angles in degrees
    img = cv2.imread('red.png', cv2.IMREAD_UNCHANGED)

    # Call the render function
    annotated_frame = render(frame, pi_lat, pi_lon, object_distances, object_angles, img, results = [1])
    cv2.imshow('Annotated Frame', frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()