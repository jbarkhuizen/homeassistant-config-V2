# Opened Files
## File Name
packages/battery_monitoring.yaml
## File Content
# ==============================================================================
# COMPLETE BATTERY MONITORING SYSTEM
# Save as packages/battery_monitoring.yaml
# ==============================================================================

# ==============================================================================
# INPUT HELPERS FOR CONFIGURATION
# ==============================================================================
input_number:
  battery_critical_threshold:
    name: "Battery Critical Threshold"
    min: 5
    max: 25
    step: 1
    unit_of_measurement: "%"
    icon: mdi:battery-alert
    initial: 15

  battery_low_threshold:
    name: "Battery Low Threshold"
    min: 15
    max: 40
    step: 1
    unit_of_measurement: "%"
    icon: mdi:battery-low
    initial: 25

  battery_warning_threshold:
    name: "Battery Warning Threshold"
    min: 25
    max: 60
    step: 1
    unit_of_measurement: "%"
    icon: mdi:battery-medium
    initial: 40

input_boolean:
  battery_alerts_enabled:
    name: "Battery Alerts Enabled"
    initial: true
    icon: mdi:battery-alert

  battery_daily_report:
    name: "Daily Battery Report"
    initial: true
    icon: mdi:file-chart

  battery_weekend_alerts:
    name: "Weekend Alerts"
    initial: true
    icon: mdi:calendar-weekend

input_datetime:
  battery_daily_report_time:
    name: "Daily Report Time"
    has_date: false
    has_time: true
    initial: "08:00"

input_select:
  battery_notification_frequency:
    name: "Battery Notification Frequency"
    options:
      - "Immediate (Real-time)"
      - "Hourly (For critical only)"
      - "Daily (Morning summary)"
      - "Weekly (Full report only)"
    initial: "Daily (Morning summary)"
    icon: mdi:bell-outline

# ==============================================================================
# COUNTERS FOR TRACKING
# ==============================================================================
counter:
  battery_alerts_sent:
    name: "Total Battery Alerts Sent"
    icon: mdi:email-send
    step: 1

  battery_alerts_today:
    name: "Battery Alerts Today"
    icon: mdi:email-alert
    step: 1

