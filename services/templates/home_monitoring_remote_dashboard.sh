#!/bin/bash
HOME_MONITORING_DISPLAY_DIR='<path_to_dir>/home_monitoring_display'
PYTHON_POETRY='<python_path>'
PANEL_DASHBOARDS_DIR=$HOME_MONITORING_DISPLAY_DIR/home_monitoring_display/panel
CONF_DIR=$HOME_MONITORING_DISPLAY_DIR/conf

export PANEL_OAUTH_KEY=<oauth_key>
export PANEL_OAUTH_SECRET=<oauth_secret>
export PANEL_COOKIE_SECRET=$($PYTHON_POETRY -m panel secret)

$PYTHON_POETRY -m panel serve \
$PANEL_DASHBOARDS_DIR/streaming_dashboard.py \
$PANEL_DASHBOARDS_DIR/analytics_dashboard.py \
$PANEL_DASHBOARDS_DIR/electrical_consumption.py \
--port <port> \
--allow-websocket-origin=<remote_ip>:<port> \
--oauth-provider=<oauth_provider> \
--reuse-sessions \
--admin \
--args -c $CONF_DIR