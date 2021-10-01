import os
import re
import numpy as np
from cv2 import cv2

from collections import defaultdict

from pycountry import countries

import webbrowser
import urllib.request
from json import load as loadJSON

from art import text2art
from colored import fg, attr

import queue
import threading

from tqdm import tqdm

from random import sample as random_sample

# object detection constants
MIN_CONFIDENCE = 0.6 # 60%
# NON_MAXIMA_THRESHOLD = 0.3

# threading constants
OPTIMIZED_MAX_WORKERS = os.cpu_count() - 1

# web request constants
REQUEST_TIMEOUT = 10 # seconds
USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5'

# regex constants
IP_PATTERN = r"^(?:http)s?(?::\/\/)(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\/.*$"

# load the COCO class labels the YOLO model was trained on
print(" %s[LOADING]%s Loading object labels..." % (fg('cyan'), attr('reset')))
with open(os.path.join("YOLO", "coco.names")) as lablesFile: LABELS = lablesFile.read().strip().split("\n")


def analyze_ip(url):
    camera_ip = url.split('/')[2].split(':')[0]
    ipinfo = 'http://ipinfo.io/' + camera_ip + '/json'

    try:
        response = urllib.request.urlopen(ipinfo, timeout = 10)
        data = loadJSON(response)
    except:
        return " [ERROR] Couldn't establish a connection with ipinfo API.\n\n"

    ip = data['ip']
    org = data['org']
    city = data['city']
    country = data['country']
    region = data['region']

    details = ' IP details of the Camera:\n\n'
    details += f' IP : {org} \n Region : {region} \n Country : {country} \n City : {city} \n Org : {ip} \n\n'
    return details


def detect_objects(image, net, ln):
    net.setInput(cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False))
    layerOutputs = net.forward(ln)

    objects = defaultdict(list)
    # [objects[LABELS[np.argmax(detection[5:])]].append(np.amax(detection[5:])) for output in layerOutputs for detection in output if np.amax(detection[5:]) >= MIN_CONFIDENCE]

    for output in layerOutputs:
        for detection in output:   
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            if confidence >= MIN_CONFIDENCE:
                objects[LABELS[classID]].append(confidence)

    return {obj: np.average(confidence) for obj, confidence in objects.items()}


def process_cameras(raw_results, final_results, all_the_objects_found):
    try:
        # load YOLO weights for eath thread indivisually
        net = cv2.dnn.readNetFromDarknet(os.path.join("YOLO", "yolov3.cfg"), os.path.join("YOLO", "yolov3.weights"))

        # determine only the *output* layer names that we need from YOLO
        ln = net.getLayerNames()
        ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

        # main loop
        while (not is_searching_done.is_set() or not cameras2scan.empty()) and not user_interruption.is_set():
            try:
                camera = cameras2scan.get(timeout=5)
                stream = urllib.request.urlopen(urllib.request.Request(camera, None, headers={'User-Agent': USER_AGENT}), timeout=REQUEST_TIMEOUT)

                # find the image in the response
                img_bytes = b''
                while True:
                    img_bytes += stream.read(1024)
                    a = img_bytes.find(b'\xff\xd8')
                    b = img_bytes.find(b'\xff\xd9')
                    if a != -1 and b != -1:
                        jpg = img_bytes[a:b+2]
                        objects_detected = detect_objects(cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR), net, ln)
                        
                        # find the objects
                        for obj, confidence in objects_detected.items():
                            all_the_objects_found[obj] += 1
                            if obj == object_label:
                                raw_results.append(camera)
                                camera_details = "\n\n URL: %s\n\n" % camera
                                camera_details += analyze_ip(camera)
                                camera_details += " Average Confidence: {:%}\n".format(confidence)
                                final_results.append(camera_details)
                        break
                
                if raw_results:
                    pbar.set_description(f" [SCANNING ({len(raw_results)} result{'s' if len(raw_results) > 1 else ''})]")
                pbar.update()
            except queue.Empty:
                # queue timeout
                continue
            except:
                # urllib.request timeout
                pbar.update()
                continue
        # print("DONE")
        return True
    except Exception as e:
        print("BIG HELLA ERROR LOL:", e)
        return False