# ==============================================================================
# TEMPLATE SENSORS FOR BATTERY MONITORING
# ==============================================================================
template:
  - sensor:
      # Battery status summary
      - name: "Battery Status Summary"
        unique_id: battery_status_summary
        state: >
          {% set ns = namespace(critical=0, low=0, warning=0, ok=0, total=0) %}
          {% for state in states.sensor if 'battery' in state.entity_id.lower() and state.state not in ['unknown', 'unavailable', 'none'] %}
            {% set battery_level = state.state | int(0) %}
            {% if battery_level > 0 %}
              {% set ns.total = ns.total + 1 %}
              {% if battery_level <= states('input_number.battery_critical_threshold') | int %}
                {% set ns.critical = ns.critical + 1 %}
              {% elif battery_level <= states('input_number.battery_low_threshold') | int %}
                {% set ns.low = ns.low + 1 %}
              {% elif battery_level <= states('input_number.battery_warning_threshold') | int %}
                {% set ns.warning = ns.warning + 1 %}
              {% else %}
                {% set ns.ok = ns.ok + 1 %}
              {% endif %}
            {% endif %}
          {% endfor %}
          {% if ns.critical > 0 %}Critical
          {% elif ns.low > 0 %}Low
          {% elif ns.warning > 0 %}Warning
          {% else %}Good
          {% endif %}
        attributes:
          critical_count: >
            {% set ns = namespace(critical=0) %}
            {% for state in states.sensor if 'battery' in state.entity_id.lower() and state.state not in ['unknown', 'unavailable', 'none'] %}
              {% set battery_level = state.state | int(0) %}
              {% if battery_level > 0 and battery_level <= states('input_number.battery_critical_threshold') | int %}
                {% set ns.critical = ns.critical + 1 %}
              {% endif %}
            {% endfor %}
            {{ ns.critical }}
          low_count: >
            {% set ns = namespace(low=0) %}
            {% for state in states.sensor if 'battery' in state.entity_id.lower() and state.state not in ['unknown', 'unavailable', 'none'] %}
              {% set battery_level = state.state | int(0) %}
              {% if battery_level > states('input_number.battery_critical_threshold') | int and battery_level <= states('input_number.battery_low_threshold') | int %}
                {% set ns.low = ns.low + 1 %}
              {% endif %}
            {% endfor %}
            {{ ns.low }}
          warning_count: >
            {% set ns = namespace(warning=0) %}
            {% for state in states.sensor if 'battery' in state.entity_id.lower() and state.state not in ['unknown', 'unavailable', 'none'] %}
              {% set battery_level = state.state | int(0) %}
              {% if battery_level > states('input_number.battery_low_threshold') | int and battery_level <= states('input_number.battery_warning_threshold') | int %}
                {% set ns.warning = ns.warning + 1 %}
              {% endif %}
            {% endfor %}
            {{ ns.warning }}
          total_batteries: >
            {% set ns = namespace(total=0) %}
            {% for state in states.sensor if 'battery' in state.entity_id.lower() and state.state not in ['unknown', 'unavailable', 'none'] %}
              {% set battery_level = state.state | int(0) %}
              {% if battery_level > 0 %}
                {% set ns.total = ns.total + 1 %}
              {% endif %}
            {% endfor %}
            {{ ns.total }}
          critical_devices: >
            {% set devices = [] %}
            {% for state in states.sensor if 'battery' in state.entity_id.lower() and state.state not in ['unknown', 'unavailable', 'none'] %}
              {% set battery_level = state.state | int(0) %}
              {% if battery_level > 0 and battery_level <= states('input_number.battery_critical_threshold') | int %}
                {% set devices = devices + [state.name + ' (' + state.state + '%)'] %}
              {% endif %}
            {% endfor %}
            {{ devices | join(', ') }}
          low_devices: >
            {% set devices = [] %}
            {% for state in states.sensor if 'battery' in state.entity_id.lower() and state.state not in ['unknown', 'unavailable', 'none'] %}
              {% set battery_level = state.state | int(0) %}
              {% if battery_level > states('input_number.battery_critical_threshold') | int and battery_level <= states('input_number.battery_low_threshold') | int %}
                {% set devices = devices + [state.name + ' (' + state.state + '%)'] %}
              {% endif %}
            {% endfor %}
            {{ devices | join(', ') }}
        icon: >
          {% set status = this.state %}
          {% if status == 'Critical' %}
            mdi:battery-alert
          {% elif status == 'Low' %}
            mdi:battery-low
          {% elif status == 'Warning' %}
            mdi:battery-medium
          {% else %}
            mdi:battery-check
          {% endif %}

      # Notification tracking sensor
      - name: "Battery Notification Stats"
        unique_id: battery_notification_stats
        state: >
          {{ states('counter.battery_alerts_sent') | int(0) }}
        attributes:
          alerts_today: >
            {{ states('counter.battery_alerts_today') | int(0) }}
          notification_status: >
            {% if is_state('input_boolean.battery_alerts_enabled', 'on') %}
              Active
            {% else %}
              Disabled
            {% endif %}

  - binary_sensor:
      # Critical battery alert
      - name: "Battery Critical Alert"
        unique_id: battery_critical_alert
        state: >
          {% for state in states.sensor if 'battery' in state.entity_id.lower() and state.state not in ['unknown', 'unavailable', 'none'] %}
            {% set battery_level = state.state | int(0) %}
            {% if battery_level > 0 and battery_level <= states('input_number.battery_critical_threshold') | int %}
              {{ true }}
            {% endif %}
          {% endfor %}
        device_class: problem
        attributes:
          critical_devices: >
            {% set devices = [] %}
            {% for state in states.sensor if 'battery' in state.entity_id.lower() and state.state not in ['unknown', 'unavailable', 'none'] %}
              {% set battery_level = state.state | int(0) %}
              {% if battery_level > 0 and battery_level <= states('input_number.battery_critical_threshold') | int %}
                {% set devices = devices + [{'name': state.name, 'level': battery_level, 'entity_id': state.entity_id}] %}
              {% endif %}
            {% endfor %}
            {{ devices }}

      # Low battery alert
      - name: "Battery Low Alert"
        unique_id: battery_low_alert
        state: >
          {% for state in states.sensor if 'battery' in state.entity_id.lower() and state.state not in ['unknown', 'unavailable', 'none'] %}
            {% set battery_level = state.state | int(0) %}
            {% if battery_level > 0 and battery_level <= states('input_number.battery_low_threshold') | int %}
              {{ true }}
            {% endif %}
          {% endfor %}
        device_class: problem
        attributes:
          low_devices: >
            {% set devices = [] %}
            {% for state in states.sensor if 'battery' in state.entity_id.lower() and state.state not in ['unknown', 'unavailable', 'none'] %}
              {% set battery_level = state.state | int(0) %}
              {% if battery_level > 0 and battery_level <= states('input_number.battery_low_threshold') | int %}
                {% set devices = devices + [{'name': state.name, 'level': battery_level, 'entity_id': state.entity_id}] %}
              {% endif %}
            {% endfor %}
            {{ devices }}

