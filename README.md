# C4DPlanarComponents
Planar Components script for Cinema 4D

This script is based on the original tutorial available in the video: https://www.youtube.com/watch?v=ieN5SyGJwIw&t=26s

## Prerequisites

The script requires the **NumPy** library. To install it, you first need to have **pip** (Python's package installer) installed. The `c4d_install_pip_numpy` script will download and install `pip` for you, and then use it to install **NumPy**.

### Installation Steps

1. **Install `pip` and NumPy**:
   - Copy the appropriate installation script (`c4d_install_pip_numpy2.cmd` for Python 2 or `c4d_install_pip_numpy3.cmd` for Python 3) to the directory where `python.exe` is located.
   
   - For **Python 2** (Cinema 4D R22 and earlier), the path might look like:
     ```
     C:\Program Files\Maxon\Cinema 4D R22\resource\modules\python\libs\python27.win64.framework
     ```
   
   - For **Python 3** (Cinema 4D R23 and above), the path might look like:
     ```
     C:\Program Files\Maxon\Cinema 4D R26\resource\modules\python\libs\python39.win64.framework
     ```

   - Run the script `c4d_install_pip_numpy2.cmd` (for Python 2) or `c4d_install_pip_numpy3.cmd` (for Python 3). This will download and install **pip**, and then use it to install the **NumPy** library.

2. **Run the Script**:
   - Once **NumPy** is installed, open Cinema 4D and launch the Script Editor.
   - Run the `c4dPlanarComponents.py` script from the Script Editor.


https://github.com/user-attachments/assets/0384a276-d42e-4e2b-bfa3-37151a9542ae
