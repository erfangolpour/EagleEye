# EagleEye
EagleEye combines the power of web scraping and machine vision to search for objects across the globe using public IP cameras. The cameras are scraped from the internet, courtesy of [Insecam](https://insecam.org), and then processed using YoloV3 pretrained model. The objects available in this model can be found [here](https://github.com/pjreddie/darknet/blob/master/data/coco.names).

## Pretrained Model
Currently, EagleEye uses YoloV3 weights to perform object detection. Due to GitHub restrictions, the weights cannot be uploaded to this repository. However, they can be downloaded from [this](https://pjreddie.com/media/files/yolov3.weights) url. You should place the pretrained model inside Yolo folder once you downloaded it.

## Preview
Cars are the object of interest in this example:
![preview-gif](examples/preview.gif)

## TODO
- [X] Open the results in the browser
- [ ] Update the DNN model to YoloV4
- [ ] Add a graphical user interface
