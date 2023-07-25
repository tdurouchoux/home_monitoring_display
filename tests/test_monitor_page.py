
from inky import InkyPHAT

from home_monitoring_display.inky.home_monitor_page import HomeMonitorPage
from home_monitoring_display import utils

inky_display = InkyPHAT("yellow")

monitor_page = HomeMonitorPage(
    inky_display