# ==============================================================================
# NOTIFICATION PLATFORMS
# ==============================================================================
notify:
  # Battery-specific email notification
  - name: battery_alerts_email
    platform: smtp
    server: smtp.gmail.com
    port: 587
    timeout: 15
    sender: jbarkhuizen@gmail.com
    encryption: starttls
    username: jbarkhuizen@gmail.com
    password: !secret gmail_token
    recipient: jbarkhuizen@gmail.com
    sender_name: "HA Battery Monitor"

  # Group notification for all channels
  - name: battery_alert_all
    platform: group
    services:
      - service: email
      - service: telegram
      - service: battery_alerts_email

# ==============================================================================
# AUTOMATION FOR BATTERY ALERTS
# ==============================================================================
automation:
  # Critical battery alert - immediate notification
  - id: battery_critical_alert
    alias: "Battery: Critical Level Alert"
    description: "Send immediate alert when any battery reaches critical level"
    trigger:
      - platform: state
        entity_id: binary_sensor.battery_critical_alert
        to: 'on'
      - platform: time_pattern
        hours: "/4"  # Check every 4 hours
    condition:
      - condition: state
        entity_id: input_boolean.battery_alerts_enabled
        state: 'on'
      - condition: state
        entity_id: binary_sensor.battery_critical_alert
        state: 'on'
    action:
      - service: counter.increment
        target:
          entity_id: counter.battery_alerts_sent
      - service: counter.increment
        target:
          entity_id: counter.battery_alerts_today
      - service: notify.email
        data:
          title: "🔋 CRITICAL: Battery Replacement Required"
          message: >
            URGENT: The following devices need immediate battery replacement:
            
            {% for device in state_attr('binary_sensor.battery_critical_alert', 'critical_devices') %}
            • {{ device.name }}: {{ device.level }}%
            {% endfor %}
            
            Critical threshold: {{ states('input_number.battery_critical_threshold') }}%
            Time: {{ now().strftime('%Y-%m-%d %H:%M:%S') }}
            
            These devices may stop working soon. Replace batteries immediately.
            
            Dashboard: http://192.168.1.30:8123/lovelace/battery-monitoring
      - service: notify.telegram
        data:
          title: "🔋 CRITICAL BATTERY ALERT"
          message: >
            ⚠️ IMMEDIATE ACTION REQUIRED ⚠️
            
            Critical battery levels detected:
            {% for device in state_attr('binary_sensor.battery_critical_alert', 'critical_devices') %}
            🔴 {{ device.name }}: {{ device.level }}%
            {% endfor %}
            
            Replace batteries NOW to prevent device failure!
      - service: persistent_notification.create
        data:
          title: "Critical Battery Alert"
          message: >
            Critical battery levels detected. Check notification for details.
          notification_id: "battery_critical"

  # Low battery alert - daily notification
  - id: battery_low_alert
    alias: "Battery: Low Level Alert"
    description: "Send daily alert for low batteries"
    trigger:
      - platform: time
        at: "09:00:00"  # Daily check at 9 AM
      - platform: state
        entity_id: binary_sensor.battery_low_alert
        to: 'on'
        for:
          hours: 1  # Only trigger if persistently low
    condition:
      - condition: state
        entity_id: input_boolean.battery_alerts_enabled
        state: 'on'
      - condition: state
        entity_id: binary_sensor.battery_low_alert
        state: 'on'
    action:
      - service: counter.increment
        target:
          entity_id: counter.battery_alerts_sent
      - service: notify.email
        data:
          title: "🔋 Battery Replacement Needed"
          message: >
            The following devices have low batteries and should be replaced soon:
            
            {% for device in state_attr('binary_sensor.battery_low_alert', 'low_devices') %}
            • {{ device.name }}: {{ device.level }}%
            {% endfor %}
            
            Low threshold: {{ states('input_number.battery_low_threshold') }}%
            Critical threshold: {{ states('input_number.battery_critical_threshold') }}%
            
            Plan to replace these batteries in the next few days.
            
            Dashboard: http://192.168.1.30:8123/lovelace/battery-monitoring
      - service: notify.telegram
        data:
          title: "🔋 Low Battery Alert"
          message: >
            Low battery levels detected:
            {% for device in state_attr('binary_sensor.battery_low_alert', 'low_devices') %}
            🟡 {{ device.name }}: {{ device.level }}%
            {% endfor %}
            
            Plan battery replacement soon.

  # Daily battery report
  - id: battery_daily_report
    alias: "Battery: Daily Status Report"
    description: "Send daily battery status summary"
    trigger:
      - platform: time
        at: "08:00:00"  # Daily report at 8 AM
    condition:
      - condition: state
        entity_id: input_boolean.battery_daily_report
        state: 'on'
    action:
      - service: notify.email
        data:
          title: "🔋 Daily Battery Status Report"
          message: >
            Battery Status Summary for {{ now().strftime('%Y-%m-%d') }}:
            
            📊 Overall Status: {{ states('sensor.battery_status_summary') }}
            📱 Total Devices: {{ state_attr('sensor.battery_status_summary', 'total_batteries') }}
            
            Status Breakdown:
            🔴 Critical (≤{{ states('input_number.battery_critical_threshold') }}%): {{ state_attr('sensor.battery_status_summary', 'critical_count') }} devices
            🟡 Low (≤{{ states('input_number.battery_low_threshold') }}%): {{ state_attr('sensor.battery_status_summary', 'low_count') }} devices
            🟠 Warning (≤{{ states('input_number.battery_warning_threshold') }}%): {{ state_attr('sensor.battery_status_summary', 'warning_count') }} devices
            
            {% if state_attr('sensor.battery_status_summary', 'critical_devices') %}
            🔴 CRITICAL DEVICES:
            {{ state_attr('sensor.battery_status_summary', 'critical_devices') }}
            
            {% endif %}
            {% if state_attr('sensor.battery_status_summary', 'low_devices') %}
            🟡 LOW BATTERY DEVICES:
            {{ state_attr('sensor.battery_status_summary', 'low_devices') }}
            
            {% endif %}
            All battery levels are being monitored continuously.
            
            Dashboard: http://192.168.1.146:8123/lovelace/battery-monitoring

  # Weekly battery maintenance reminder
  - id: battery_weekly_maintenance
    alias: "Battery: Weekly Maintenance Reminder"
    description: "Weekly reminder to check all battery levels"
    trigger:
      - platform: time
        at: "10:00:00"
        weekday:
          - mon  # Monday
    action:
      - service: notify.email
        data:
          title: "🔋 Weekly Battery Maintenance Reminder"
          message: >
            Weekly Battery Maintenance Check:
            
            📋 Tasks to complete:
            1. Review battery dashboard for any declining levels
            2. Check physical condition of battery-powered devices
            3. Test functionality of critical devices
            4. Order replacement batteries for upcoming needs
            
            📊 Current Status: {{ states('sensor.battery_status_summary') }}
            📱 Total Devices Monitored: {{ state_attr('sensor.battery_status_summary', 'total_batteries') }}
            
            Access your battery dashboard: http://192.168.1.30:8123/lovelace/battery-monitoring
            
            Stay proactive with battery maintenance!

  # Reset daily counter
  - id: battery_reset_daily_counter
    alias: "Battery: Reset Daily Counter"
    trigger:
      - platform: time
        at: "00:00:01"
    action:
      - service: counter.reset
        target:
          entity_id: counter.battery_alerts_today

