#!/opt/homebrew/bin/python3
## 
# @brief Evaluate focus by OpenCV functions.
# @author remov_b4_flight

import argparse
import cv2
import os
import sys

# Constants
MIN_RESULT = 5
MAX_RESULT = 255
YAML_PATH = "."
SMALL_LS = 3000
BIG_LS = 8000
VISUAL_WAIT = 1500
MOUTH_DEDUCT = 0.75
# FaceDetectorYN result index
FACE_X = 0; FACE_Y = 1
FACE_WIDTH = 2 ; FACE_HEIGHT = 3
FACE_REYE_X = 4 ; FACE_REYE_Y = 5
FACE_LEYE_X = 6 ; FACE_LEYE_Y = 7
FACE_NOSE_X = 8 ; FACE_NOSE_Y = 9
FACE_RMOUTH_X = 10 ; FACE_RMOUTH_Y = 11
FACE_LMOUTH_X = 12 ; FACE_LMOUTH_Y = 13
FACE_TRUSTY = 14

# Write vlog image to home
def write_image(file_path, image, sub_dir="vlog", suffix="") :
    homedir = os.environ['HOME']
    (_, file_name) = os.path.split(file_path)
    report_dir = os.path.join(homedir, sub_dir)
    os.makedirs(report_dir, exist_ok=True)

    export_file_path = os.path.join(report_dir,file_name)

    cv2.imwrite(export_file_path, image)

# get 1/(2^n) long side size for image
def adjust_long(long_side) :
    long_result = -1
    if (long_side >= BIG_LS) :
        long_result = int(long_side / 4)
    elif (SMALL_LS <= long_side and long_side < BIG_LS) :
        long_result = int(long_side / 2)
 
    return long_result

# Main
result = 0

# Option parse
ap = argparse.ArgumentParser(description = "Evaluate image focus.")
ap.add_argument("file", help = "Image file to process.")
ap.add_argument("-v", help = "verbose outputs", action = 'count', default = 0)
ap.add_argument("-l", "--log", help = "save image log", action = 'store_true')
ap.add_argument("-m", "--model", help = "model", default = "yunet.onnx")
ap.add_argument("-bm", "--brisque_model", help = "BRISQUE model file", default = "brisque_model_live.yml")
ap.add_argument("-br", "--brisque_range", help = "BRISQUE range file", default = "brisque_range_live.yml")
ap.add_argument("-n", "--noresize", help = "no resize", action = 'store_true')

args = vars(ap.parse_args())

verbose = args["v"]
model_path = os.path.dirname(os.path.abspath(__file__))
model = os.path.join(model_path, args["model"])

brisque_model = YAML_PATH + os.sep + args["brisque_model"]
brisque_range = YAML_PATH + os.sep + args["brisque_range"]

if (verbose >= 3) : 
    print("model =", model)
    print("brisque_model =", brisque_model)
    print("brisque_range =", brisque_range)

image_path = args["file"]

if (verbose >= 1) : print("input image =", image_path)
# Read image
original_image = cv2.imread(image_path)
if original_image is None :
    print(image_path, " CAN'T READ.")
    sys.exit(1)

# BRISQUE evaluation
brisque_array = cv2.quality.QualityBRISQUE_compute(original_image, brisque_model, brisque_range)
brisque_score = round(brisque_array[0], 2)
if (verbose >= 1) : print("BRISQUE score =", brisque_score)
if (brisque_score > 80.0) :
    if (verbose >= 2) : print("Evaluate terminated by low BRISQUE score.")
    sys.exit(MIN_RESULT)

orig_height, orig_width, _ = original_image.shape
long_side = max(orig_height,orig_width)
resize_long = adjust_long(long_side)
if (resize_long < 0 or args["noresize"] == True) : # No resize
    image = original_image
else :
    aspect = orig_width / orig_height
    if (orig_height >= orig_width) : #portlait
        target_size = (int(resize_long * aspect), resize_long)
    else : #landscape
        target_size = (resize_long, int(resize_long / aspect))
    image = cv2.resize(original_image,target_size, interpolation = cv2.INTER_NEAREST_EXACT)

