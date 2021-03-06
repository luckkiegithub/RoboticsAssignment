#! /usr/bin/python

# Import the core Python modules for ROS and to implement ROS Actions:
import rospy
import actionlib

# Import some image processing modules:
#import cv2
#from cv_bridge import CvBridge

# Import all the necessary ROS message types:
#from com2009_actions.msg import CameraSweepFeedback, CameraSweepResult, CameraSweepAction
#from sensor_msgs.msg import CompressedImage
from com2009_actions.msg import SearchFeedback, SearchResult, SearchAction

from sensor_msgs.msg import LaserScan

# Import some other modules from within this package
from move_tb3 import MoveTB3
from tb3_odometry import TB3Odometry

# Import some other useful Python Modules
import numpy as np
from math import radians
import datetime as dt
import os

class AvoidServer(object):
    feedback = SearchFeedback() 
    result = SearchResult()

    def __init__(self):
        self.actionserver = actionlib.SimpleActionServer("/obstacle_avoid_action_server", 
            SearchAction, self.action_server_launcher, auto_start=False)
        self.actionserver.start()

        #self.base_image_path = '/home/student/myrosdata/week5_images'
        self.camera_subscriber = rospy.Subscriber("/scan",
            LaserScan, self.scan_callback)
        #self.cv_image = CvBridge()

        self.robot_controller = MoveTB3()
        self.robot_odom = TB3Odometry()
    
    def scan_callback(self, scan_data):
        left_arc = scan_data.ranges[0:21]
        right_arc = scan_data.ranges[-20:]

        front_arc = np.array(left_arc[::-1] + right_arc[::-1])

        arc_angles = np.arange(-20, 21)
        
        self.min_distance = front_arc.min()
        self.object_angle = arc_angles[np.argmin(front_arc)]
    
    def action_server_launcher(self, goal):
        r = rospy.Rate(10)

        #self.robot_controller.set_move_cmd(linear=goal.fwd_velocity)

       # self.robot_controller.set_move_cmd(linear=1, angular=0.1)
        #self.robot_controller.publish()

        time = 0
        while True:

            

            if self.min_distance <= 0.6:
                self.robot_controller.set_move_cmd(linear=0.1, angular=0.5)
            else:
                self.robot_controller.set_move_cmd(linear=0.1, angular=0.0)
            


            """
            if abs(self.object_angle - self.robot_odom.yaw) < 0.1:
                if self.object - self.robot_odom.yaw < 0:
                    self.robot_controller.set_move_cmd(linear=0.1, angular=-0.6)
                else:
                    self.robot_controller.set_move_cmd(linear=0.1, angular=0.6)

                #self.robot_controller.set_move_cmd(linear=0.1, angular=0.2)
            else:
                self.robot_controller.set_move_cmd(linear=0.1, angular=0.0)
            """
            self.robot_controller.publish()

            time  = time + 1

        

        




        


        """
        success = True
        if goal.sweep_angle <= 0 or goal.sweep_angle > 180:
            print("Invalid sweep_angle.  Select a value between 1 and 180 degrees.")
            success = False
        if goal.image_count <=0:
            print("I can't capture a negative number of images!")
            success = False
        elif goal.image_count > 50:
            print("Woah, too many images! I can do a maximum of 50.")
            success = False

        if not success:
            self.actionserver.set_aborted()
            return

        print("Request to capture {} images over a {} degree sweep".format(goal.image_count, goal.sweep_angle))

        # calculate the angular increments over which to capture images:
        ang_incs = goal.sweep_angle/float(goal.image_count)
        print("Capture an image every {:.3f} degrees".format(ang_incs))

        turn_vel = 0.2 # rad/s
        full_sweep_time = radians(goal.sweep_angle)/abs(turn_vel)

        print("The full sweep will take {:.5f} seconds".format(full_sweep_time))

        # set the robot velocity:
        self.robot_controller.set_move_cmd(0.0, turn_vel)
        
        # Get the current robot odometry (yaw only):
        ref_yaw = self.robot_odom.yaw
        start_yaw = self.robot_odom.yaw

        # Get the current date and time and create a timestamp string of it
        # (to use when we construct the image filename):
        start_time = dt.datetime.strftime(dt.datetime.now(),'%Y%m%d_%H%M%S')
        
        i = 0
        while i < goal.image_count:
            self.robot_controller.publish()
            # check if there has been a request to cancel the action mid-way through:
            if self.actionserver.is_preempt_requested():
                rospy.loginfo('Cancelling the camera sweep.')
                self.actionserver.set_preempted()
                # stop the robot:
                self.robot_controller.stop()
                success = False
                # exit the loop:
                break
            
            if abs(self.robot_odom.yaw - ref_yaw) >= ang_incs:
                # increment the image counter
                i += 1
                
                # populate the feedback message and publish it:
                rospy.loginfo('Captured image {}'.format(i))
                self.feedback.current_image = i
                self.feedback.current_angle = abs(self.robot_odom.yaw)
                self.actionserver.publish_feedback(self.feedback)

                # update the reference odometry:
                ref_yaw = self.robot_odom.yaw

                # save the most recently captured image:
                cv2.imwrite(os.path.join(self.base_image_path, "{}_img{:03.0f}.jpg".format(start_time, i)), 
                    self.current_camera_image)
        
        if success:
            rospy.loginfo('Camera sweep completed sucessfully.')
            self.result.image_path = self.base_image_path
            self.actionserver.set_succeeded(self.result)
            self.robot_controller.stop()
        """
            
if __name__ == '__main__':
    rospy.init_node('camera_sweep_action_server')
    AvoidServer()
    rospy.spin()
