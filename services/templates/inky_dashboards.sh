#!/bin/bash
HOME_MONITORING_DISPLAY_DIR='<path_to_dir>/home_monitoring_display'
PYTHON_POETRY='<python_path>'

export OPENWEATHER_API_KEY=<openweather_api_key>

cd $HOME_MONITORING_DISPLAY_DIR
$PYTHON_POETRY $HOME_MONITORING_DISPLAY_DIR/home_monitoring_display/inky/inky_controller.py