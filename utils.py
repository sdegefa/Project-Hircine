import numpy as np
import base64
from PIL import Image
import io
import math
import cv2

def get_obj_coords(viewer_coords, object_distances, object_angles):
    coords = []
    for dist, angle in zip(object_distances, object_angles):
        # convert angle to radians for calculation
        angle_rad = np.radians(angle)

        dx = dist * np.cos(angle_rad)
        dy = dist * np.sin(angle_rad)
        
        x, y = dx + viewer_coords[0], dy + viewer_coords[1]

        coords.append(np.array([x, y]))
    
    return coords

def ll_to_cart(lat, lon):
    R = 6378137 # earths radius in m
    
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    # Earth's radius in meters
    R = 6378137.0
    
    # Mercator projection formulas
    x = R * lon_rad
    y = R * math.log(math.tan(math.pi/4 + lat_rad/2))

    return np.array([x, y])

def cart_to_ll(coords):
    R = 6378137 # earths radius in m
    lats = []
    lons = []
    for coord in coords:
        x = coord[0]
        y = coord[1]

        # Inverse Mercator projection formulas
        lon = x / R
        lat = 2 * math.atan(math.exp(y / R)) - math.pi/2

        # Convert latitude and longitude to degrees
        lat_deg = math.degrees(lat)
        lon_deg = math.degrees(lon)

        lats.append(lat_deg)
        lons.append(lon_deg)
        
    return lats, lons

def img_decode(img):
    # decode bytes
    img = base64.b64decode(img)
    # convert image into np array
    return np.array(Image.open(io.BytesIO(img)))


def img_toHTML(img):
    img = Image.fromarray(img.astype('uint8'), 'RGB')
    buf = io.BytesIO()
    img.save(buf, format = 'PNG')
    img_bytes = buf.getvalue()
    img = base64.b64encode(img_bytes).decode('utf-8')
    img_data = f'data:image/png;base64,{img}'
    return img_data

def fov_check(viewer_coords, facing_angle, fov, object_coords):
    in_fov = []
    angles = []
    distances = []
        
    max_distance = 150  # Maximum distance to render

    for obj in object_coords:
        dx, dy = obj[0] - viewer_coords[0], obj[1] - viewer_coords[1]
        distance = np.sqrt(dx**2 + dy**2)
        
        # Calculate angle of the object relative to the viewer
        angle_to_object = np.degrees(np.arctan2(dy, dx)) % 360
        # print(f"distance: {distance}, angle: {angle_to_object}")

        # Calculate the angle of the object relative to the viewer's facing direction
        angle_relative = (angle_to_object - facing_angle) % 360
        
        # Adjust angle_relative to be within -180 to 180 degrees
        if angle_relative > 180:
            angle_relative -= 360

        # Check if the angle is within the field of view
        in_fov_angle = -fov / 2 <= angle_relative <= fov / 2
        
        in_fov.append(in_fov_angle)
        angles.append(angle_relative)
        distances.append(distance)

    return in_fov, angles, distances

def get_scales(dist_detector, dist_viewer, results, red_height=598):
    scales = []
    
    for i in range(len(results)):
        # Assuming results[i]['box']['y1'] and results[i]['box']['y2'] give the height of the object
        object_height = abs(results[i]['box']['y1'] - results[i]['box']['y2'])
        
        if object_height == 0:  # Prevent division by zero
            scale = 0.00001
        else:
            # Calculate the scale factor
            # The perceived size is inversely proportional to the distance from the viewer
            scale = (red_height / object_height) * (dist_detector[i] / dist_viewer[i])
        
        scales.append(scale)

    return scales


