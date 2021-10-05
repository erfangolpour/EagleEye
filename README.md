# EagleEye
EagleEye combines the power of web scraping with machine vision to search for objects across the world using public cameras. The cameras are scraped from the internet, courtesy of [Insecam](https://insecam.org), and then processed using YoloV3 pretrained model. The available objects can be found [here](https://github.com/pjreddie/darknet/blob/master/data/coco.names).

## Pretrained Model
Currently, EagleEye uses YoloV3 weights to perform object detection. Due to GitHub restrictions, the pretrained model could not be uploaded to this repository. However, it can be downloaded [here](https://pjreddie.com/media/files/yolov3.weights). You should place the pretrained model inside Yolo folder once you download it.

## Preview
![preview-gif](examples/preview.gif)

## TODO
- [X] Open the results in the browser
- [ ] Update the DNN model to YoloV4
- [ ] Add a graphical user interface
