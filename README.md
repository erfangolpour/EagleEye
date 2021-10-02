# EagleEye
EagleEye combines the power of web scraping with machine vision and OpenCV to search for objects across the world using public cameras. The cameras are scraped from the internet, courtesy of [Insecam](www.insecam.org), and then processed using YoloV3 pretrained models. The available objects can be found [here](https://github.com/pjreddie/darknet/blob/master/data/coco.names).
## Pretrained Models
Currently, EagleEye uses YoloV3 weights to detect objects. Due to GitHub restrictions, the pretrained models could not be uploaded to this repository. However, they can be downloaded [here](https://pjreddie.com/media/files/yolov3.weights). You should place the pretrained model inside Yolo folder once you download it.

## Preview
![preview-gif](examples/preview.gif)

## TODO
- [X] Open the cameras in the browser
- [ ] Update the DNN model to YoloV4
- [ ] Add a graphical user interface
