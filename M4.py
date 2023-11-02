import os
import sys
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node

# math 모듈을 import하는 부분이 누락되어있어 추가합니다.
from math import sin, cos

class AutonomousNavigation(Node):
    def __init__(self):
        super().__init__('autonomous_navigation')
        # 내비게이션 클라이언트 설정
        self.navigation_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

    def send_goal(self, x, y, theta):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.z = sin(theta / 2)
        goal_msg.pose.pose.orientation.w = cos(theta / 2)

        self.navigation_client.wait_for_server()
        self.send_goal_future = self.navigation_client.send_goal_async(goal_msg)
        self.send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected :(')
            return

        self.get_logger().info('Goal accepted :)')

        self.result_future = goal_handle.get_result_async()
        self.result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        if result:
            self.get_logger().info('Goal reached :)')
        else:
            self.get_logger().info('Goal failed :(')

def main(args=None):
    rclpy.init(args=args)
    autonomous_navigation = AutonomousNavigation()

    # 목적지 좌표 입력
    x_goal = 2.0
    y_goal = 2.0
    theta_goal = 0.0

    # 지도 저장하는 코드 부분 추가
    # SLAM 시작 후 지도 저장
    os.system('ros2 launch slam_toolbox online_async_launch.py')
    # 지도 저장 경로 설정
    map_save_directory = os.path.expanduser('~/saved_maps')
    os.makedirs(map_save_directory, exist_ok=True)
    # 지도 저장 명령 실행
    os.system(f'ros2 run nav2_map_server map_saver_cli -f {map_save_directory}/my_map')

    # 내비게이션 시작
    navigation_launch_path = os.path.join(
        get_package_share_directory('nav2_bringup'), 'launch', 'bringup_launch.py')
    os.system(f'ros2 launch {navigation_launch_path}')

    # 내비게이션 목적지로 이동
    autonomous_navigation.send_goal(x_goal, y_goal, theta_goal)

    rclpy.spin(autonomous_navigation)
    autonomous_navigation.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()