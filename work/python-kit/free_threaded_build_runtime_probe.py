import sys
import sysconfig

supports_free_threading = sysconfig.get_config_var("Py_GIL_DISABLED") == 1
gil_enabled_now = sys._is_gil_enabled()
print("free_threaded_build", supports_free_threading)
print("gil_enabled_now", gil_enabled_now)