if (verbose >= 3) :
    cv2.imshow("resize",image)
    cv2.waitKey(VISUAL_WAIT)

if (verbose >= 2) : print("shape =", image.shape)

# Detect faces
fd = cv2.FaceDetectorYN_create(model, "", (0,0))
height, width, _ = image.shape
fd.setInputSize((width, height))
fdresult, faces = fd.detect(image)

faces_count = len(faces) if faces is not None else 0
if (verbose >= 1) :
    print("faces =", faces_count)

# If any face not found, process entire image.
faces = faces if faces is not None else [[
    0, 0, width, height, 
    0, 0,   # right eye (x,y)
    0, 0,   # left eye (x,y)
    0, 0,   # nose (x,y)
    -1, -1,   # right mouth edge (x,y)
    -1, -1,   # left mouth edge (x,y)
    -1
]]

vlog_line = int(max(width,height) / 1000)
if (vlog_line < 3) : vlog_line = 3
writeflag = False

count = 1 if faces_count >= 1 else 0
current_max = 0

# Loop with detected faces
for face in faces :

    if (verbose >= 1) : print("area ", count, end="")
    face_rmouth_x = int(face[FACE_RMOUTH_X])
    face_rmouth_y = int(face[FACE_RMOUTH_Y])
    face_lmouth_x = int(face[FACE_LMOUTH_X])
    face_lmouth_y = int(face[FACE_LMOUTH_Y])
    if (faces_count >= 1 and verbose >= 2) :
        print(" mouth =", face_rmouth_x, face_lmouth_x, end="")
    face_trusty = round(face[FACE_TRUSTY], 2) if faces_count >= 1 else 0.0
    #Crop face
    face_x1 = int(face[FACE_X])
    face_x2 = int(face[FACE_X] + face[FACE_WIDTH])
    face_y1 = int(face[FACE_Y])
    face_y2 = int(face[FACE_Y] + face[FACE_HEIGHT])
    face_image = image[ face_y1 : face_y2,
                        face_x1 : face_x2 ]
    #Grayscale conversion
    gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    #Laplacian conversion
    laplacian = cv2.Laplacian(gray, cv2.CV_8U)
    if (verbose >= 2 and faces_count >= 1) :
        cv2.imshow("crop", laplacian)
        cv2.waitKey(VISUAL_WAIT)
    # Get result
    mean_array ,stddev_array = cv2.meanStdDev(laplacian)
    mean = round(mean_array[0][0], 2)
    stddev = stddev_array[0][0]

    # If both mouth edge not detected, results deducted.
    if (faces_count >=1 and face_rmouth_x <= 0 and face_lmouth_x <= 0) : 
        stddev *= MOUTH_DEDUCT

    value = int((stddev * 8) + 0.5)
    if (verbose >= 1) : print(" stddev =", round(stddev, 2), end="")
    if (verbose >= 2) : print(" mean =", mean, end="")

    # Report Visualization
    if ( args["log"] ) :
        writeflag = True
        box = list(map(int, face[:4]))
        cv2.rectangle(image, box, (255, 0, 0), vlog_line)
        cv2.putText(image, str(face_trusty), (face_x1, (face_y1 - 8)), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,0))
        cv2.circle(image, [face_rmouth_x, face_rmouth_y], 5, (255,0,255), -1, cv2.LINE_AA)
        cv2.circle(image, [face_lmouth_x, face_lmouth_y], 5, (255,0,255), -1, cv2.LINE_AA)

    if (verbose >= 1 and faces_count >= 1) : 
        print(" score =", face_trusty, end="")
    # End of loop
    count += 1
    if (value > current_max) : current_max = value
    if (verbose >= 1) : print()
# End loop of faces
if (writeflag == True) : write_image(image_path, image)

# Return value to OS
if (current_max > MAX_RESULT) :
    current_max = MAX_RESULT
elif (0 < current_max < MIN_RESULT) : 
    current_max = MIN_RESULT

result = current_max
print("result =", result)
sys.exit(result)
