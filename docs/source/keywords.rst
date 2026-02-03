Appium Keywords
===============

Get Device Id
-------------

Reads DUT configuration from ``configurations.ini``.

**Arguments**
- ``dut_name`` – Logical device name (Phone / Main / Cluster)

**Example**

.. code-block:: none

   ${device}=    Get Device Id    Phone


Start Appium Session
--------------------

Starts or reuses an Appium session for a device.

**Arguments**
- ``dut_name``

**Example**

.. code-block:: none

   Start Appium Session    Phone


Stop Appium Session
-------------------

Stops the active Appium session.

**Example**

.. code-block:: none

   Stop Appium Session


Verify Text Appium Full
----------------------

Verifies exact visible text using Appium XML.

**Arguments**
- ``expected_text``
- ``dut_name``

**Example**

.. code-block:: none

   Verify Text Appium Full    Settings    Phone


Tap By Coordinates
------------------

Taps screen using X,Y coordinates from JSON.

**Arguments**
- ``json_name``
- ``key_name``
- ``dut_name``

**Example**

.. code-block:: none

   Tap By Coordinates    coords.json    settings_icon    Phone


Tap By Text
-----------

Uses OCR to locate visible text and tap it.

**Arguments**
- ``expected_text``
- ``dut_name``

**Example**

.. code-block:: none

   Tap By Text    Bluetooth    Phone


Verify Image Element
--------------------

Verifies an image on screen using OpenCV.

**Arguments**
- ``image_name``
- ``dut_name``
- ``threshold`` (optional)

**Example**

.. code-block:: none

   Verify Image Element    wifi_icon.png    Cluster    0.85


Click By Image
--------------

Finds an image and clicks the matched area.

**Arguments**
- ``image_name``
- ``dut_name``
- ``threshold``

**Example**

.. code-block:: none

   Click By Image    play.png    Phone


Run Command
-----------

Executes shell command using Appium ``mobile:shell``.

**Arguments**
- ``command``
- ``dut_name``
- ``timeout_ms``

**Example**

.. code-block:: none

   ${out}=    Run Command    dumpsys battery    Phone


Press Key
---------

Sends Android key event.

**Arguments**
- ``keycode``
- ``dut_name``

**Example**

.. code-block:: none

   Press Key    3    Phone


Swipe Left Right
----------------

Performs safe horizontal swipe.

**Arguments**
- ``dut_name``
- ``direction`` (left/right)
- ``percent``

**Example**

.. code-block:: none

   Swipe Left Right    Phone    left


Scroll Top Bottom
-----------------

Performs safe vertical scrolling.

**Arguments**
- ``dut_name``
- ``direction`` (up/down)
- ``percent``

**Example**

.. code-block:: none

   Scroll Top Bottom    Phone    down


Start Screen Recording
----------------------

Starts Android screen recording via ADB.

**Arguments**
- ``dut_name``
- ``test_name``

**Example**

.. code-block:: none

   Start Screen Recording    Phone    Settings_Test


Stop Screen Recording
---------------------

Stops recording and pulls video locally.

**Arguments**
- ``dut_name``
- ``local_video_path``

**Example**

.. code-block:: none

   Stop Screen Recording    Phone    Results/video.mp4


Test Video
----------

Embeds recorded video in Robot report.

**Arguments**
- ``video_path``
- ``width``
- ``title``

**Example**

.. code-block:: none

   Test Video    Results/video.mp4    480    Execution Video
