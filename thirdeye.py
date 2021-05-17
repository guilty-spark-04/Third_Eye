import io
import os
from google.cloud import vision
from google.cloud.vision import types
from google.oauth2 import service_account
from gtts import gTTS
import cv2
from PIL import Image, ImageDraw
import time
import RPi.GPIO as gpio
import threading





gpio.setmode(gpio.BOARD)
num_people = 0
output_text = ""
ModeChange = 1
TRIG_1 = 38
ECHO_1 = 40
TRIG_2 = 24
ECHO_2 = 26
language = 'en'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"
############################################################################################
def detect_face(file, max_results=4):

    with open(file,"rb") as face_file:
        client = vision.ImageAnnotatorClient()

        content = face_file.read()
        image = types.Image(content=content)

    return client.face_detection(
        image=image, max_results=max_results).face_annotations

def highlight_faces(image, faces): #person detection function
    im = Image.open(image)
    draw = ImageDraw.Draw(im)
    # Specify the font-family and the font-size
    for face in faces:
        box = [(vertex.x, vertex.y)
               for vertex in face.bounding_poly.vertices]
        draw.line(box + [box[0]], width=5, fill='#00ff00')
        # Place the confidence value/score of the detected faces above the
        # detection box in the output image
        draw.text(((face.bounding_poly.vertices)[0].x,
                   (face.bounding_poly.vertices)[0].y - 30),
                  str(format(face.detection_confidence, '.3f')) + '%',
                  fill='#FF0000')
    im.save("live.png")


def localize_objects(path):
    """Localize objects in the local image.

    Args:
    path: The path to the local file.
    """
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    with open(path, 'rb') as image_file:
        content = image_file.read()
    image = vision.types.Image(content=content)

    objects = client.object_localization(
        image=image).localized_object_annotations

    return objects




# Instantiates a client
client = vision.ImageAnnotatorClient()
def detect_text(path):
    """Detects text in the file."""
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    string = ''
    i = 0
    for text in texts:
        i+=1
        if (i < 15):
            string+=' ' + text.description
    try:    
        detection = gTTS(text = string, lang = language, slow = False)
        detection.save("detection.mp3")
        os.system("mpg321 detection.mp3")
        sleep()
    except:
        string = "There is no text to read"
        detection = gTTS(text = string, lang = language, slow = False)
        detection.save("detection.mp3")
        os.system("mpg321 detection.mp3")
    
###############################################################################################################


def distance_calc(trig,echo):
    gpio.setmode(gpio.BOARD)
    #print("Distance Measurement in Progress")
    gpio.setup(trig,gpio.OUT)
    gpio.setup(echo,gpio.IN)

    gpio.output(trig,False)
    #print("Waiting for sensor to settle")
    time.sleep(2)
    gpio.output(trig,True)
    time.sleep(.00001)
    gpio.output(trig,False)
    while gpio.input(echo)==0:
        pulse_start = time.time()
    while gpio.input(echo)==1:
        pulse_end = time.time()
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration *17150
    distance = round(distance,2)
    distance = distance/30.48 #converts distance from cm to feet
    return int(distance)

def object_analysis():
        # Capture frame-by-frame
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        file = 'live.png'
        cv2.imwrite( file,frame)
        objects = localize_objects(file)
        for item in objects:
            print(item.name)
        output_text = ""
        for item in objects:
            if (not(item.name in output_text)):
                output_text += ' ' + item.name
        detection = gTTS(text = output_text, lang = language, slow = False)
        detection.save("detection.mp3")

            # Starts playing the audio
        os.system("mpg321 detection.mp3")

        cap.release()
        cv2.destroyAllWindows()
        sleep()

#########
#button activations #event trigger for object scan button
def ObjectScan(channel):
    print("Button was pushed!")
    object_analysis()
    if ModeChange == 1:
        distance_left = distance_calc(TRIG_1,ECHO_1)
        distance_right = distance_calc(TRIG_2,ECHO_2)
        if distance_left > 2 and distance_left <7:
            output_text = "Warning, there is an object",str(distance_left),"feet on your left"
            detection = gTTS(text=output_text,lang=language,slow=False)
        if distance_right > 2 and distance_right < 7:
            output_text = "Warning, there is an object",str(distance_right),"feet on your right"


def TextScan(channel): #event trigger for text scan button press
    cap = cv2.VideoCapture(0)
    print("Text Scann Button was pushed!")
    ret, frame = cap.read()
    file = 'live.png'
    cv2.imwrite(file,frame)
    detect_text(file)
    
def ToggleMode(channel): #event trigger for mode change button
    print(" Mode ButtonButton was pushed!")
    global ModeChange
    if ModeChange == 1:
        ModeChange =0
    else:
        ModeChange = 1
    gpio.setmode(gpio.BOARD)

def sleep(): #constantly scans for button presses
    while True:
        time.sleep(1)
        #gpio.setup(37, gpio.IN, pull_up_down=gpio.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
        gpio.add_event_detect(37,gpio.RISING,callback=ObjectScan, bouncetime = 25)

        #gpio.setup(13, gpio.IN, pull_up_down=gpio.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
        gpio.add_event_detect(13,gpio.RISING,callback=ToggleMode, bouncetime = 1)


        #gpio.setup(15, gpio.IN, pull_up_down=gpio.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
        gpio.add_event_detect(15,gpio.RISING,callback=TextScan, bouncetime = 25) # Setup event on pin 10 rising edge

    #button detection
gpio.setup(37, gpio.IN, pull_up_down=gpio.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
gpio.add_event_detect(37,gpio.RISING,callback=ObjectScan, bouncetime = 25)

gpio.setup(13, gpio.IN, pull_up_down=gpio.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
gpio.add_event_detect(13,gpio.RISING,callback=ToggleMode, bouncetime = 1)


gpio.setup(15, gpio.IN, pull_up_down=gpio.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
gpio.add_event_detect(15,gpio.RISING,callback=TextScan, bouncetime = 25) # Setup event on pin 10 rising edge

    


while True: #distance calculations to determine how far an object is. Determines if its coming from left or right side
    if ModeChange == 0:
        print (TRIG_1,ECHO_1)
        print(TRIG_2, ECHO_2)
        distance_left = distance_calc(TRIG_1,ECHO_1)
        print(distance_left)
        distance_right = distance_calc(TRIG_2,ECHO_2)
        print(distance_right)
        if distance_left > 2 and distance_left <7:
            output_text = "Warning, there is an object"+ str(distance_left)+"feet on your right"
            detection = gTTS(text = output_text, lang = language, slow = False)
            detection.save("detection.mp3")
            os.system("mpg321 detection.mp3")
        if distance_right > 2 and distance_right < 7:
            output_text = ("Warning, there is an object"+str(distance_right)+"feet on your left")
            detection = gTTS(text = output_text, lang = language, slow = False)
            detection.save("detection.mp3")
            os.system("mpg321 detection.mp3")
    time.sleep(10)
gpio.cleanup() # Clean up    
#############

