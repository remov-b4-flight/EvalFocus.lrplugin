from imutils import paths
import argparse
import cv2
import os

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--images", required=True,
                help="path to input directory of images")
ap.add_argument("-t", "--threshold", type=float, default=100.0,
                help="focus measures that fall below this value will be considered 'blurry'")
args = vars(ap.parse_args())


def variance_of_laplacian(image):
    return cv2.Laplacian(image, cv2.CV_64F)


def report_image(image, laplacian, faces, face_laplacians=None):
    text = "Not Blurry"
    if laplacian.var() < args["threshold"]:
        text = "Blurry"

    if len(faces):
        for index, (x, y, w, h) in enumerate(faces):
             cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)
             cv2.putText(image, "{}: {:.2f}".format("Face", face_laplacians[index].var()), (x, y),
                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)

    cv2.putText(image, "{}: {:.2f}".format(text, laplacian.var()), (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
    # cv2.imshow("Image", image)
    # key = cv2.waitKey(0)


def write_image(file_path, image, sub_dir="/report", suffix=""):
    dir_file = os.path.split(file_path)
    dir = dir_file[0]
    file_name = dir_file[1]
    report_dir = dir + sub_dir

    root, ext = os.path.splitext(report_dir + "/" + file_name)
    export_file_path = root + suffix + ext

    os.makedirs(report_dir, exist_ok=True)
    cv2.imwrite(export_file_path, image)

def face_recognition(gray):
    face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    return face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20))

def crop_faces(gray, faces):
    return [gray[y: y + h, x: x + w] for x,y,w,h in faces]

def resize_image(image):
    height, width = image.shape[:2]
    while width >= 1500:
        image = resize_image_to_harf(image)
        height, width = image.shape[:2]
    else:
        return image

def resize_image_to_harf(image):
    return cv2.resize(image,None,fx=0.5, fy=0.5)

for image_path in paths.list_images(args["images"]):
    original_image = cv2.imread(image_path)
    image = resize_image(original_image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces = face_recognition(gray)

    face_laplacians = None
    if len(faces):
        face_images = crop_faces(gray, faces)

        for index, face_image in enumerate(face_images):
            write_image(image_path, face_image, "/faces", "_" + str(index))

        face_laplacians = [variance_of_laplacian(face_image) for face_image in face_images]


    laplacian = variance_of_laplacian(gray)
    report_image(image, laplacian, faces, face_laplacians)
    write_image(image_path, image)
    write_image(image_path, laplacian, "/laplacian")
