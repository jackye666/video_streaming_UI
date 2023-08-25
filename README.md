# Video-Streaming-Software
A Flask Web-App to stream video and do inference based on the image
### Setup
## Using simulate mode(no model inference) and non-web UI and simulate-video
```
python app.py -s -g
 
```
## Using simulate mode(no model inference) and web UI and camera video stream
```
python app.py -s -c
 
```
### Pyinstaller
#### First do
```
pyinstaller -w -F --add-data "templates:templates" --add-data "static:static" app.py
 
```
#### Then do
```
pyinstaller -w -F --add-data "templates:templates" --add-data "static:static" --add-binary ../../video_streaming_UI/UI_env/lib/python3.10/site-packages/opencv_python.libs/*:. app.py
 
```