# ==============================================================================
# SCRIPTS FOR MANUAL ACTIONS
# ==============================================================================
script:
  battery_emergency_alert:
    alias: "Emergency Battery Alert"
    description: "Send emergency alert for specific battery"
    fields:
      entity_id:
        description: "Entity ID of the battery sensor"
        required: true
      device_name:
        description: "Friendly name of the device"
        required: true
    sequence:
      - service: notify.battery_alert_all
        data:
          title: "🚨 EMERGENCY: {{ device_name }} Battery Critical"
          message: >
            EMERGENCY BATTERY ALERT
            
            Device: {{ device_name }}
            Battery Level: {{ states(entity_id) }}%
            Entity: {{ entity_id }}
            Time: {{ now().strftime('%Y-%m-%d %H:%M:%S') }}
            
            This device requires IMMEDIATE attention!

  battery_test_notifications:
    alias: "Test Battery Notifications"
    description: "Test all battery notification channels"
    sequence:
      - service: notify.email
        data:
          title: "🧪 Battery Notification Test - Email"
          message: >
            This is a test of your battery monitoring email notifications.
            
            If you receive this message, email notifications are working correctly.
            
            Test performed: {{ now().strftime('%Y-%m-%d %H:%M:%S') }}
      
      - service: notify.telegram
        data:
          title: "🧪 Battery Notification Test"
          message: "This is a test of your battery monitoring Telegram notifications."
      
      - service: persistent_notification.create
        data:
          title: "Battery Notification Test Complete"
          message: "All battery notification channels have been tested."
          notification_id: "battery_test_{{ now().strftime('%Y%m%d_%H%M') }}"
