#!/usr/bin/python

import sys
import numpy as np 
import cv2
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
import rospy
from move_to_pose import GoToPose
from std_msgs.msg import Int32, String
from ar_track_alvar_msgs.msg import AlvarMarkers
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from tbotnav.msg import StringArray
from tf.transformations import quaternion_from_euler, euler_from_quaternion
from math import pi, radians, atan, sqrt, cos, sin
from face_recog import FaceRecognition

class MoveTbot:
    def __init__(self):
        self.node_name = "move_tbot"
        rospy.init_node(self.node_name)

        rospy.on_shutdown(self._shutdown)

        self.bridge = CvBridge()
        self.turn = Twist()
        self.move = GoToPose()
        # self.face_recog_file = FaceRecognition()
        # self.get_person_data = GetPersonData()
        self.qr_data = []
        self.all_face_names = []
        self.face_names = []
        self.counter = 0

        self.qr_sub = rospy.Subscriber('ar_pose_marker', AlvarMarkers, self.qr_callback)
        self.odom_sub = rospy.Subscriber('odom', Odometry, self.odom_callback)
        self.num_fingers_sub = rospy.Subscriber('num_fingers', Int32, self.num_fingers_callback)
        # self.hand_img_sub = rospy.Subscriber('hand_img', Image, self.hand_img_callback)
        # self.face_img_sub = rospy.Subscriber('face_img', Image, self.face_img_callback)
        self.face_name_sub = rospy.Subscriber('face_names', StringArray, self.face_names_callback)
        self.all_face_names_sub = rospy.Subscriber('all_face_names', StringArray, self.all_face_names_callback)

        self.turn_pub = rospy.Publisher('cmd_vel_mux/input/navi', Twist, queue_size=10)
        self.rate = rospy.Rate(10)

        while not rospy.is_shutdown():
            self.run_tbot_routine()

    def run_tbot_routine(self):
        begin = 0

        while begin != 5:
            rospy.loginfo("Gesture '5' to begin OR '4' to exit")
            rospy.sleep(3)
            self.determine_gesture()
            begin = self.detected_gesture
            rospy.sleep(2)
            if begin == 4:
                rospy.signal_shutdown('Terminating...')
                sys.exit(0)

        rospy.loginfo("You gestured %d", self.detected_gesture)
        rospy.sleep(1)

        if self.counter == 0:
                rospy.loginfo("Initializing...Rotating 360 deg...")
                self.rotate_tbot(360.0+120.0)
                rospy.sleep(2)
        rospy.loginfo("Gesture '3' to enter Station-Finder Mode... OR")
        rospy.loginfo("Gesture '5' to enter Person-Finder Mode...")
        rospy.sleep(2)

        self.determine_gesture()
        rospy.loginfo("You gestured %d", self.detected_gesture)
        rospy.sleep(1)

        # if self.detected_gesture == 3:  
        

        # if self.counter == 0:
        #     rospy.loginfo("Rotating 360 deg...")
        #     self.rotate_tbot(360.0+120.0)
        #     rospy.sleep(3)
        if self.detected_gesture == 3:
            rospy.loginfo("Entering station-finder mode...")
            rospy.sleep(2)
            count=0
            while count < 3:
                rospy.loginfo("Which station would you like me to move?")
                rospy.sleep(2)

                self.determine_gesture()
                station_id = self.detected_gesture

                if station_id > 1:
                    rospy.loginfo("You gestured %d", self.detected_gesture)
                    rospy.sleep(1)
                    rospy.loginfo("Looking for station %d...", self.detected_gesture)
                    
                    station_loc = self.find_station(station_id)
                    if station_loc != 0:
                        x1 = station_loc[0]
                        y1 = station_loc[1]
                        d1 = sqrt(x1**2 + y1**2)
                        th = atan(y1/x1)
                        d2 = d1 - 0.45
                        x2 = d2*cos(th)
                        y2 = d2*sin(th)
                        if x1 < 0 and y1<0:
                            x2 = -x2
                            y2 = -y2
                        rospy.loginfo("Moving to station %d...", station_id)
                        # if station_loc[0]<0:
                        #     goal_x = station_loc[0] + 0.3
                        # else:
                        #     goal_x = station_loc[0] - 0.3
                        # if station_loc[1]<0:
                        #     goal_y = station_loc[1] + 0.1
                        # else:
                        #     goal_y = station_loc[1] - 0.1
                        # # goal_y = station_loc[1]
                        self.move_tbot(x2, y2)
                        count = 3
                    else:
                        rospy.loginfo("Couldn't find station, try again!")
                        count += 1
                        if count == 3:
                            rospy.loginfo("Aborting mission...")
        
            self.detected_gesture = 0;

        if self.detected_gesture == 5:  
            rospy.loginfo("Entering person-finder mode...")
            rospy.sleep(1)
            rospy.loginfo("Gathering person data...")

            # rospy.loginfo("Rotating 360 deg...")
            # self.rotate_tbot(360.0+120.0)
            # rospy.sleep(3)

            person_data = self.all_face_names
            rospy.sleep(2)
            # print person_data
            # person_data = [abhi, mikhail, tanay]
            total_person_data = len(person_data)
            rospy.loginfo("Who would you like me to find?") 
            for i in range(total_person_data):           
                rospy.loginfo("%d -- %s", i+2, person_data[i])            
            # rospy.loginfo("3 -- %s", person_data[len-2])            
            # rospy.loginfo("4 -- %s", person_data[len-3])            
            # rospy.loginfo("5 -- %s", person_data[len-4])
            rospy.sleep(4)
            self.determine_gesture()

            person_id = self.detected_gesture
            
            rospy.loginfo("You gestured %d", self.detected_gesture)
            rospy.sleep(3)
            # person_data = self.get_person_data.get_data()
            if person_id > 1:
                rospy.loginfo("Looking for %s...", person_data[person_id-2])                
                name = person_data[person_id-2]

                count=2
                found=False
                while found != True and count < 6:               
                    station_loc = self.find_station(count)
                    if station_loc:
                        x1 = station_loc[0]
                        y1 = station_loc[1]
                        d1 = sqrt(x1**2 + y1**2)
                        th = atan(y1/x1)
                        d2 = d1 - 0.45
                        x2 = d2*cos(th)
                        y2 = d2*sin(th)
                        if x1 < 0 and y1<0:
                            x2 = -x2
                            y2 = -y2
                        rospy.loginfo("Moving to station %d", count)
                        # if count == 1:
                        #     goal_x, goal_y = 0.0, 0.0
                        # if station_loc[0]<0:
                        #     goal_x = station_loc[0] + 0.3
                        # else:
                        #     goal_x = station_loc[0] - 0.3
                        # if station_loc[1]<0:
                        #     goal_y = station_loc[1] + 0.3
                        # else:
                        #     goal_y = station_loc[1] - 0.3
                        # goal_y = station_loc[1]
                        self.move_tbot(x2, y2)

                        found = self.find_person(name)
                        rospy.sleep(1)
                        if found:
                            rospy.loginfo("I found %s !", name)
                            rospy.sleep(2)
                            self.rotate_tbot(360.0*2)
                            rospy.sleep(10)
                            
                    else:
                        rospy.loginfo("Couldn't find station. Searching for next station...")

                    count += 1  
            else:
                rospy.loginfo("Did not understand you, please try again")

        # station_loc = self.find_station(3)
        # print station_loc
        # # goal_x = station_loc[0]
        # # goal_y = station_loc[1]
        # x1 = station_loc[0]
        # y1 = station_loc[1]
        # d1 = sqrt(x1**2 + y1**2)
        # th = atan(y1/x1)
        # d2 = d1 - 0.45
        # x2 = d2*cos(th)
        # y2 = d2*sin(th)
        # if x1 < 0 and y1<0:
        #     x2 = -x2
        #     y2 = -y2
        # print th
        # print x1, y1
        # print x2, y2
        # self.move_tbot(x2, y2)

        # # station_loc = self.qr_tag_loc(3)
        
        # rospy.sleep(20)
        self.counter += 1


    def qr_callback(self, data):
        self.qr_data = data.markers

    def odom_callback(self, data):
        self.odom_orient = data.pose.pose.orientation

    def num_fingers_callback(self, data):
        self.num_fingers = data.data

    def hand_img_callback(self, ros_image):
        try:
            self.hand_img = self.bridge.imgmsg_to_cv2(ros_image, "bgr8")
        except CvBridgeError, e:
            print e

        # cv2.imshow("Hand Image", self.hand_img)
        # cv2.waitKey(3)

    def face_img_callback(self, ros_image):
        try:
            self.face_img = self.bridge.imgmsg_to_cv2(ros_image, "bgr8")
        except CvBridgeError, e:
            print e

        # cv2.imshow("Face Image", self.face_img)
        # cv2.waitKey(3)

    def face_names_callback(self, data):
        self.face_names = data.data
        # print self.face_names

    def all_face_names_callback(self, data):
        self.all_face_names = data.data
        # print self.all_face_names

    def rotate_tbot(self, deg, speed=45.0):
        num = int(deg/45.0)
        for i in range(num*10):
            self.turn.angular.z = radians(45.0)
            self.turn_pub.publish(self.turn)
            self.rate.sleep()

    def determine_gesture(self): 
        rospy.loginfo("Position your gesture infront of camera.")
        # cv2.imshow("Hand Image", self.hand_img)
        # cv2.waitKey(3) 
        rospy.sleep(3) 
        rospy.loginfo("Detecting gesture...")
        # rospy.sleep(2)      
        a = []  
        
        for i in range(6):
            a.append(self.num_fingers)
            rospy.loginfo("Detected fingers: %d", a[i])
            rospy.sleep(0.3)

        self.detected_gesture = max(set(a), key=a.count)

    def find_station(self, station_id):
        station_loc = []
        if station_id < 2:
            return [0.0, 0.0]
        station_loc = self.qr_tag_loc(station_id)
        count=0
        while not station_loc:
            if count == 12:
                break
            self.rotate_tbot(90.0)
            rospy.sleep(4)
            station_loc = self.qr_tag_loc(station_id)
            # print station_loc
            # rospy.sleep(3)
            count += 1
        return station_loc

    def qr_tag_loc(self, qr_id):
        # if qr_id == 1:
        #     return [0.0, 0.0]

        if self.qr_data:
            for i in range(len(self.qr_data)):
                if self.qr_data[i].id == qr_id:
                    # print [self.qr_data[i].pose.pose.position.x, self.qr_data[i].pose.pose.position.y]
                    return [self.qr_data[i].pose.pose.position.x, self.qr_data[i].pose.pose.position.y]
        else:
            return []

    def find_person(self, name):
        # cv2.imshow("Face Image", self.face_img)
        # cv2.waitKey(3)

        count=0
        found = False
        while count < 6 and found != True:
            for i in range(len(self.face_names)):
                if self.face_names[i] == name:
                    print self.face_names[i]
                    return True
                    break
            count += 1
            self.rotate_tbot(180.0, 45.0/2)
            rospy.sleep(5)
            # print count
        return found
        
    def move_tbot(self, goal_x, goal_y):
        self.move.move_to_pose(goal_x, goal_y)

    def _shutdown(self):
        rospy.loginfo("Shutting down node...")

if __name__ == '__main__':
    try:
        MoveTbot()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("Exception thrown")