def search_cameras(n, url):
    max_pages = 100 if CTR else 1000
    random_pages = random_sample(range(max_pages), (n // 6) + 1)
    
    for p in random_pages:
        try:
            req = urllib.request.Request(url + str(p), None, {'User-agent': USER_AGENT})
            content = str(urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT).read())
            for ip in content.split('"'):
                if re.match(IP_PATTERN, ip): cameras2scan.put(ip)
        except:
            continue
        
    is_searching_done.set()
    return True


if __name__ == "__main__":
    # clear the screen and print the label
    os.system('clear') if os.name == 'posix' else os.system('cls')
    print(fg('green'), text2art('EagleEye', 'rand'), attr('reset'), "\n\n")

    while True:
        n = input(" Maximum number of cameras to scan (100 is the deafult value): ")
        if not n or n.isdecimal(): break
        print("\n%s Please enter a valid number. %s\n" % (fg('red'), attr('reset')))
    n = 100 if not n else int(n)
    print("\n")

    while True:
        object_label = input(' The object you are searching for (Please refer to YOLOv3 - Darknet/coco.names - for more information): ').lower()
        if object_label in LABELS: break
        print("\n%s Unknown input. Please choose a label from coco.names list. %s\n" % (fg('red'), attr('reset')))
    print('\n')

    while True:
        max_workers = input(' Enter a limit for the number of workers in the multiprocessing pool, or press enter to use the default value (%s): ' % (OPTIMIZED_MAX_WORKERS))
        if not max_workers or max_workers.isdecimal(): break
        print("\n%s Please enter a valid number. %s\n" % (fg('red'), attr('reset')))
    if not max_workers: print("\n %s[NOTE] The default value is calcuated using the number of cores your processor has.%s" % (fg('grey_66'), attr('reset')))
    max_workers = OPTIMIZED_MAX_WORKERS if not max_workers else max(int(max_workers), 2)
    print("\n")

    CTR = input(' Do you want to limit the results and specify a country? If yes, enter the country code: ').upper()
    if CTR:
        try:
            urllib.request.urlopen(urllib.request.Request('http://www.insecam.org/en/bycountry/' + CTR, None, {'User-agent' : USER_AGENT}))
            print("\n%s [FOUND} Attack is locked on %s! %s" % (fg('green'), countries.get(alpha_2=CTR).name, attr('reset')))
        except:
            print("\n%s [NOT FOUND] This country code does not exist or is not available at the moment. %s \n" % (fg('red'), attr('reset')))
            print("%s [INFO] Starting the scan without geometric limitation... %s" % (fg('green'), attr('reset')))
            CTR = ''


    raw_results = []
    final_results = []
    all_the_objects_found = defaultdict(int)

    cameras2scan = queue.Queue()
    is_searching_done = threading.Event()
    user_interruption = threading.Event()

    tag_filter = "bycountry/" + CTR if CTR else "bynew"
    url = 'http://www.insecam.org/en/' + tag_filter + '/?page='

    print("\n\n [PROCESSING] Scanning with %s threads!\n" % max_workers)
    pbar = tqdm(total=n, desc=" [SCANNING]")

    try:
        searching_process = threading.Thread(target=search_cameras, args=(n, url,))
        scanning_processes = [threading.Thread(target=process_cameras, args=(raw_results, final_results, all_the_objects_found,)) for i in range(max_workers - 1)]
        
        searching_process.setDaemon(True)
        searching_process.start()
        
        [p.setDaemon(True) for p in scanning_processes]
        [p.start() for p in scanning_processes]

        for p in scanning_processes:
            p.join()
        pbar.close()
    except KeyboardInterrupt:
        print("\n [EXITING] Keyboard Interrupt")
        user_interruption.set()
        print(" [EXITING] Waiting for the workers to recieve the termination signal...")
        for p in scanning_processes:
            try:
                p.join(timeout=5)
            except:
                pass
        pbar.close()

    print("\n\n [INFO] Objects found in this scan:")
    for obj, count in all_the_objects_found.items():
        if obj == 'person' and count > 1:
            print(" %s people" % count)
        else:
            print(f" {count} {obj}{'s' if count > 1 else ''}") 

    if raw_results:
        print("\n\n All the cameras consisiting of at least one %s:" % object_label)
        [print(r) for r in final_results]

        if input('\n\n Open all the results in the web browser? (y/n): ').lower() == 'y':
            [webbrowser.open(camera, new = 2) for camera in raw_results]
    else:
        print("\n\n None of the cameras include a %s." % object_label)