# Opened Files
## File Name
custom_components/battery_discovery.py
## File Content

# Opened Files
## File Name
readme.md
## File Content
# Home Assistant Configuration V2

This repository contains my Home Assistant configuration files.

## System Information
- **Home Assistant Version**: Latest (Auto-updating)
- **Installation Type**: Home Assistant OS
- **Hardware**: [Your hardware details]
- **Static IP**: 192.168.1.30:8123

## Installed Add-ons
- InfluxDB
- Node-RED
- Grafana
- Tailscale
- AdGuard Home
- Duck DNS
- Glances
- Mosquitto Broker
- Spotify Connect
- Studio Code Server

## Connected Devices
- Multiple SONOFF devices
- TUYA devices
- 2x 8kW Sunsynk inverters
- [Add other devices as needed]

## Security Notes
- All sensitive information is stored in `secrets.yaml` (not committed)
- Use `secrets.yaml.example` as a template
- Database files and logs are excluded from version control

## Installation
1. Copy `secrets.yaml.example` to `secrets.yaml`
2. Fill in your actual values in `secrets.yaml`
3. Restart Home Assistant

## Backup Strategy
- Local backups configured
- Cloud backups enabled
- Configuration versioned in Git

## Support
For issues with this configuration, please create an issue in this repository.
# Opened Files
## File Name
packages/notification.yaml
## File Content
notify:
  - name: email
    platform: smtp
    server: smtp.gmail.com
    port: 587  # Adjust as needed - common ports are 587 (TLS) or 465 (SSL)
    timeout: 15
    sender: jbarkhuizen@gmail.com
    encryption: starttls  # Options: starttls, ssl
    username: jbarkhuizen@gmail.com
    password: !secret gmail_token
    recipient: jbarkhuizen@gmail.com
    sender_name: Home Assistant Notification Alert
#xxxxxxxxxxxxxxxxxxxxxxxxxxxXXXXXXXXXXXXXXXXXXXXXXXXXxxxxxxxxxxxxxxxxxxxxxxxxxxx
  - name: email_alerts_speedtest
    platform: smtp
    server: smtp.gmail.com
    port: 587  # Adjust as needed - common ports are 587 (TLS) or 465 (SSL)
    timeout: 15
    sender: jbarkhuizen@gmail.com
    encryption: starttls  # Options: starttls, ssl
    username: jbarkhuizen@gmail.com
    password: !secret gmail_token
    recipient: jbarkhuizen@gmail.com
    sender_name: "Home Assistant Speed Monitor"  
#xxxxxxxxxxxxxxxxxxxxxxxxxxxXXXXXXXXXXXXXXXXXXXXXXXXXxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Opened Files
## File Name
packages/influxdb.yaml
## File Content
# InfluxDB Configuration with System Monitoring
# File: /config/packages/influxdb.yaml

influxdb:  
    host: localhost
    port: 8086
    database: home_assistant
    username: !secret influxdb_username  # Move to secrets.yaml
    password: !secret influxdb_password  # Move to secrets.yaml
    max_retries: 3
    default_measurement: state
    include:
      domains:
        - sensor
        - binary_sensor
      entity_globs:
        # Your Sunsynk/Deye inverters
        - "sensor.deyeinvertermaster_*"
        - "sensor.deyeinverterslave_*"
        # Prepaid meter
        - "sensor.prepaid_*"
        - "input_number.prepaid_*"
        # Energy monitoring
        - "sensor.*energy*"
        - "sensor.*power*"
        - "sensor.*battery*"
        # Speed test entities
        - "sensor.cloudflare_speed_test_*"
        - "sensor.speedtest_*"
        - "binary_sensor.speedtest_*"
        # System monitoring
        - "sensor.processor_*"
        - "sensor.memory_*"
        - "sensor.disk_*"
        - "sensor.swap_*"
        - "sensor.system_*"
        - "sensor.load_*"
        - "sensor.throughput_*"
        - "sensor.packets_*"
        - "sensor.ipv4_*"
        - "sensor.last_boot"
        - "binary_sensor.system_*"
        - "sensor.cpu_usage_*"
        - "sensor.memory_usage_*"
        # Battery Management
        - "sensor.*battery*"
        - "sensor.battery_status_summary"
        - "binary_sensor.battery_*_alert"
# ==============================================================================
    # Exclude noisy entities
# ==============================================================================
    exclude:
      entities:
        - sensor.time
        - sensor.date
      entity_globs:
        - "automation.*"
# ==============================================================================
    # Add tags for better organization
# ==============================================================================
    tags:
      source: home_assistant
      location: pretoria
      system: solar_monitoring
