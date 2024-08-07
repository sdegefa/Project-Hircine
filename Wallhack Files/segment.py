import cv2
import numpy as np
from torchvision import models, transforms
import torch
import math

def segment_detections(results, image):    
    
    # Get bboxes
    bboxes = []
    for result in results:
        bboxes.append((result['box']['x1'],result['box']['y1'],result['box']['x2'],result['box']['y2']))
    
    # Initialize the model
    model = models.segmentation.deeplabv3_resnet101(pretrained=True).eval()

    # Transform for the model
    preprocess = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((520, 520)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    transparent_images = []

    for bbox in bboxes:
        r_bbox = tuple([math.floor(x) if isinstance(x, float) else x for x in bbox])
        x1, y1, x2, y2 = r_bbox
        roi = image[y1:y2, x1:x2]

        # Preprocess
        input_tensor = preprocess(roi).unsqueeze(0)

        # Perform inference
        with torch.no_grad():
            output = model(input_tensor)['out'][0]
        output_predictions = output.argmax(0).byte().cpu().numpy()

        # Create binary mask for the person class (e.g., class index 15)
        mask_person = (output_predictions == 15).astype(np.uint8) * 255

        # Resize mask_person to match the ROI size
        mask_person_resized = cv2.resize(mask_person, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST)

        # Create transparent image
        transparent_image = cv2.cvtColor(roi, cv2.COLOR_BGR2BGRA)
        transparent_image[..., 3] = mask_person_resized

        # Append to the list
        transparent_images.append(transparent_image)

    return transparent_images
