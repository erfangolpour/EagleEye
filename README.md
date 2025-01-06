# ArguX

## Real-Time Object Detection in Public Camera Feeds

**ArguX** is a Python script that scans public cameras gathered from [Insecam](http://www.insecam.org/) to locate objects of interest through utilizing [YOLOv4](https://arxiv.org/pdf/2004.10934) object detection model. The name is inspired by Greek mythology, where Argus Panoptes (Ἀὁγος Πανόπτης, "All-seeing Argos") is a many-eyed giant capable of seeing everything.

---

## Features

- Multithreaded for scanning multiple streams simultaneously.
- Provides the detected camera's IP address, geolocation, and the model's confidence level in identifying the specified object.
- Filter searches by country.
- Option to open detected camera streams directly in your web browser.

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/erfangolpour/ArguX.git
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Download the YOLOv4 weights file (245 MB):

   - [yolov4.weights](https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights)
   - Google Drive mirror: [yolov4.weights](https://drive.google.com/open?id=1cewMfusmPjYWbrnuJRuKhPMwRe_b9PaT)

   Place the file in the `YOLO` directory.

---

## Usage

Run the script with the following options:

```bash
usage: ArguX.py [-h] [-n NUMBER] -o {person,bicycle,car,...} [-w WORKERS] [-c COUNTRY]

ArguX - A tool for scanning public security cameras

Options:
  -h, --help            Show this help message and exit.
  -n NUMBER, --number NUMBER
                        Maximum number of cameras to scan (default: 100).
  -o {person,bicycle,car,...}
                        Specify the object to search for (refer to YOLOv4 - Darknet/coco.names for options).
  -w WORKERS, --workers WORKERS
                        Limit the number of multiprocessing pool workers.
  -c COUNTRY, --country COUNTRY
                        Filter results by country.
```

You can find the list of searchable objects [here](https://github.com/pjreddie/darknet/blob/master/data/coco.names).

---

## Demonstration

<p align="center">
  <img alt="preview-gif" src="examples/preview.gif" />
</p>

---

## Configuration

The following settings can be customized in the script:

- `MIN_CONFIDENCE`: Minimum confidence threshold for object detection (default: 0.6).
- `OPTIMIZED_MAX_WORKERS`: Default number of worker threads (CPU cores minus one).
- `REQUEST_TIMEOUT`: Timeout duration for web requests in seconds (default: 10).
- `USER_AGENT`: User agent string for web requests.

---

## Contributing

Contributions are welcome! If you encounter any issues or have ideas for improvement, feel free to open an issue or submit a pull request.

---

## License

This project is licensed under the [GPLv3 License](LICENSE).

---

## Acknowledgments

Special thanks to:

- The [YOLO](https://github.com/AlexeyAB/darknet) object detection model.
- The [Insecam website](http://www.insecam.org) for public camera streams.
- The [tqdm library](https://github.com/tqdm/tqdm) for progress bar visualization.