def overlay_detections(frame, overlay, in_fov, angles, scales, fov, times):
    frame_height, frame_width = frame.shape[:2]
    
    # Find the oldest and newest times for normalization
    oldest_time = min(times)
    newest_time = max(times)
    time_range = newest_time - oldest_time if newest_time > oldest_time else 1  # Avoid division by zero
    
    for check, angle, scale, time in zip(in_fov, angles, scales, times):
        if check:
            # Convert angle to screen coordinates based on FOV
            screen_center_x = frame_width / 2
            screen_center_y = frame_height / 2
            
            # Calculate x offset from the center
            x_offset = math.floor(-angle * (frame_width / fov))  # Flipping offset direction
            y_offset = 0  # Assuming we are only dealing with horizontal FOV here

            # Calculate the center of the overlay
            center_x = int(screen_center_x + x_offset)
            center_y = int(screen_center_y + y_offset)
            
            # Ensure the center is within frame bounds
            center_x = np.clip(center_x, 0, frame_width - 1)
            center_y = np.clip(center_y, 0, frame_height - 1)
                        
            # Resize the overlay image
            detection_height, detection_width = overlay.shape[:2]
            new_width = int(detection_width * scale)
            new_height = int(detection_height * scale)
            
            # Resize the overlay with the adjusted dimensions
            resized_overlay = cv2.resize(overlay, (new_width, new_height))

            # Calculate the position for the resized overlay (centered at (center_x, center_y))
            top_left = (int(center_x - new_width // 2), int(center_y - new_height // 2))

            # Calculate the color based on the age of the detection
            time_factor = (time - oldest_time) / time_range
            blue = int(255 * (1 - time_factor))
            red = int(255 * time_factor)
            color = (blue, 0, red)  # BGR format

            # Apply the color tint to the overlay
            colored_overlay = apply_color_tint(resized_overlay, color)

            # Overlay the resized and colored detection image onto the frame
            overlay_image(frame, colored_overlay, top_left, opacity=0.5)

def apply_color_tint(image, color):
    # Ensure the image is in the correct format
    if image.dtype != np.float32:
        image = image.astype(np.float32) / 255.0

    # Separate the color channels and alpha channel
    if image.shape[2] == 4:  # RGBA
        rgb = image[:,:,:3]
        alpha = image[:,:,3]
    else:  # RGB
        rgb = image
        alpha = None

    # Create a color overlay for the RGB channels
    color_overlay = np.full(rgb.shape, color, dtype=np.float32) / 255.0
    
    # Blend the image with the color overlay
    tinted_rgb = cv2.addWeighted(rgb, 0.6, color_overlay, 0.4, 0)
    
    # Recombine with the alpha channel if it exists
    if alpha is not None:
        tinted_image = np.dstack((tinted_rgb, alpha))
    else:
        tinted_image = tinted_rgb
    
    # Convert back to uint8
    return (tinted_image * 255).astype(np.uint8)

def overlay_image(background, overlay, position, opacity=0.5):
    x, y = position
    h, w = overlay.shape[:2]

    # Define the region of interest (ROI) based on the position and overlay size
    x_end = min(x + w, background.shape[1])
    y_end = min(y + h, background.shape[0])
    x_start = max(x, 0)
    y_start = max(y, 0)

    # Calculate the size of the overlay that fits within the bounds
    overlay_part = overlay[
        max(0, y - y_start):y_end - y,
        max(0, x - x_start):x_end - x
    ]
    
    # Extract the corresponding region from the background
    roi = background[y_start:y_end, x_start:x_end]

    # Resize the ROI to match the overlay_part if needed
    if overlay_part.shape[:2] != roi.shape[:2]:
        overlay_part_resized = cv2.resize(overlay_part, (roi.shape[1], roi.shape[0]))
    else:
        overlay_part_resized = overlay_part

    if overlay_part_resized.shape[2] == 4:  # If the overlay has an alpha channel
        overlay_color = overlay_part_resized[:, :, :3]
        alpha_channel = overlay_part_resized[:, :, 3] / 255.0  # Normalize alpha to [0, 1]
        
        # Set desired opacity for non-fully transparent pixels
        adjusted_alpha_channel = np.where(alpha_channel > 0, opacity, 0)  # Apply the flat opacity

        # Perform blending
        for c in range(3):  # Iterate over the 3 color channels
            roi[:, :, c] = (adjusted_alpha_channel * overlay_color[:, :, c] +
                            (1 - adjusted_alpha_channel) * roi[:, :, c])
    else:
        # If no alpha channel, directly overlay without transparency
        roi[:] = cv2.addWeighted(roi, 1 - opacity, overlay_part_resized, opacity, 0)

    # Place the blended ROI back into the background
    background[y_start:y_end, x_start:x_end] = roi

def convert_frame_to_base64(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    return frame_base64

def angle_conv(object_angles):
    angles = []
    for angle in object_angles:
        angle = (90 - angle) % 360
        angles.append(angle)
    
    return angles