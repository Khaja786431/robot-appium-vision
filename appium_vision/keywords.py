from appium import webdriver
from robot.api.deco import keyword
from appium.options.android import UiAutomator2Options
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
from datetime import datetime
import subprocess
import configparser
import time
import os
import json
import cv2
import shutil
import importlib.util
import pytesseract


class AppiumKeywords:
    """
    Robot Framework keyword library for Android automation using Appium.

    Capabilities:
    - Multi-DUT Appium session management
    - OCR-based text verification and tapping
    - Image-based verification and clicking using OpenCV
    - Coordinate-based tap actions
    - Android shell command execution
    - Safe swipe and scroll gestures
    - Screen recording with embedded video reporting
    """

    def __init__(self):
        """
        Initializes keyword library.
        - Loads DUT configuration from configurations.ini
        - Initializes driver dictionary
        """
        self.drivers = {}

        base_path = os.path.dirname(os.path.abspath(__file__))
        ini_path = os.path.join(base_path, "..", "Configurations", "configurations.ini")

        self.config = configparser.ConfigParser()
        self.config.read(ini_path)

        # Optional Tesseract override (recommended for PyPI users)
        tesseract_cmd = os.getenv("TESSERACT_CMD")
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Runtime dependency validation
        try:
            self._check_runtime_dependencies()
        except Exception as e:
            logger.warn(
                f"⚠️ Dependency check skipped during initialization:\n{e}"
            )

    # ---------------------------------------------------------------------
    @keyword
    def get_device_id(self, dut_name):
        """
        Returns DUT configuration section for the given DUT name.

        Arguments:
        - dut_name (str): Logical DUT name (Phone / Main / Cluster)

        Returns:
        - Config section containing device capabilities

        Fails If:
        - DUT section is not found
        """
        section = f"DUT.{dut_name}"
        if section not in self.config:
            raise Exception(f"DUT section '{section}' not found")
        return self.config[section]

    # ---------------------------------------------------------------------
    @keyword
    def start_appium_session(self, dut_name):
        """
        Starts or reuses an Appium session for the given DUT.

        Maintains one Appium driver per DUT.

        Arguments:
        - dut_name (str): Logical DUT name

        Returns:
        - Appium WebDriver instance
        """
        if dut_name in self.drivers:
            return self.drivers[dut_name]

        caps = self.get_device_id(dut_name)
        options = UiAutomator2Options().load_capabilities(caps)

        driver = webdriver.Remote(
            command_executor="http://127.0.0.1:4723",
            options=options
        )

        self.drivers[dut_name] = driver
        return driver

    # ---------------------------------------------------------------------
    @keyword
    def stop_appium_session(self):
        """
        Stops all active Appium sessions.
        """
        for driver in self.drivers.values():
            driver.quit()
        self.drivers.clear()

    # ---------------------------------------------------------------------
    @keyword
    def verify_text_appium_full(self, expected_text, dut_name):
        """
        Verifies that exact visible text is present on screen using Appium.

        Arguments:
        - expected_text (str): Exact text to verify
        - dut_name (str): Logical DUT name

        Returns:
        - True if text is found

        Fails If:
        - Text is not present
        """
        driver = self.start_appium_session(dut_name)

        elements = driver.find_elements(
            by="xpath",
            value="//*[normalize-space(@text) != '']"
        )

        visible_texts = [el.text.strip() for el in elements if el.text.strip()]

        if expected_text in visible_texts:
            logger.info(f"<b style='color:green'>Text verified:</b> {expected_text}", html=True)
            return True

        raise AssertionError(f"Exact text '{expected_text}' not found")

    # ---------------------------------------------------------------------
    @keyword
    def tap_by_coordinates(self, json_name, key_name, dut_name):
        """
        Taps on screen using X,Y coordinates from a JSON file.

        Arguments:
        - json_name (str): JSON file name
        - key_name (str): Key containing x,y values
        - dut_name (str): Logical DUT name

        Returns:
        - Success message
        """
        driver = self.start_appium_session(dut_name)
        project_root = BuiltIn().get_variable_value("${EXECDIR}")

        json_file = os.path.join(project_root, "Resources", "Coordinates", json_name)
        if not os.path.isfile(json_file):
            raise AssertionError(f"JSON file not found: {json_file}")

        with open(json_file) as f:
            data = json.load(f)

        if key_name not in data:
            raise AssertionError(f"Key '{key_name}' not found")

        x = int(data[key_name]["x"])
        y = int(data[key_name]["y"])

        driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
        return f"Tapped at ({x},{y}) on {dut_name}"

    # ---------------------------------------------------------------------
    @keyword
    def tap_by_text(self, expected_text, dut_name):
        """
        Taps on visible text using OCR instead of UI hierarchy.

        Arguments:
        - expected_text (str): Text to tap
        - dut_name (str): Logical DUT name

        Returns:
        - True if text is tapped

        Fails If:
        - Text not found via OCR
        """
        driver = self.start_appium_session(dut_name)
        output_dir = BuiltIn().get_variable_value("${OUTPUTDIR}")
        screenshot_path = os.path.join(output_dir, "ocr_screen.png")

        driver.save_screenshot(screenshot_path)
        img = cv2.imread(screenshot_path)

        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        for i, text in enumerate(ocr_data["text"]):
            if text.strip() == expected_text:
                x = ocr_data["left"][i]
                y = ocr_data["top"][i]
                w = ocr_data["width"][i]
                h = ocr_data["height"][i]

                driver.execute_script(
                    "mobile: clickGesture",
                    {"x": int(x + w / 2), "y": int(y + h / 2)}
                )
                return True

        raise AssertionError(f"Text '{expected_text}' not found via OCR")

    # ---------------------------------------------------------------------
    @keyword
    def verify_image_element(self, image_name, dut_name, threshold=0.9):
        """
        Verifies an image on screen using OpenCV template matching.

        Arguments:
        - image_name (str): Reference image
        - dut_name (str): Logical DUT name
        - threshold (float): Similarity threshold

        Returns:
        - True if image is matched
        """
        driver = self.start_appium_session(dut_name)
        project_root = BuiltIn().get_variable_value("${EXECDIR}")
        output_dir = BuiltIn().get_variable_value("${OUTPUTDIR}")

        ref_img = cv2.imread(os.path.join(project_root, "Resources", "images", image_name))
        screenshot_path = os.path.join(output_dir, f"verify_{time.time()}.png")
        driver.save_screenshot(screenshot_path)

        screen = cv2.imread(screenshot_path)
        res = cv2.matchTemplate(
            cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY),
            cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY),
            cv2.TM_CCOEFF_NORMED
        )

        _, max_val, _, _ = cv2.minMaxLoc(res)
        if max_val >= threshold:
            return True

        raise AssertionError(f"Image match failed: score={max_val:.3f}")

    # ---------------------------------------------------------------------
    @keyword
    def click_by_image(self, image_name, dut_name, threshold=0.8):
        """
        Clicks on UI element using image recognition.

        Arguments:
        - image_name (str): Reference image
        - dut_name (str): Logical DUT name
        - threshold (float): Confidence threshold

        Returns:
        - Click success message
        """
        driver = self.start_appium_session(dut_name)
        project_root = BuiltIn().get_variable_value("${EXECDIR}")
        output_dir = BuiltIn().get_variable_value("${OUTPUTDIR}")

        ref = cv2.imread(os.path.join(project_root, "Resources", "images", image_name))
        screenshot = os.path.join(output_dir, f"click_{time.time()}.png")
        driver.save_screenshot(screenshot)

        screen = cv2.imread(screenshot)
        res = cv2.matchTemplate(
            cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY),
            cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY),
            cv2.TM_CCOEFF_NORMED
        )

        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val < threshold:
            raise AssertionError("Image not found")

        h, w = ref.shape[:2]
        x = max_loc[0] + w // 2
        y = max_loc[1] + h // 2

        driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
        return f"Clicked image at ({x},{y})"

    # ---------------------------------------------------------------------
    @keyword
    def run_command(self, command, dut_name, timeout_ms=5000):
        """
        Executes Android shell command using Appium.

        Arguments:
        - command (str): Shell command
        - dut_name (str): Logical DUT name
        - timeout_ms (int): Timeout

        Returns:
        - Command output
        """
        driver = self.start_appium_session(dut_name)
        parts = command.split()

        result = driver.execute_script(
            "mobile: shell",
            {"command": parts[0], "args": parts[1:], "timeout": timeout_ms}
        )

        if isinstance(result, dict):
            return result.get("stdout", "").strip()
        return result.strip()

    # ---------------------------------------------------------------------
    @keyword
    def press_key(self, keycode, dut_name):
        """
        Presses Android hardware/system key.

        Arguments:
        - keycode (int): Android keycode
        - dut_name (str): Logical DUT name
        """
        driver = self.start_appium_session(dut_name)
        driver.execute_script(
            "mobile: shell",
            {"command": "input", "args": ["keyevent", str(keycode)]}
        )

    # ---------------------------------------------------------------------
    @keyword
    def swipe_left_right(self, dut_name, direction="left", percent=0.9):
        """
        Performs safe horizontal swipe.

        Arguments:
        - dut_name (str): Logical DUT name
        - direction (str): left / right
        - percent (float): Swipe distance
        """
        driver = self.start_appium_session(dut_name)
        size = driver.get_window_size()

        driver.execute_script(
            "mobile: scrollGesture",
            {
                "direction": direction,
                "percent": percent,
                "left": int(size["width"] * 0.1),
                "top": int(size["height"] * 0.35),
                "width": int(size["width"] * 0.8),
                "height": int(size["height"] * 0.3),
            }
        )

    # ---------------------------------------------------------------------
    @keyword
    def scroll_top_bottom(self, dut_name, direction="down", percent=0.9):
        """
        Performs safe vertical scroll.

        Arguments:
        - dut_name (str): Logical DUT name
        - direction (str): up / down
        - percent (float): Scroll distance
        """
        driver = self.start_appium_session(dut_name)
        size = driver.get_window_size()

        driver.execute_script(
            "mobile: scrollGesture",
            {
                "direction": direction,
                "percent": percent,
                "left": int(size["width"] * 0.1),
                "top": int(size["height"] * 0.15),
                "width": int(size["width"] * 0.8),
                "height": int(size["height"] * 0.7),
            }
        )

    # ---------------------------------------------------------------------
    @keyword
    def start_screen_recording(self, dut_name, test_name):
        """
        Starts Android screen recording using adb.

        Arguments:
        - dut_name (str): Logical DUT name
        - test_name (str): Test case name

        Returns:
        - Device video path
        """
        device_id = self.get_device_id(dut_name).get("device_id")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"/sdcard/{device_id}_{timestamp}_{test_name}.mp4"

        self._screen_proc = subprocess.Popen(
            ["adb", "-s", device_id, "shell", "screenrecord", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        self._device_video_path = path
        self._device_id = device_id
        return path

    # ---------------------------------------------------------------------
    @keyword
    def stop_screen_recording(self, dut_name, local_video_path):
        """
        Stops screen recording and pulls video to local system.

        Arguments:
        - dut_name (str): Logical DUT name
        - local_video_path (str): Local save path

        Returns:
        - Local video path
        """
        if self._screen_proc:
            self._screen_proc.terminate()
            self._screen_proc.wait()

        subprocess.run(
            ["adb", "-s", self._device_id, "pull", self._device_video_path, local_video_path],
            check=True
        )
        return local_video_path

    # ---------------------------------------------------------------------
    @keyword
    def Test_Video(self, video_path, width=480, title="Screen Recording"):
        """
        Embeds video in Robot Framework HTML report.

        Arguments:
        - video_path (str): MP4 file path
        - width (int): Video width
        - title (str): Video title
        """
        if not os.path.exists(video_path):
            logger.warn(f"Video not found: {video_path}")
            return

        html = f"""
        <b>{title}</b><br>
        <video width="{width}" controls>
            <source src="{video_path}" type="video/mp4">
        </video>
        """
        logger.info(html, html=True)


def _check_runtime_dependencies(self):
    """
    Performs runtime dependency checks.

    - Verifies required Python packages
    - Verifies optional system tools (adb, tesseract)
    - Logs warnings instead of crashing where possible
    """

    # -------------------------------
    # Required Python packages
    # -------------------------------
    required_packages = {
        "robotframework": "robot",
        "appium-python-client": "appium",
        "selenium": "selenium",
        "opencv-python": "cv2",
        "pytesseract": "pytesseract",
    }

    for pkg_name, import_name in required_packages.items():
        if importlib.util.find_spec(import_name) is None:
            raise RuntimeError(
                f"❌ Required dependency '{pkg_name}' is not installed.\n"
                f"Install it using: pip install {pkg_name}"
            )

    logger.info("✅ All required Python dependencies are installed")

    # -------------------------------
    # adb check (required for shell & recording)
    # -------------------------------
    if shutil.which("adb") is None:
        logger.warn(
            "⚠️ adb not found in PATH.\n"
            "Keywords using shell commands and screen recording may fail."
        )
    else:
        logger.info("✅ adb detected")

    # -------------------------------
    # Tesseract OCR check (optional)
    # -------------------------------
    tesseract_path = (
        os.getenv("TESSERACT_CMD")
        or shutil.which("tesseract")
    )

    if not tesseract_path:
        logger.warn(
            "⚠️ Tesseract OCR not found.\n"
            "OCR-based keywords (Tap By Text) will NOT work.\n"
            "Install Tesseract and set TESSERACT_CMD environment variable."
        )
    else:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        logger.info(f"✅ Tesseract OCR detected at: {tesseract_path}")
