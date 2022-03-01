# -*- coding: utf-8 -*-
#
#         PySceneDetect: Python-Based Video Scene Detector
#   ---------------------------------------------------------------
#     [  Site: http://www.bcastell.com/projects/PySceneDetect/   ]
#     [  Github: https://github.com/Breakthrough/PySceneDetect/  ]
#     [  Documentation: http://pyscenedetect.readthedocs.org/    ]
#
# Copyright (C) 2014-2022 Brandon Castellano <http://www.bcastell.com>.
#
# PySceneDetect is licensed under the BSD 3-Clause License; see the included
# LICENSE file, or visit one of the above pages for details.
#
# This software may also invoke mkvmerge or FFmpeg, if available.
#
# FFmpeg is a trademark of Fabrice Bellard.
# mkvmerge is Copyright (C) 2005-2016, Matroska.
#
# Certain distributions of PySceneDetect may include the above software;
# see the included LICENSE-FFMPEG and LICENSE-MKVMERGE files. If using a
# source distribution, these programs can be obtained from following URLs
# (note that mkvmerge is a part of the MKVToolNix package):
#
#     FFmpeg:   [ https://ffmpeg.org/download.html ]
#     mkvmerge: [ https://mkvtoolnix.download/downloads.html ]
#
# Also note that Linux users can likely obtain them from their package
# manager (e.g. `sudo apt-get install ffmpeg`).
#
# Once installed, ensure the program can be accessed system-wide by calling
# the `mkvmerge` or `ffmpeg` command from a terminal/command prompt.
# PySceneDetect will automatically use whichever program is available on
# the computer, depending on the specified command-line options.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
""" ``scenedetect.video_splitter`` Module

The `scenedetect.video_splitter` module contains functions to split videos
with a scene list using external tools (e.g. `mkvmerge`, `ffmpeg`), as well
as functions to check if the tools are available.

These programs can be obtained from following URLs (note that mkvmerge is a part mkvtoolnix):

 * FFmpeg:   [ https://ffmpeg.org/download.html ]
 * mkvmerge: [ https://mkvtoolnix.download/downloads.html ]

If you are a Linux user, you can likely obtain the above programs from your
package manager (e.g. `sudo apt-get install ffmpeg`).

Once installed, ensure the program can be accessed system-wide by calling
the `mkvmerge` or `ffmpeg` command from a terminal/command prompt.
PySceneDetect will automatically use whichever program is available on
the computer, depending on the specified command-line options.
"""

import logging
import subprocess
import math
import time
from typing import Iterable, Optional, Tuple
from string import Template

from scenedetect.frame_timecode import FrameTimecode
from scenedetect.platform import tqdm, invoke_command, CommandTooLong, get_file_name


logger = logging.getLogger('pyscenedetect')

FrameTimecodePair = Tuple[FrameTimecode, FrameTimecode]

COMMAND_TOO_LONG_STRING = '''
Cannot split video due to too many scenes (resulting command
is too large to process). To work around this issue, you can
split the video manually by exporting a list of cuts with the
`list-scenes` command.
See https://github.com/Breakthrough/PySceneDetect/issues/164
for details.  Sorry about that!
'''

##
## Command Availability Checking Functions
##


def is_mkvmerge_available():
    # type: () -> bool
    """ Is mkvmerge Available: Gracefully checks if mkvmerge command is available.

    Returns:
        (bool) True if the mkvmerge command is available, False otherwise.
    """
    ret_val = None
    try:
        ret_val = subprocess.call(['mkvmerge', '--quiet'])
    except OSError:
        return False
    if ret_val is not None and ret_val != 2:
        return False
    return True


def is_ffmpeg_available():
    # type: () -> bool
    """ Is ffmpeg Available: Gracefully checks if ffmpeg command is available.

    Returns:
        (bool) True if the ffmpeg command is available, False otherwise.
    """
    ret_val = None
    try:
        ret_val = subprocess.call(['ffmpeg', '-v', 'quiet'])
    except OSError:
        return False
    if ret_val is not None and ret_val != 1:
        return False
    return True


##
## Split Video Functions
##


