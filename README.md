# EagleEye

<p align="center">
  <img alt="logo" src="examples/logo.jpeg" width=320 />
</p>

EagleEye is a Python script that tracks public cameras scraped from Insecam public camera directory to find a specified object using the YOLOv4 object detection model. The objects available in this model can be found [here](https://github.com/pjreddie/darknet/blob/master/data/coco.names). EagleEye also utilizes multithreading to efficiently scan multiple camera streams concurrently.

## Features

- Detects objects in public camera streams using the YOLOv4 object detection model.
- Utilizes multithreading for efficient scanning of multiple camera streams simultaneously.
- Provides information about the detected camera's IP address, geolocation, and confidence level.
- Allows limiting the search to a specific country.
- Supports opening detected camera streams in a web browser.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/EagleEye.git
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Due to the restrictions of GitHub, the weights cannot be uploaded to this repository. Download `yolov4.weights` file 245 MB: [yolov4.weights](https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights) (Google-drive mirror [yolov4.weights](https://drive.google.com/open?id=1cewMfusmPjYWbrnuJRuKhPMwRe_b9PaT)) and place it in the directory named `YOLO`.

## Usage

1. Navigate to the project directory:

```bash
cd EagleEye
```

2. Run the script:

```bash
python EagleEye.py
```

3. Follow the prompts to specify the maximum number of cameras to scan, the object label to search for, and other optional parameters.

4. Once the scanning is complete, the script will display the detected camera URLs, IP information, and confidence levels.

5. You can choose to open the detected camera streams in a web browser.

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

EagleEye is released under the [GPLv3 License](LICENSE).

## Acknowledgments

Special thanks to:
- The [YOLO](https://github.com/AlexeyAB/darknet) object detection model and weights.
- The [Insecam website](http://www.insecam.org) for providing access to public camera streams.
- The [pycountry library](https://pypi.org/project/pycountry/) for country information.
- The [tqdm library](https://github.com/tqdm/tqdm) for progress bar visualization.
