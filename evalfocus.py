#!/opt/homebrew/bin/python3
## 
# @brief Evaluate focus by OpenCV functions.
# @author remov_b4_flight

import argparse
import cv2
import os
import sys

#Constants
MIN_RESULT = 5
MAX_RESULT = 255
YAML_PATH = "/opt/homebrew/share/opencv4/quality"
SMALL_LS = 3000
BIG_LS = 8000

def write_image(file_path, image, sub_dir="/log", suffix="") :
    dir_file = os.path.split(file_path)
    dir = dir_file[0]
    file_name = dir_file[1]
    report_dir = dir + sub_dir

    root, ext = os.path.splitext(report_dir + "/" + file_name)
    export_file_path = root + suffix + ext

    os.makedirs(report_dir, exist_ok=True)
    cv2.imwrite(export_file_path, image)

def adjust_long(long_side) :
    long_result = -1
    if (long_side >= BIG_LS) :
        long_result = int(long_side / 4)
    elif (SMALL_LS <= long_side and long_side < BIG_LS) :
        long_result = int(long_side / 2)
 
    return long_result

#main
result = 0

#Option parse
ap = argparse.ArgumentParser(description = "Evaluate image focus.")
ap.add_argument("file", help = "Image file to process.")
ap.add_argument("-v", help = "verbose outputs", action = 'count', default = 0)
ap.add_argument("-l", "--log", help = "save image log", action = 'store_true')
ap.add_argument("-m", "--model", help = "model", default = "yunet.onnx")
ap.add_argument("-bm", "--brisque_model", help = "BRISQUE model file", default = "brisque_model_live.yml")
ap.add_argument("-br", "--brisque_range", help = "BRISQUE range file", default = "brisque_range_live.yml")
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

#Read image
original_image = cv2.imread(image_path)
if original_image is None :
    print(image_path, " CAN'T READ.")
    sys.exit(1)

#BRISQUE evaluation
brisque_array = cv2.quality.QualityBRISQUE_compute(original_image, brisque_model, brisque_range)
brisque_score = round(brisque_array[0], 2)
if (verbose >= 1) : print("BRISQUE score =", brisque_score)
if (brisque_score > 80.0) :
    if (verbose >= 2) : print("Evaluate terminated by low BRISQUE score.")
    sys.exit(MIN_RESULT)

orig_height, orig_width, _ = original_image.shape
long_side = max(orig_height,orig_width)
resize_long = adjust_long(long_side)
if (resize_long < 0) : # No resize
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
    cv2.waitKey(1000)

if (verbose >= 2) : print("shape =", image.shape)

#Detect front face
fd = cv2.FaceDetectorYN_create(model, "", (0,0))
height, width, _ = image.shape
fd.setInputSize((width, height))
fdresult, faces = fd.detect(image)

if (verbose >= 3) : print("face detect =", fdresult)

faces_count = len(faces) if faces is not None else 0
if (verbose >= 1) :
    print("faces =", faces_count)

#If any face not found, process entire image.
faces = faces if faces is not None else [[0,0,width,height,-1]]

vlog_line = int(max(width,height) / 1000)
if (vlog_line < 3) : vlog_line = 3
writeflag = False

count = 1 if faces_count > 0 else 0
current_max = 0

#Loop with detected faces
for face in faces :
    if (verbose >= 1) : print("area ", count, end="")
    face_score = round(face[-1], 2) if faces_count > 0 else 0.0
    #Crop face
    face_x = int(face[1])
    face_width = int(face[1]+face[3])
    face_y = int(face[0])
    face_height = int(face[0]+face[2])
    face_image = image[ face_x:face_width,
                        face_y:face_height ]
    #Grayscale conversion
    gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    #Laplacian conversion
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    if (verbose >= 2 and faces_count > 0) :
        cv2.imshow("crop", laplacian)
        cv2.waitKey(1000)
    #Get result
    value = int(laplacian.var() + 0.5)
    if (verbose >= 1) : print(" value =", value, end="")

    #Report Visualization
    if ( args["log"] ) :
        writeflag = True
        box = list(map(int, face[:4]))
        cv2.rectangle(image, box, (255, 0, 0), vlog_line)
        cv2.putText(image, str(face_score), (face_y, face_x), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,0))

    if (verbose >= 1 and faces_count > 0) : print(" score =", face_score, end="")
    #End of loop
    count += 1
    if (value > current_max) : current_max = value
    if (verbose >= 1) : print()
#End loop of faces
if (writeflag == True) : write_image(image_path, image)

#Return value to OS
if (current_max > MAX_RESULT) :
    current_max = MAX_RESULT
elif (0 < current_max < MIN_RESULT) : 
    current_max = MIN_RESULT

result = current_max
print("result = ", result)
sys.exit(result)