def split_video_mkvmerge(input_video_path: str,
                         scene_list: Iterable[FrameTimecodePair],
                         output_file_template: str = '$VIDEO_NAME.mkv',
                         video_name: Optional[str] = None,
                         show_output: bool = False):
    """ Calls the mkvmerge command on the input video(s), splitting it at the
    passed timecodes, where each scene is written in sequence from 001.

    Arguments:
        input_video_path: Path to the video to be split.
        scene_list : List of scenes as pairs of FrameTimecodes denoting the start/end times.
        output_file_template: Template to use for output files. Mkvmerge always adds the suffix
            "-$SCENE_NUMBER". Can use $VIDEO_NAME as a template parameter (e.g. "$VIDEO_NAME.mkv").
        video_name (str): Name of the video to be substituted in output_file_template for
            $VIDEO_NAME. If not specified, will be obtained from the filename.
        show_output: If False, adds the --quiet flag when invoking `mkvmerge`.

    Returns:
        Return code of invoking mkvmerge (0 on success). If scene_list is empty, will
        still return 0, but no commands will be invoked.
    """

    if not scene_list:
        return 0

    logger.info('Splitting input video using mkvmerge, output path template:\n  %s',
                output_file_template)

    if video_name is None:
        video_name = get_file_name(input_video_path, include_extension=False)

    ret_val = 0
    # mkvmerge automatically appends '-$SCENE_NUMBER', so we remove it if present.
    output_file_template = output_file_template.replace('-$SCENE_NUMBER',
                                                        '').replace('$SCENE_NUMBER', '')
    output_file_name = Template(output_file_template).safe_substitute(VIDEO_NAME=video_name)

    try:
        call_list = ['mkvmerge']
        if not show_output:
            call_list.append('--quiet')
        call_list += [
            '-o', output_file_name, '--split',
            'parts:%s' % ','.join([
                '%s-%s' % (start_time.get_timecode(), end_time.get_timecode())
                for start_time, end_time in scene_list
            ]), input_video_path
        ]
        total_frames = scene_list[-1][1].get_frames() - scene_list[0][0].get_frames()
        processing_start_time = time.time()
        ret_val = invoke_command(call_list)
        if show_output:
            logger.info('Average processing speed %.2f frames/sec.',
                        float(total_frames) / (time.time() - processing_start_time))
    except CommandTooLong:
        logger.error(COMMAND_TOO_LONG_STRING)
    except OSError:
        logger.error('mkvmerge could not be found on the system.'
                     ' Please install mkvmerge to enable video output support.')
    if ret_val != 0:
        logger.error('Error splitting video (mkvmerge returned %d).', ret_val)
    return ret_val


def split_video_ffmpeg(input_video_path: str,
                       scene_list: Iterable[FrameTimecodePair],
                       output_file_template: str = '$VIDEO_NAME-Scene-$SCENE_NUMBER.mp4',
                       video_name: Optional[str] = None,
                       arg_override: str = '-c:v libx264 -preset fast -crf 21 -c:a aac',
                       show_progress: bool = False,
                       show_output: bool = False):
    """ Calls the ffmpeg command on the input video, generating a new video for
    each scene based on the start/end timecodes.

    Arguments:
        input_video_path: Path to the video to be split.
        scene_list (List[Tuple[FrameTimecode, FrameTimecode]]): List of scenes
            (pairs of FrameTimecodes) denoting the start/end frames of each scene.
        output_file_template (str): Template to use for generating the output filenames.
            Can use $VIDEO_NAME and $SCENE_NUMBER in this format, for example:
            `$VIDEO_NAME - Scene $SCENE_NUMBER.mp4`
        video_name (str): Name of the video to be substituted in output_file_template. If not
            passed will be calculated from input_video_path automatically.
        arg_override (str): Allows overriding the arguments passed to ffmpeg for encoding.
        show_progress (bool): If True, will show progress bar provided by tqdm (if installed).
        show_output (bool): If True, will show output from ffmpeg for first split.

    Returns:
        Return code of invoking ffmpeg (0 on success). If scene_list is empty, will
        still return 0, but no commands will be invoked.
    """

    if not scene_list:
        return 0

    logger.info('Splitting input video using ffmpeg, output path template:\n  %s',
                output_file_template)

    if video_name is None:
        video_name = get_file_name(input_video_path, include_extension=False)

    arg_override = arg_override.replace('\\"', '"')

    ret_val = 0
    arg_override = arg_override.split(' ')
    filename_template = Template(output_file_template)
    scene_num_format = '%0'
    scene_num_format += str(max(3, math.floor(math.log(len(scene_list), 10)) + 1)) + 'd'

    try:
        progress_bar = None
        total_frames = scene_list[-1][1].get_frames() - scene_list[0][0].get_frames()
        if show_progress and tqdm:
            progress_bar = tqdm(total=total_frames, unit='frame', miniters=1, dynamic_ncols=True)
        processing_start_time = time.time()
        for i, (start_time, end_time) in enumerate(scene_list):
            duration = (end_time - start_time)
            call_list = ['ffmpeg']
            if not show_output:
                call_list += ['-v', 'quiet']
            elif i > 0:
                # Only show ffmpeg output for the first call, which will display any
                # errors if it fails, and then break the loop. We only show error messages
                # for the remaining calls.
                call_list += ['-v', 'error']
            call_list += [
                '-nostdin', '-y', '-ss',
                str(start_time.get_seconds()), '-i', input_video_path, '-t',
                str(duration.get_seconds())
            ]
            call_list += arg_override
            call_list += [
                '-sn',
                filename_template.safe_substitute(
                    VIDEO_NAME=video_name, SCENE_NUMBER=scene_num_format % (i + 1))
            ]
            ret_val = invoke_command(call_list)
            if show_output and i == 0 and len(scene_list) > 1:
                logger.info(
                    'Output from ffmpeg for Scene 1 shown above, splitting remaining scenes...')
            if ret_val != 0:
                logger.error('Error splitting video (ffmpeg returned %d).', ret_val)
                break
            if progress_bar:
                progress_bar.update(duration.get_frames())
        if show_output:
            logger.info('Average processing speed %.2f frames/sec.',
                        float(total_frames) / (time.time() - processing_start_time))

    except CommandTooLong:
        logger.error(COMMAND_TOO_LONG_STRING)
    except OSError:
        logger.error('ffmpeg could not be found on the system.'
                     ' Please install ffmpeg to enable video output support.')
    return ret_val
