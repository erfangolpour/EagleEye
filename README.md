# EagleEye
EagleEye combines the power of web scraping and machine vision to search for objects across the globe using public IP cameras. The cameras are scraped from the internet, courtesy of [Insecam](https://insecam.org), and then processed using YOLOv3 pretrained model. The objects available in this model can be found [here](https://github.com/pjreddie/darknet/blob/master/data/coco.names).

## Pretrained Model
Currently, EagleEye uses YoloV3 weights to perform object detection. Due to the restrictions of GitHub, the weights cannot be uploaded to this repository. However, they are available to download from [this](https://pjreddie.com/media/files/yolov3.weights) url. You should place the pretrained model inside the folder associated with Yolo once you downloaded it.

## Preview
Cars are the object of interest in this example:
![preview-gif](examples/preview.gif)

## TODO
- [X] Automatically open the results
- [ ] Update the DNN model to YOLOVv4
- [ ] Add a graphical user interface
