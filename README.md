
![PySceneDetect](https://raw.githubusercontent.com/Breakthrough/PySceneDetect/master/docs/img/pyscenedetect_logo_small.png)
==========================================================
Video Scene Cut Detection and Analysis Tool
----------------------------------------------------------

[![Build Status](https://img.shields.io/travis/com/Breakthrough/PySceneDetect/v0.6)](https://travis-ci.com/github/Breakthrough/PySceneDetect) [![PyPI Status](https://img.shields.io/pypi/status/scenedetect.svg)](https://pypi.python.org/pypi/scenedetect/) [![LGTM Analysis](https://img.shields.io/lgtm/grade/python/github/Breakthrough/PySceneDetect.svg)](https://lgtm.com/projects/g/Breakthrough/PySceneDetect) [![PyPI Version](https://img.shields.io/pypi/v/scenedetect?color=blue)](https://pypi.python.org/pypi/scenedetect/)  [![PyPI License](https://img.shields.io/pypi/l/scenedetect.svg)](http://pyscenedetect.readthedocs.org/en/latest/copyright/)

----------------------------------------------------------

### Version: v0.6-dev (TBD)

**Website**:  http://www.scenedetect.com

**Getting Started**: [Usage Example](https://pyscenedetect.readthedocs.io/en/latest/examples/usage-example/)

**Documentation**:  http://manual.scenedetect.com

**Discord**: https://discord.gg/H83HbJngk7

----------------------------------------------------------

**Quick Install**: To install PySceneDetect via `pip` with all dependencies:

    pip install scenedetect[opencv]

For servers, you can use the headless (non-GUI) version of OpenCV by installing `scenedetect[opencv-headless]`.  To enable video splitting support, you will also need to have `mkvmerge` or `ffmpeg` installed - see the documentation on [Video Splitting Support](https://pyscenedetect.readthedocs.io/en/latest/examples/video-splitting/) for details.

Requires Python modules `click`, `numpy`, OpenCV `cv2`, and (optional) `tqdm` for displaying progress.  For details, see the [dependencies on the downloads page](https://pyscenedetect.readthedocs.io/en/latest/download/#dependencies).

----------------------------------------------------------

**Quick Start (Command Line)**:

Split the input video wherever a new scene is detected:

    scenedetect -i video.mp4 detect-content split-video

Skip the first 10 seconds of the input video, and output a list of scenes to the terminal:

    scenedetect -i video.mp4 time -s 10s detect-content list-scenes

To show a summary of all other options and commands:

    scenedetect help

You can find more examples [on the website](https://pyscenedetect.readthedocs.io/en/latest/examples/usage-example/) or [in the manual](https://pyscenedetect.readthedocs.io/projects/Manual/en/latest/cli/global_options.html).

**Quick Start (Python API)**:

To get started, there is a high level function in the library that performs content-aware
scene detection on a video path:

```python
from scenedetect import detect_scenes

scene_list = detect_scenes('my_video.mp4')
```

Scenes will now be a list containing the start/end times of all scenes found in the video.
We can just call `print(scene_list)`, but to show the result in a nicer format:

```python
for i, scene in enumerate(scene_list):
    print('    Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
        i+1,
        scene[0].get_timecode(), scene[0].get_frames(),
        scene[1].get_timecode(), scene[1].get_frames(),))
```

You can also specify threshold, and an optional file to store the metrics calculated on each frame.
For more advanced usage the API is highly configurable and can easily integrate with any pipeline.
This includes using different detection algorithms, splitting the input video, and more.
For example:

```python
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg

def split_video_into_scenes(video_path, threshold=27.0):
    # Open our video, create a scene manager, and add a detector.
    video = open_video(path=video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(threshold=threshold))
    # Process all frames in the video, and show a progress bar.
    scene_manager.detect_scenes(video, show_progress=True)
    scene_list = scene_manager.get_scene_list()
    split_video_ffmpeg(video_path, scene_list)
```

See [the manual](https://pyscenedetect.readthedocs.io/projects/Manual/en/latest/api.html) for the full PySceneDetect API documentation.

----------------------------------------------------------

PySceneDetect is a command-line tool and Python library, which uses OpenCV to analyze a video to find each shot change (or "cut"/"scene").  If `ffmpeg` or `mkvmerge` is installed, the video can also be split into scenes automatically.  A frame-by-frame analysis can also be generated for a video, to help with determining optimal threshold values or detecting patterns/other analysis methods for a particular video.  See [the Usage documentation](https://pyscenedetect.readthedocs.io/en/latest/examples/usage/) for details.

There are two main detection methods PySceneDetect uses: `detect-threshold` (comparing each frame to a set black level, useful for detecting cuts and fades to/from black), and `detect-content` (compares each frame sequentially looking for changes in content, useful for detecting fast cuts between video scenes, although slower to process).  Each mode has slightly different parameters, and is described in detail below.

In general, use `detect-threshold` mode if you want to detect scene boundaries using fades/cuts in/out to black.  If the video uses a lot of fast cuts between content, and has no well-defined scene boundaries, you should use the `detect-content` mode.  Once you know what detection mode to use, you can try the parameters recommended below, or generate a statistics file (using the `-s` / `--statsfile` flag) in order to determine the correct paramters - specifically, the proper threshold value.

Note that PySceneDetect is currently in beta; see Current Features & Roadmap below for details.  For help or other issues, you can join [the official PySceneDetect Discord Server](https://discord.gg/H83HbJngk7), submit an issue/bug report [here on Github](https://github.com/Breakthrough/PySceneDetect/issues), or contact me via [my website](http://www.bcastell.com/about/).


Usage
----------------------------------------------------------

 - [Basic Usage](https://pyscenedetect.readthedocs.io/en/latest/examples/usage/)
 - [PySceneDetect Manual](https://pyscenedetect-manual.readthedocs.io/en/latest/), covers `scenedetect` command and Python API
 - [Example: Detecting and Splitting Scenes in Movie Clip](https://pyscenedetect.readthedocs.io/en/latest/examples/usage-example/)


Current Features & Roadmap
----------------------------------------------------------

You can [view the latest features and version roadmap on Readthedocs](http://pyscenedetect.readthedocs.org/en/latest/features/).
See [`docs/changelog.md`](https://github.com/Breakthrough/PySceneDetect/blob/master/docs/changelog.md) for a list of changes in each version, or visit [the Releases page](https://github.com/Breakthrough/PySceneDetect/releases) to download a specific version.  Feel free to submit any bugs/issues or feature requests to [the Issue Tracker](https://github.com/Breakthrough/PySceneDetect/issues).

Additional features being planned or in development can be found [here (tagged as `feature`) in the issue tracker](https://github.com/Breakthrough/PySceneDetect/issues?q=is%3Aissue+is%3Aopen+label%3Afeature).  You can also find additional information about PySceneDetect at [http://www.bcastell.com/projects/PySceneDetect/](http://www.bcastell.com/projects/PySceneDetect/).


----------------------------------------------------------

Licensed under BSD 3-Clause (see the `LICENSE` file for details).

Copyright (C) 2014-2021 Brandon Castellano.
All rights reserved.

