# -*- coding: utf-8 -*-
#
#         PySceneDetect: Python-Based Video Scene Detector
#   ---------------------------------------------------------------
#     [  Site: http://www.bcastell.com/projects/PySceneDetect/   ]
#     [  Github: https://github.com/Breakthrough/PySceneDetect/  ]
#     [  Documentation: http://pyscenedetect.readthedocs.org/    ]
#
# Copyright (C) 2014-2021 Brandon Castellano <http://www.bcastell.com>.
#
# PySceneDetect is licensed under the BSD 3-Clause License; see the included
# LICENSE file, or visit one of the following pages for details:
#  - https://github.com/Breakthrough/PySceneDetect/
#  - http://www.bcastell.com/projects/PySceneDetect/
#
# This software uses Numpy, OpenCV, click, tqdm, simpletable, and pytest.
# See the included LICENSE files or one of the above URLs for more information.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

"""PySceneDetect scenedetect.scene_manager Tests

This file includes unit tests for the scenedetect.scene_manager.SceneManager class,
which applies SceneDetector algorithms on VideoStream backends.
"""

# Standard project pylint disables for unit tests using pytest.
# pylint: disable=no-self-use, protected-access, multiple-statements, invalid-name
# pylint: disable=redefined-outer-name

# Standard Library Imports
import os
import os.path
import glob

# PySceneDetect Library Imports
from scenedetect.scene_manager import SceneManager
from scenedetect.scene_manager import save_images
from scenedetect.frame_timecode import FrameTimecode
from scenedetect.backends.opencv import VideoStreamCv2
from scenedetect.detectors import ContentDetector

# TODO(v1.0): Add hard-coded results for test files.

def test_detect_scenes(test_video_file):
    """ Test SceneManager with VideoStream and ContentDetector. """
    video = VideoStreamCv2(test_video_file)
    sm = SceneManager()
    sm.add_detector(ContentDetector())

    video_fps = video.frame_rate
    end_time = FrameTimecode('00:00:05', video_fps)

    sm.auto_downscale = True
    num_frames = sm.detect_scenes(video, end_time=end_time)
    assert num_frames == end_time.get_frames() + 1


def test_scene_list(test_video_file):
    """ Test SceneManager get_scene_list method with VideoStreamCv2/ContentDetector. """
    video = VideoStreamCv2(test_video_file)
    sm = SceneManager()
    sm.add_detector(ContentDetector())

    video_fps = video.frame_rate
    start_time = FrameTimecode('00:00:05', video_fps)
    end_time = FrameTimecode('00:00:15', video_fps)

    assert end_time.get_frames() > start_time.get_frames()

    video.seek(start_time)
    sm.auto_downscale = True
    num_frames = sm.detect_scenes(video, end_time=end_time)

    assert num_frames == (1 + end_time.get_frames() - start_time.get_frames())

    scene_list = sm.get_scene_list()
    print(scene_list)
    assert scene_list
    # Each scene is in the format (Start Timecode, End Timecode)
    assert len(scene_list[0]) == 2

    for i, _ in enumerate(scene_list):
        assert scene_list[i][0].get_frames() < scene_list[i][1].get_frames()
        if i > 0:
            # Ensure frame list is sorted (i.e. end time frame of
            # one scene is equal to the start time of the next).
            assert scene_list[i-1][1] == scene_list[i][0]


def test_save_images(test_video_file):
    """ Test scenedetect.scene_manager.save_images function.  """
    video = VideoStreamCv2(test_video_file)
    sm = SceneManager()
    sm.add_detector(ContentDetector())

    image_name_glob = 'scenedetect.tempfile.*.jpg'
    image_name_template = 'scenedetect.tempfile.$SCENE_NUMBER.$IMAGE_NUMBER'

    try:
        video_fps = video.frame_rate
        start_time = FrameTimecode('00:00:05', video_fps)
        end_time = FrameTimecode('00:00:15', video_fps)

        video.seek(start_time)
        sm.auto_downscale = True


        sm.detect_scenes(video=video, end_time=end_time)

        scene_list = sm.get_scene_list()
        assert scene_list

        image_filenames = save_images(
            scene_list=scene_list,
            video=video,
            num_images=3,
            image_extension='jpg',
            image_name_template=image_name_template)

        # Ensure images got created, and the proper number got created.
        total_images = 0
        for scene_number in image_filenames:
            for path in image_filenames[scene_number]:
                assert os.path.exists(path)
                total_images += 1

        assert total_images == len(glob.glob(image_name_glob))

    finally:
        for path in glob.glob(image_name_glob):
            os.remove(path)


class FakeCallback(object):
    """ Fake callback used for testing purposes only. Currently just stores
    the number of times the callback was invoked."""
    def __init__(self):
        self._i = 0

    def num_invoked(self):
        return self._i

    def get_callback(self):
        return lambda image, frame_num: self._callback(image, frame_num)

    def _callback(self, image, frame_num):
        self._i += 1


def test_detect_scenes_callback(test_video_file):
    """ Test SceneManager detect_scenes method with a callback function.

    Note that the API signature of the callback will undergo breaking changes in v0.6.
    """
    video = VideoStreamCv2(test_video_file)
    sm = SceneManager()
    sm.add_detector(ContentDetector())

    fake_callback = FakeCallback()

    video_fps = video.frame_rate
    start_time = FrameTimecode('00:00:05', video_fps)
    end_time = FrameTimecode('00:00:15', video_fps)
    video.seek(start_time)
    sm.auto_downscale = True

    num_frames = sm.detect_scenes(video=video, end_time=end_time, callback=fake_callback.get_callback())
    assert fake_callback.num_invoked() == (len(sm.get_scene_list()) - 1)
