import argparse
import logging
import os
import queue
import re
import threading
import webbrowser
from collections import defaultdict
from random import sample as random_sample
from typing import Dict, List, Tuple

import cv2
import numpy as np
import requests
from tqdm import tqdm

# object detection
MIN_CONFIDENCE = 0.6  # 60%

# threading
MAX_WORKERS = int((os.cpu_count() or 1) / 2 + 0.5)  # 50% of the CPU cores (round up)

# web request
REQUEST_TIMEOUT = 10  # seconds
USER_AGENT = "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5"

# regex (URLs of the form http(s)://IP/...)
URL_PATTERN = r"^(?:http)s?(?::\/\/)(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\/.*$"

# load the COCO class labels the YOLO model was trained on
with open(os.path.join("YOLO", "coco.names")) as lablesFile:
    LABELS = lablesFile.read().strip().splitlines()

# logger
logger = logging.getLogger(__name__)

# shared queues
cameras2scan: queue.Queue["Camera"] = queue.Queue()
is_searching_done = threading.Event()


def req(url: str, **kwargs) -> requests.Response:
    """Make web requests with proper headers and timeout"""
    return requests.get(
        url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT, **kwargs
    )


class Camera:
    def __init__(self, url: str):
        self.url = url
        self.ip = self.url.split("/")[2].split(":")[0]
        self.img: cv2.typing.MatLike
        self.objects: List[Tuple[str, np.floating]] = []
        self.city: str | None = None
        self.country: str | None = None
        self.region: str | None = None
        self.org: str | None = None

    def extract_img(self) -> bool:
        try:
            stream = req(self.url, stream=True).raw
        except Exception as e:
            logger.warning("[Error Retrieving Camera Stream] %s", e)
            return False

        # TODO: avoid infinite loops on invalid streams
        img_bytes = b""
        while True:
            try:
                img_bytes += stream.read(1024)
            except requests.exceptions.ReadTimeout:
                logger.warning("[Error Reading Camera Stream] Read Timeout")
            a = img_bytes.find(b"\xff\xd8")
            b = img_bytes.find(b"\xff\xd9")
            if a != -1 and b != -1:
                # store image for future reference rather than returning it
                self.img = cv2.imdecode(
                    np.frombuffer(img_bytes[a : b + 2], dtype=np.uint8),
                    cv2.IMREAD_COLOR,
                )
                return True

    def detect_objects(
        self, net: cv2.dnn.Net, ol: List[str]
    ) -> List[Tuple[str, np.floating]]:
        if not self.extract_img():
            return []

        net.setInput(
            cv2.dnn.blobFromImage(
                self.img, 1 / 255.0, (416, 416), swapRB=True, crop=False
            )
        )
        layerOutputs = net.forward(ol)

        # [objects[LABELS[np.argmax(detection[5:])]].append(np.amax(detection[5:])) for output in layerOutputs for detection in output if np.amax(detection[5:]) >= MIN_CONFIDENCE]
        objects: Dict[str, List[float]] = defaultdict(list)
        for output in layerOutputs:
            for detection in output:
                scores = detection[5:]
                classID = np.argmax(scores)
                confidence = scores[classID]

                if confidence >= MIN_CONFIDENCE:
                    objects[LABELS[classID]].append(confidence)

        self.objects = [
            (obj, np.max(confidence)) for obj, confidence in objects.items()
        ]
        return self.objects

    def evaluate_ip(self) -> None:
        try:
            data = req(f"http://ipinfo.io/{self.ip}/json").json()
            self.city = data["city"]
            self.country = data["country"]
            self.region = data["region"]
            self.org = data["org"]
        except Exception as e:
            logger.error("[Error Retrieving IP Info] %s", e)

    def __str__(self) -> str:
        camera_details = f"URL: {self.url}\n"
        camera_details += f"IP: {self.ip}\n"
        camera_details += f"City: {self.city or 'N/A'}\n"
        camera_details += f"Country: {self.country or 'N/A'}\n"
        camera_details += f"Region: {self.region or 'N/A'}\n"
        camera_details += f"Org: {self.org or 'N/A'}\n"
        object_summary = " - ".join(f"{obj}: {conf:.1%}" for obj, conf in self.objects)
        camera_details += f"Objects: {object_summary or "N/A"}"
        return camera_details

    def __repr__(self) -> str:
        return f"Camera({self.ip})"


