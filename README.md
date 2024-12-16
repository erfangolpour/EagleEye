# ArguX

Find a car, a toaster, or even a zebra and watch it in real-time! ArguX is a Python script that tracks public cameras scraped from Insecam public camera directory to find a specified object using [YOLOv4](https://arxiv.org/pdf/2004.10934). The name is borrowed from Greek mythology. Argus or Argos Panoptes (Ancient Greek: Ἄργος Πανόπτης, "All-seeing Argos") is a many-eyed giant in Greek mythology that can see "all".

## Features

- Detects objects in public camera streams using YOLOv4.
- Utilizes multithreading for efficient scanning of multiple camera streams simultaneously.
- Provides information about the detected camera's IP address, geolocation, and confidence level.
- Allows limiting the search to a specific country.
- Can automatically open detected camera streams in your web browser.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/erfangolpour/ArguX.git
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Download `yolov4.weights` file 245 MB: [yolov4.weights](https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights) (Google-drive mirror [yolov4.weights](https://drive.google.com/open?id=1cewMfusmPjYWbrnuJRuKhPMwRe_b9PaT)) and place it in the directory named `YOLO`.

## Usage

```
usage: ArguX.py [-h] [-n NUMBER] -o {person,bicycle,car,...}
                   [-w WORKERS] [-c COUNTRY]

ArguX - A tool for scanning public security cameras

options:
  -h, --help            show this help message and exit
  -n NUMBER, --number NUMBER
                        Maximum number of cameras to scan (100 is the deafult value)
  -o {person,bicycle,car,...}
                        The object you are searching for (Please refer to YOLOv4 - Darknet/coco.names - for more information)
  -w WORKERS, --workers WORKERS
                        Limit the number of workers in the multiprocessing pool
  -c COUNTRY, --country COUNTRY
                        Filter the results by specifying a country
```

The list of objects available to search for can be found [here](https://github.com/pjreddie/darknet/blob/master/data/coco.names).

## Demonstration

<p align="center">
  <img alt="preview-gif" src="examples/preview.gif" />
</p>

## Configuration

- `MIN_CONFIDENCE`: The minimum confidence threshold for object detection (default: 0.6).
- `OPTIMIZED_MAX_WORKERS`: The default number of worker threads (set to the number of CPU cores minus one).
- `REQUEST_TIMEOUT`: The timeout for web requests in seconds (default: 10).
- `USER_AGENT`: The user agent string for web requests.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

ArguX is released under the [GPLv3 License](LICENSE).

## Acknowledgments

Special thanks to:
- The [YOLO](https://github.com/AlexeyAB/darknet) object detection model.
- The [Insecam website](http://www.insecam.org) for providing access to public camera streams.
- The [tqdm library](https://github.com/tqdm/tqdm) for progress bar visualization.
