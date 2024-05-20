import argparse
import os
import queue
import re
import threading
import webbrowser
from collections import defaultdict
from random import sample as random_sample

import cv2
import numpy as np
import requests
from pycountry import countries
from tqdm import tqdm

# object detection constants
MIN_CONFIDENCE = 0.6  # 60%
# NON_MAXIMA_THRESHOLD = 0.3

# threading constants
cpu_count = os.cpu_count() or 1
OPTIMIZED_MAX_WORKERS = int(cpu_count / 1.25) or 1  # 80% of the CPU cores

# web request constants
REQUEST_TIMEOUT = 10  # seconds
USER_AGENT = "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5"

# regex constants
IP_PATTERN = r"^(?:http)s?(?::\/\/)(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\/.*$"


def analyze_ip(url):
    camera_ip = url.split("/")[2].split(":")[0]
    ipinfo = "http://ipinfo.io/" + camera_ip + "/json"

    try:
        data = requests.get(ipinfo, timeout=REQUEST_TIMEOUT).json()
    except Exception as e:
        print(f"[ERROR] {e}")
        return "[ERROR] Couldn't establish a connection with ipinfo API.\n\n"

    ip = data["ip"]
    org = data["org"]
    city = data["city"]
    country = data["country"]
    region = data["region"]

    details = "IP details of the Camera:\n"
    details += f" IP: {org}\n Region: {region}\n Country: {country}\n City: {city}\n Org: {ip}\n\n"
    return details


def detect_objects(image, net, ol):
    net.setInput(
        cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    )
    layerOutputs = net.forward(ol)

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


def process_cameras(target_label):
    try:
        # load YOLO weights for each thread indivisually
        net = cv2.dnn.readNetFromDarknet(
            os.path.join("YOLO", "yolov4.cfg"), os.path.join("YOLO", "yolov4.weights")
        )
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

        # determine only the *output* layer names that we need from YOLO
        ln = net.getLayerNames()
        ol = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

        # main loop
        while not is_searching_done.is_set() or not cameras2scan.empty():
            try:
                camera = cameras2scan.get(timeout=5)
                stream = requests.get(
                    camera,
                    stream=True,
                    timeout=REQUEST_TIMEOUT,
                    headers={"User-Agent": USER_AGENT},
                ).raw

                # find the image in the response
                img_bytes = b""
                while True:
                    img_bytes += stream.read(1024)
                    a = img_bytes.find(b"\xff\xd8")
                    b = img_bytes.find(b"\xff\xd9")
                    if a != -1 and b != -1:
                        jpg = cv2.imdecode(
                            np.frombuffer(img_bytes[a : b + 2], dtype=np.uint8),
                            cv2.IMREAD_COLOR,
                        )
                        objects_detected = detect_objects(jpg, net, ol)

                        # find the objects
                        for obj, confidence in objects_detected.items():
                            all_the_objects_found[obj] += 1
                            if obj == target_label:
                                raw_results.append(camera)
                                camera_details = "\n\nURL: %s\n\n" % camera
                                camera_details += analyze_ip(camera)
                                camera_details += "Average Confidence: {:%}\n".format(
                                    confidence
                                )
                                final_results.append(camera_details)
                        break

                if raw_results:
                    pbar.set_description(
                        f"[SCANNING ({len(raw_results)} result{'s' if len(raw_results) > 1 else ''})]"
                    )
                pbar.update()
            except queue.Empty:
                # queue timeout
                continue
            except requests.exceptions.Timeout:
                pbar.update()
                continue
            except Exception as e:
                print(f"[ERROR] {e}")
                pbar.update()
                continue
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def search_cameras(n, url, max_pages):
    random_pages = random_sample(range(max_pages), (n // 6) + 1)

    for p in random_pages:
        try:
            content = requests.get(
                url + str(p),
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
            if content.status_code != 200:
                continue
            for ip in content.text.split('"'):
                if re.match(IP_PATTERN, ip):
                    cameras2scan.put(ip)
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            print(f"[ERROR] {e}")
            continue

    is_searching_done.set()
    return True


if __name__ == "__main__":
    # load the COCO class labels the YOLO model was trained on
    print("[LOADING] Loading object labels...")
    with open(os.path.join("YOLO", "coco.names")) as lablesFile:
        LABELS = lablesFile.read().strip().split("\n")

    def Country(x):
        x = x.upper()
        if countries.get(alpha_2=x) is None:
            raise argparse.ArgumentTypeError("Invalid country code.")

        country = countries.get(alpha_2=x).name.lower()
        r = requests.get(
            "http://www.insecam.org/en/bycountry/" + country,
            headers={"User-Agent": USER_AGENT},
        )
        if r.status_code != 200:
            raise argparse.ArgumentTypeError(
                "This is not available as a filter at the moment."
            )
        return x

    # argument parser
    parser = argparse.ArgumentParser(
        description="EagleEye - A tool for scanning public security cameras"
    )
    parser.add_argument(
        "-n",
        "--number",
        type=int,
        help="Maximum number of cameras to scan (100 is the deafult value)",
        default=100,
    )
    parser.add_argument(
        "-o",
        "--object",
        type=str.lower,
        help="The object you are searching for (Please refer to YOLOv3 - Darknet/coco.names - for more information)",
        choices=LABELS,
        required=True,
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        help="Limit the number of workers in the multiprocessing pool",
        default=OPTIMIZED_MAX_WORKERS,
    )
    parser.add_argument(
        "-c",
        "--country",
        type=Country,
        help="Filter the results by specifying a country",
    )
    args = parser.parse_args()

    raw_results = []
    final_results = []
    all_the_objects_found = defaultdict(int)

    cameras2scan = queue.Queue()
    is_searching_done = threading.Event()

    tag_filter = f"bycountry/{args.country}" if args.country else "bynew"
    url = f"http://www.insecam.org/en/{tag_filter}/?page="

    print(f"[PROCESSING] Scanning with {args.workers} threads!\n")
    pbar = tqdm(total=args.number, desc="[SCANNING]")

    try:
        searching_process = threading.Thread(
            target=search_cameras,
            args=(args.number, url, 100 if args.country else 1000),
            daemon=True,
        )
        searching_process.start()

        # Create a thread pool
        scanning_threads = [
            threading.Thread(target=process_cameras, args=(args.object,), daemon=True)
            for _ in range(args.workers)
        ]
        [thread.start() for thread in scanning_threads]
        [thread.join() for thread in scanning_threads]

        pbar.close()
    except KeyboardInterrupt:
        print("\n[EXITING] Keyboard Interrupt")
        pbar.close()

    print("\n\n[INFO] Objects found in this scan:")
    for obj, count in all_the_objects_found.items():
        if obj == "person" and count != 1:
            print(f" {count} people")
        else:
            print(f" {count} {obj}{'s' if count > 1 else ''}")

    if raw_results:
        print(f"\n\nAll the cameras consisiting of at least one {args.object}")
        print("\n".join(final_results))

        if input("\n\nOpen all the results in the web browser? (y/n): ").lower() == "y":
            [webbrowser.open(camera, new=2) for camera in raw_results]
    else:
        print(f"\n\nNone of the cameras include a {args.object}.")