class Scanner:
    def __init__(self, target_object: str) -> None:
        self.target_label = target_object

        # load YOLO weights for each thread indivisually
        self.net = cv2.dnn.readNetFromDarknet(
            os.path.join("YOLO", "yolov4.cfg"), os.path.join("YOLO", "yolov4.weights")
        )
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

        # determine only the output layer names that we need from YOLO
        ln = self.net.getLayerNames()
        self.ol = [ln[i - 1] for i in self.net.getUnconnectedOutLayers()]

        self.thread = threading.Thread(
            target=self.process_cameras,
            daemon=True,
        )

    def start(self) -> None:
        self.thread.start()

    def join(self) -> None:
        self.thread.join()

    def process_cameras(self) -> None:
        while not (is_searching_done.is_set() and cameras2scan.empty()):
            try:
                camera = cameras2scan.get(timeout=5)
                try:
                    for obj, _ in camera.detect_objects(self.net, self.ol):
                        all_the_objects_found[obj] += 1
                        if obj == self.target_label:
                            camera.evaluate_ip()
                            results.append(camera)
                            print(camera, end="\n\n")
                            pbar.set_description(
                                f"[SCANNING ({len(results)} result{'s' if len(results) != 1 else ''})]"
                            )
                except Exception as e:
                    logger.error("[Error Processing %s] %s", camera.ip, e)
            except queue.Empty:
                continue

            pbar.update()


class Searcher:
    def __init__(self, n: int, country: str) -> None:
        self.n = n
        tag_filter = f"bycountry/{country}" if country else "bynew"
        self.url = f"http://www.insecam.org/en/{tag_filter}/?page="
        self.max_pages = 100 if country else 1000

    def start(self) -> None:
        self.thread = threading.Thread(
            target=self.search_cameras,
            daemon=True,
        )
        self.thread.start()

    def join(self) -> None:
        self.thread.join()

    def search_cameras(self) -> None:
        # random_pages = random_sample(
        #     range(self.max_pages), (self.n // 6) + 1
        # )  # 6 cameras per page

        # we could sample just as many pages as we need, but some pages may be faulty
        # instead, assume 1 camera per page to account for errors (6/page in reality)
        random_pages = iter(random_sample(range(self.max_pages), self.n))
        while self.n > 0:
            try:
                content = req(self.url + str(next(random_pages))).text
                for url in content.split('"'):
                    if re.match(URL_PATTERN, url):
                        cameras2scan.put(Camera(url))
                        self.n -= 1
            except Exception as e:
                logger.warning("[Failed to Retrieve page on Insecam] %s", e)
                continue

        is_searching_done.set()


class EagleEye:
    def __init__(self, target_object: str, n: int, n_workers: int, country: str):
        self.scanner_pool = [Scanner(target_object) for _ in range(n_workers)]
        self.searcher = Searcher(n, country)

    def process(self):
        logger.info("[PROCESSING] Scanning with %s threads", args.workers)
        self.searcher.start()
        [thread.start() for thread in self.scanner_pool]
        self.searcher.join()
        [thread.join() for thread in self.scanner_pool]


if __name__ == "__main__":

    def Country(x):
        r = req(f"http://www.insecam.org/en/bycountry/{x}")
        if r.status_code != 200:
            raise argparse.ArgumentTypeError(
                "This country is not available as a filter at the moment."
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
        help="Maximum number of cameras to scan (default: %(default)s)",
        default=50,
    )
    parser.add_argument(
        "-t",
        "--target-object",
        type=str.lower,
        help="The object you are searching for (Please refer to `YOLO/coco.names` for more information)",
        choices=LABELS,
        metavar="TARGET",
        required=True,
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        help="Limit the number of workers in the multiprocessing pool (default: %(default)s)",
        default=MAX_WORKERS,
    )
    parser.add_argument(
        "-c",
        "--country",
        type=Country,
        help="Filter the results by specifying a country (default: %(default)s)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Increase output verbosity",
        action="store_true",
    )
    args = parser.parse_args()

    # ignore warnings by default
    logger.setLevel(logging.INFO if args.verbose else logging.ERROR)

    results: List[Camera] = []
    all_the_objects_found: Dict[str, int] = defaultdict(int)

    pbar = tqdm(total=args.number, desc="[SCANNING]")
    try:
        eagle_eye = EagleEye(
            args.target_object, args.number, args.workers, args.country
        )
        eagle_eye.process()
    except KeyboardInterrupt:
        logger.warning("[EXITING] Keyboard Interrupt")
    pbar.close()

    print("\n\n[INFO] Objects found in this scan:")
    for obj, count in all_the_objects_found.items():
        if obj == "person" and count != 1:
            print(f" {count} people")
        else:
            print(f" {count} {obj}{'s' if count > 1 else ''}")

    if results:
        print(f"\n\nAll the cameras consisiting of at least one {args.target_object}")
        print("\n\n".join(str(camera) for camera in results))

        if input("\n\nOpen all the results in the web browser? (y/n): ").lower() == "y":
            [webbrowser.open(camera.url, new=2) for camera in results]
    else:
        print(f"\n\nNone of the cameras include a {args.target_object}.")
