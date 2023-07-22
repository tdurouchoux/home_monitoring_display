import time

from inky.auto import auto
import buttonshim


from home_monitoring_display.influxdb.query_influxdb import InfluxDBConnector
from home_monitoring_display import utils
from home_monitoring_display.inky.home_monitor_page import HomeMonitorPage
from home_monitoring_display.inky.day_weather_page import DayWeatherPage

PAGES_MAPPING = {
    "homemonitor": HomeMonitorPage,
    "dayweather": DayWeatherPage,
    # "citiesweather": inky_pages.CitiesWeatherPage,
    # "elecconsumption": inky_pages.ElecConsumptionPage,
    # "sysmonitor": inky_pages.SysMonitorPage,
}

# ? use buttonshim led


@buttonshim.on_press(buttonshim.BUTTON_A)
def press_a(button, pressed):
    global next_page
    next_page = "homemonitor"


@buttonshim.on_hold(buttonshim.BUTTON_A, hold_time=2)
def hold_a(button, pressed):
    global next_page
    global current_page
    global stop_refresh
    next_page = current_page
    stop_refresh = not stop_refresh


@buttonshim.on_press(buttonshim.BUTTON_B)
def press_b(button, pressed):
    global next_page
    next_page = "dayweather"


@buttonshim.on_press(buttonshim.BUTTON_C)
def press_c(button, pressed):
    global next_page
    next_page = "citiesweather"


@buttonshim.on_press(buttonshim.BUTTON_D)
def press_d(button, pressed):
    global next_page
    next_page = "elecconsumption"


@buttonshim.on_press(buttonshim.BUTTON_E)
def press_e(button, pressed):
    global next_page
    next_page = "sysmonitor"


next_page = "dayweather"
stop_refresh = False
config_file = "conf/inky_config.yaml"
connectors_config_file = "conf/connectors_config.yaml"


def main():
    global next_page
    inky_display = auto()
    inky_display.set_border(inky_display.WHITE)

    print("inky display setted up")

    inky_config = utils.load_config(config_file)
    connectors_config = utils.load_config(connectors_config_file)
    # ! I don't love this
    influxdb_connectors = {
        name: InfluxDBConnector(**config) for name, config in connectors_config.items()
    }

    page = PAGES_MAPPING[next_page](
        inky_display,
        influxdb_connectors,
        inky_config["resources_path"],
        inky_config["font"],
        **inky_config[next_page]
    )

    page.enable_auto_refresh()

    current_page = next_page
    next_page = None

    while True:
        time.sleep(0.05)

        if next_page is not None:
            if current_page != next_page:
                page.disable_auto_refresh()

                page = PAGES_MAPPING[next_page](
                    inky_display,
                    influxdb_connectors,
                    inky_config["resources_path"],
                    inky_config["font"],
                    **inky_config[next_page]
                )
                page.enable_auto_refresh()
                current_page = next_page

            elif stop_refresh:
                if page.enabled:
                    page.disable_auto_refresh()
                # print something on the screen to show that it is disabled
            else:
                page.refresh()
                if not page.enabled:
                    page.enable_auto_refresh()

            next_page = None


if __name__ == "__main__":
    main()
