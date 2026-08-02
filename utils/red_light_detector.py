import cv2
import time
import os
import sys

# === 关键修复：自动把项目根目录加入路径 ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equipment_health.settings')

import django

django.setup()

from alerts.alerts_models import Alert
from core.core_models import Equipment


def detect_red_light(camera_id=0, interval=1):
    """
    OpenCV红灯自动检测脚本（已修复路径问题）
    输入：camera_id=0（内置摄像头）或1（外接USB）
    输出：检测到红灯 → 自动创建报警记录
    """
    cap = cv2.VideoCapture(camera_id)
    print("🚨 红灯检测已启动！按 q 键退出...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ 摄像头打开失败，请检查camera_id")
            break

        # 红灯检测（双范围，更准）
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_red1 = (0, 100, 100)
        upper_red1 = (10, 255, 255)
        lower_red2 = (170, 100, 100)
        upper_red2 = (180, 255, 255)

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)

        if cv2.countNonZero(mask) > 8000:  # 红灯面积足够大
            # 自动匹配第一个设备（你后面可以改成具体设备名）
            equip = Equipment.objects.first()
            if equip:
                Alert.objects.create(
                    equipment=equip,
                    alert_type='red_light',
                    desc='摄像头实时检测到红灯报警！（自动记录）'
                )
                print(f"🚨 红灯报警已自动记录！设备：{equip.name}")

        cv2.imshow('Red Light Detector - 按q退出', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(interval)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_red_light(camera_id=0, interval=1)  # 改成1试外接摄像头