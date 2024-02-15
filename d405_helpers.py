import pyrealsense2 as rs
import numpy as np
import cv2
from d405_helpers_without_pyrealsense import *

def check_exposure(value):
    int_value = int(value)
    if (int_value < 0) or (int_value > 500000):
        raise argparse.ArgumentTypeError('The provided exposure setting, %s, is outside of the allowed range [0, 500000].' % value)
    return int_value
        

def start_d405(exposure): 
    camera_info = [{'name': device.get_info(rs.camera_info.name),
                    'serial_number': device.get_info(rs.camera_info.serial_number)}
                   for device
                   in rs.context().devices]

    print('All cameras that were found:')
    print(camera_info)
    print()

    d405_info = None
    for info in camera_info:
        if info['name'].endswith('D405'):
            d405_info = info
    if d405_info is None:
        print('D405 camera not found')
        print('Exiting')
        exit()
    else:
        print('D405 found:')
        print(d405_info)
        print()

    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_device(d405_info['serial_number'])
    
    # 1280 x 720, 5 fps
    # 848 x 480, 10 fps
    # 640 x 480, 30 fps

    #width, height, fps = 1280, 720, 5
    #width, height, fps = 848, 480, 10
    #width, height, fps = 640, 480, 30
    width, height, fps = 640, 480, 15
    config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
    config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)

    profile = pipeline.start(config)
    
    # Check the exposure argument
    if exposure not in ['low', 'medium', 'auto']:
        check_exposure(exposure)
    
    if exposure == 'auto':
        # Use autoexposre
        stereo_sensor = pipeline.get_active_profile().get_device().query_sensors()[0]
        stereo_sensor.set_option(rs.option.enable_auto_exposure, True)
    else: 
        default_exposure = 33000
        if exposure == 'low':
            exposure_value = int(default_exposure/3.0)
        elif exposure == 'medium':
            exposure_value = 30000
        else:
            exposure_value = int(exposure)
            
        stereo_sensor = pipeline.get_active_profile().get_device().query_sensors()[0]
        stereo_sensor.set_option(rs.option.exposure, exposure_value)
    
    return pipeline, profile


def get_camera_info(frame):
    intrinsics = rs.video_stream_profile(frame.profile).get_intrinsics()
    
    # from Intel's documentation
    # https://intelrealsense.github.io/librealsense/python_docs/_generated/pyrealsense2.intrinsics.html#pyrealsense2.intrinsics
    # "
    # coeffs	Distortion coefficients
    # fx	Focal length of the image plane, as a multiple of pixel width
    # fy	Focal length of the image plane, as a multiple of pixel height
    # height	Height of the image in pixels
    # model	Distortion model of the image
    # ppx	Horizontal coordinate of the principal point of the image, as a pixel offset from the left edge
    # ppy	Vertical coordinate of the principal point of the image, as a pixel offset from the top edge
    # width	Width of the image in pixels
    # "

    # out = {
    #     'dist_model' : intrinsics.model,
    #     'dist_coeff' : intrinsics.coeffs,
    #     'fx' : intrinsics.fx,
    #     'fy' : intrinsics.fy,
    #     'height' : intrinsics.height,
    #     'width' : intrinsics.width,
    #     'ppx' : intrinsics.ppx,
    #     'ppy' : intrinsics.ppy
    #     }

    camera_matrix = np.array([[intrinsics.fx, 0.0,           intrinsics.ppx],
                              [0.0          , intrinsics.fy, intrinsics.ppy],
                              [0.0          , 0.0          , 1.0]])

    distortion_model = intrinsics.model

    distortion_coefficients = np.array(intrinsics.coeffs)

    camera_info = {'camera_matrix': camera_matrix, 'distortion_coefficients': distortion_coefficients, 'distortion_model': distortion_model}
    
    return camera_info
