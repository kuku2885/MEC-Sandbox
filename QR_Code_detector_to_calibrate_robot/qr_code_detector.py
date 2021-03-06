import cv2
import contour_detector
import numpy as np
from Subfunctions.WebcamVideoStream import WebcamVideoStream
from pyimagesearch.transform import *
import time
cap = WebcamVideoStream(1).start()
time.sleep(0.5)
frame_count=0
framerate=0
qrCodeDetector = cv2.QRCodeDetector()
fontStyle = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 0.7
fontThickness = 2
t0=time.time()



def find_draw_contours_calculate_px_pos_angle(imgThres,imgAnnotated):
    contours, hierarchy = cv2.findContours(imgThres, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    obj_middle_pts_list = []
    obj_angle_list = []
    for i, c in enumerate(contours):
        area = cv2.contourArea(c)
        object_hierarchy = hierarchy[0][i][3] # -1 means has no parent
        if area < 50000 or area > 1000000 or object_hierarchy != -1:
            #skip contour
            continue
        cv2.drawContours(imgAnnotated, contours, i, (255, 0, 0), 2)
        # receive the angle and th emiddle pixel coordinate of the contour (object)
        angle, middle_px = contour_detector.getOrientation(c, imgAnnotated)
        obj_middle_pts_list.append(middle_px)
        obj_angle_list.append(angle)
    return imgAnnotated, obj_middle_pts_list, obj_angle_list

def gray_blur_canny_thres_dilate_image(image,lower_thres=100,upper_thres=255):
    def auto_canny(image, sigma=0.33):
        # compute the median of the single channel pixel intensities
        v = np.median(image)
        # apply automatic Canny edge detection using the computed median
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))
        edged = cv2.Canny(image, lower, upper)
        # return the edged image
        return edged
    # imgGray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    # imgBlur = cv2.bilateralFilter(imgGray, 11, 17, 17)
    imgCanny = cv2.Canny(image,10,200)
    # imgCanny = auto_canny(imgBlur)
    _, imgThres = cv2.threshold(imgCanny, 100, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # now add dilation to connect broken parts of an object
    # Taking a matrix of size 5 as the kernel
    kernel = np.ones((5,5), np.uint8)
    # The first parameter is the original image,
    # kernel is the matrix with which image is
    # convolved and third parameter is the number
    # of iterations, which will determine how much
    # you want to erode/dilate a given image.
    # imgThres = cv2.erode(imgThres, kernel, iterations=1)
    imgThres = cv2.dilate(imgThres, kernel, iterations=1)
    return imgThres

def paint(imageCopied, imgThres):

    contours, hierarchy = cv2.findContours(imgThres, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    decodedText, points, _ = qrCodeDetector.detectAndDecode(imageCopied)

    if points is not None:
        nrOfPoints = len(points[0])
        for i, c in enumerate(contours):
            area = cv2.contourArea(c)
            object_hierarchy = hierarchy[0][i][3] # -1 means has no parent
            if area < 50000 or area > 1000000 or object_hierarchy != -1:
                #skip contour
                continue
                for i0 in range(nrOfPoints):
                    nextPointIndex = (i0+1) % nrOfPoints
                    cv2.line(imageCopied, tuple(points[0][i0]), tuple(points[0][nextPointIndex]), (255,0,0), 5)
                    cv2.circle(imageCopied,tuple(points[0][i0]), 5, (0,0,255), 5)
        print(decodedText)


while True:
    image = cap.read()
    imageCopied = image.copy();
    imgThres = gray_blur_canny_thres_dilate_image(image)
    imageCopied, obj_middle_pts_list, obj_angle_list = find_draw_contours_calculate_px_pos_angle(imgThres,imageCopied)
    paint(imageCopied, imgThres)
    #shows the WebcamVideoStream
    t1=time.time()
    frame_count+=1
    if t1-t0>=1.0:
        framerate=frame_count
        frame_count=0
        t0=time.time()
    cv2.putText(imageCopied, "Framerate: "+str(framerate),
                (10,15),fontStyle, 0.5, (255,255,255), 2)

    cv2.imshow("Image", imageCopied)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()
