import time

from inky import InkyPHAT
import buttonshim

from home_monitoring_display import inky
from home_monitoring_display.influxdb.query_influxdb import InfluxdbConnector
from home_monitoring_display import utils

PAGES_MAPPING = {
    "homemonitor": inky.home_monitor_page.HomeMonitorPage,
    # "dayweather": inky_pages.DailyWeatherPage,
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


next_page = "homemonitor"
stop_refresh = False
config_file = "conf/inky_config.yaml"
connectors_config_file = "conf/connectors_config.yaml"


def main():
    inky = InkyPHAT("yellow")
    inky_config = utils.load_config(config_file)

    connectors_config = utils.load_config(connector_config_file)
    # ! I don't love this
    influxdb_connectors = {
        name: InfluxdbConnector(**config) for name, config in connectors_config.items()
    }

    page = PAGES_MAPPING[next_page](
        inky, influxdb_connectors, inky_config["font"], **inky_config[next_page]
    )
    page.set_image()
    page.enable_auto_refresh()
    current_page = next_page

    while True:
        time.sleep(0.1)

        if current_page != next_page:
            page.disable_auto_refresh()

            page = PAGES_MAPPING[next_page](
                inky, influxdb_connectors, inky_config["font"], **inky_config[next_page]
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


if __name__ == "__main__":
    main()
