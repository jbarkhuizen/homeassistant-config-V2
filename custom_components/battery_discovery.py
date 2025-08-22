#!/usr/bin/env python3
"""
Battery Device Discovery Script for Home Assistant
Run this script to discover all battery-powered devices in your HA setup
Results will be sent via your existing HA notification services
"""

import requests
import json
import re
import os
from datetime import datetime

# Configuration
HA_URL = "http://192.168.1.30:8123"  # Your HA URL
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI1MmI5NmRkZDE1ODk0MTY0YTA5ZTBjYTRkZDRmNTAwMCIsImlhdCI6MTc1NTg2NTkyMiwiZXhwIjoyMDcxMjI1OTIyfQ.qhwcOA9gZTBKfleSiv1LL34NYeJC_ils_6-1q6Rga8Q"  # Get from HA Profile -> Long-lived access tokens

# Notification Configuration (using your existing HA services)
NOTIFICATION_SERVICES = [
    "email",                    # Your existing email service
    "telegram",                 # Your existing telegram service
    "battery_alerts_email"      # Will be available after battery monitoring setup
]

# Headers for API requests
headers = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json"
}

def get_all_entities():
    """Get all entities from Home Assistant"""
    try:
        response = requests.get(f"{HA_URL}/api/states", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching entities: {e}")
        return []

def find_battery_entities(entities):
    """Find all battery-related entities"""
    battery_entities = []
    
    battery_patterns = [
        r'.*battery.*',
        r'.*_bat$',
        r'.*_battery_level.*',
        r'.*_battery_percentage.*',
        r'.*_battery_state.*',
        r'.*_power_source.*'
    ]
    
    for entity in entities:
        entity_id = entity.get('entity_id', '')
        
        # Check if entity matches battery patterns
        for pattern in battery_patterns:
            if re.match(pattern, entity_id, re.IGNORECASE):
                # Verify it's actually a battery sensor
                state = entity.get('state', '')
                attributes = entity.get('attributes', {})
                
                # Check if it has battery-like characteristics
                device_class = attributes.get('device_class', '')
                unit = attributes.get('unit_of_measurement', '')
                
                if (device_class == 'battery' or 
                    unit == '%' or 
                    ('battery' in entity_id.lower() and 
                     state not in ['unknown', 'unavailable', 'none', ''] and
                     state.replace('.', '').isdigit())):
                    
                    battery_info = {
                        'entity_id': entity_id,
                        'name': attributes.get('friendly_name', entity_id),
                        'state': state,
                        'unit': unit,
                        'device_class': device_class,
                        'last_updated': entity.get('last_updated', ''),
                        'device_info': get_device_info(attributes)
                    }
                    battery_entities.append(battery_info)
                break
    
    return battery_entities

def get_device_info(attributes):
    """Extract device information from attributes"""
    return {
        'model': attributes.get('model', ''),
        'manufacturer': attributes.get('manufacturer', ''),
        'sw_version': attributes.get('sw_version', ''),
        'hw_version': attributes.get('hw_version', ''),
        'via_device': attributes.get('via_device', '')
    }

def categorize_devices(battery_entities):
    """Categorize devices by type/manufacturer"""
    categories = {
        'mobile_devices': [],
        'sonoff_devices': [],
        'tuya_devices': [],
        'zigbee_devices': [],
        'other_devices': []
    }
    
    for entity in battery_entities:
        entity_id = entity['entity_id'].lower()
        manufacturer = entity['device_info'].get('manufacturer', '').lower()
        
        if 'sm_' in entity_id or 'phone' in entity_id or 'mobile' in entity_id:
            categories['mobile_devices'].append(entity)
        elif 'sonoff' in entity_id or 'sonoff' in manufacturer:
            categories['sonoff_devices'].append(entity)
        elif 'tuya' in entity_id or 'tuya' in manufacturer:
            categories['tuya_devices'].append(entity)
        elif 'zigbee' in entity_id or entity['device_info'].get('via_device'):
            categories['zigbee_devices'].append(entity)
        else:
            categories['other_devices'].append(entity)
    
    return categories

def generate_battery_config(categories):
    """Generate configuration snippets for discovered devices"""
    config = {
        'recorder_includes': [],
        'influxdb_includes': [],
        'dashboard_entities': []
    }
    
    for category, devices in categories.items():
        for device in devices:
            entity_id = device['entity_id']
            
            # Add to recorder includes
            config['recorder_includes'].append(entity_id)
            
            # Add to InfluxDB includes
            config['influxdb_includes'].append(entity_id)
            
            # Add dashboard entity
            config['dashboard_entities'].append({
                'entity': entity_id,
                'name': device['name'],
                'category': category
            })
    
    return config

def print_discovery_report(categories, config):
    """Print a detailed discovery report"""
    print("=" * 80)
    print("BATTERY DEVICE DISCOVERY REPORT")
    print("=" * 80)
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    total_devices = sum(len(devices) for devices in categories.values())
    print(f"📊 SUMMARY: Found {total_devices} battery-powered devices")
    print()
    
    for category, devices in categories.items():
        if devices:
            category_name = category.replace('_', ' ').title()
            print(f"📱 {category_name}: {len(devices)} devices")
            for device in devices:
                level = device['state']
                if level.replace('.', '').isdigit():
                    level_float = float(level)
                    if level_float <= 15:
                        status = "🔴 CRITICAL"
                    elif level_float <= 25:
                        status = "🟠 LOW"
                    elif level_float <= 40:
                        status = "🟡 WARNING"
                    else:
                        status = "🟢 GOOD"
                    print(f"   • {device['name']}: {level}% {status}")
                else:
                    print(f"   • {device['name']}: {level}")
            print()
    
    print("🔧 CONFIGURATION SNIPPETS")
    print("-" * 40)
    
    print("\n# Add to packages/battery_monitoring.yaml recorder section:")
    print("recorder:")
    print("  include:")
    print("    entities:")
    for entity in config['recorder_includes']:
        print(f"      - {entity}")
    
    print("\n# Add to packages/influxdb.yaml:")
    print("influxdb:")
    print("  include:")
    print("    entities:")
    for entity in config['influxdb_includes']:
        print(f"      - {entity}")
    
    print("\n# Dashboard entities found:")
    for entity in config['dashboard_entities']:
        print(f"# {entity['category']}: {entity['entity']} ({entity['name']})")

def send_ha_notifications(report_summary, categories, json_file_path, yaml_file_path):
    """Send notifications via Home Assistant notification services"""
    try:
        print("📧 Sending notifications via Home Assistant...")
        
        # Prepare notification data
        total_devices = sum(len(devices) for devices in categories.values())
        critical_devices = []
        low_devices = []
        
        # Find critical and low devices
        for category_devices in categories.values():
            for device in category_devices:
                level = device['state']
                if level.replace('.', '').isdigit():
                    level_float = float(level)
                    if level_float <= 15:
                        critical_devices.append(f"{device['name']}: {level}%")
                    elif level_float <= 25:
                        low_devices.append(f"{device['name']}: {level}%")
        
        # Create detailed email message
        email_message = f"""🔋 Battery Device Discovery Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 SUMMARY:
• Total Devices Found: {total_devices}
• Home Assistant: {HA_URL}

📱 DEVICE BREAKDOWN:"""
        
        for category, devices in categories.items():
            if devices:
                category_name = category.replace('_', ' ').title()
                email_message += f"\n• {category_name}: {len(devices)} devices"
        
        if critical_devices:
            email_message += f"\n\n🔴 CRITICAL DEVICES ({len(critical_devices)}):\n"
            email_message += "\n".join([f"• {device}" for device in critical_devices])
        
        if low_devices:
            email_message += f"\n\n🟡 LOW BATTERY DEVICES ({len(low_devices)}):\n"
            email_message += "\n".join([f"• {device}" for device in low_devices])
        
        email_message += f"""

📁 GENERATED FILES:
• JSON Report: {os.path.basename(json_file_path)}
• YAML Automations: {os.path.basename(yaml_file_path) if yaml_file_path else 'None'}

🔧 NEXT STEPS:
1. Copy battery_monitoring.yaml to packages/ folder
2. Add entity includes to recorder and InfluxDB configs  
3. Set up battery dashboard in Lovelace
4. Test notifications using dashboard buttons

🏠 Dashboard: {HA_URL}/lovelace/battery-monitoring

This report was generated by the Battery Discovery Script."""
        
        # Create Telegram message (shorter)
        telegram_message = f"""🔋 Battery Discovery Complete!

📊 Found {total_devices} battery devices:
{chr(10).join([f"• {cat.replace('_', ' ').title()}: {len(devices)}" for cat, devices in categories.items() if devices])}"""
        
        if critical_devices:
            telegram_message += f"\n\n🔴 {len(critical_devices)} CRITICAL devices need immediate attention!"
        
        if low_devices:
            telegram_message += f"\n🟡 {len(low_devices)} devices have low batteries"
        
        telegram_message += f"\n\n📧 Check email for detailed report\n🏠 Dashboard: {HA_URL}/lovelace/battery-monitoring"
        
        # Send notifications via HA services
        notifications_sent = 0
        
        for service in NOTIFICATION_SERVICES:
            try:
                if service == "telegram":
                    # Send shorter message to Telegram
                    payload = {
                        "title": "🔋 Battery Discovery Report",
                        "message": telegram_message
                    }
                else:
                    # Send detailed message to email services
                    payload = {
                        "title": "🔋 Home Assistant Battery Discovery Report",
                        "message": email_message
                    }
                
                response = requests.post(
                    f"{HA_URL}/api/services/notify/{service}",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    print(f"✅ Notification sent via notify.{service}")
                    notifications_sent += 1
                else:
                    print(f"⚠️ Failed to send via notify.{service}: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ Error sending via notify.{service}: {e}")
        
        if notifications_sent > 0:
            print(f"✅ Successfully sent {notifications_sent} notifications!")
            return True
        else:
            print("❌ No notifications were sent successfully")
            return False
            
    except Exception as e:
        print(f"❌ Failed to send HA notifications: {e}")
        return False

def create_file_summary(json_file_path, yaml_file_path, categories):
    """Create a summary of generated files for reference"""
    summary_file = f"battery_discovery_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    total_devices = sum(len(devices) for devices in categories.values())
    
    with open(summary_file, 'w') as f:
        f.write("🔋 BATTERY DEVICE DISCOVERY SUMMARY\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Home Assistant: {HA_URL}\n")
        f.write(f"Total Devices Found: {total_devices}\n\n")
        
        f.write("📁 GENERATED FILES:\n")
        f.write(f"• JSON Report: {json_file_path}\n")
        if yaml_file_path:
            f.write(f"• YAML Automations: {yaml_file_path}\n")
        f.write(f"• This Summary: {summary_file}\n\n")
        
        f.write("📱 DEVICE CATEGORIES:\n")
        for category, devices in categories.items():
            if devices:
                category_name = category.replace('_', ' ').title()
                f.write(f"• {category_name}: {len(devices)} devices\n")
                for device in devices:
                    level = device['state']
                    status = "🔴 CRITICAL" if level.replace('.', '').isdigit() and float(level) <= 15 else \
                            "🟡 LOW" if level.replace('.', '').isdigit() and float(level) <= 25 else \
                            "🟢 GOOD"
                    f.write(f"  - {device['name']}: {level}% {status}\n")
                f.write("\n")
        
        f.write("🔧 NEXT STEPS:\n")
        f.write("1. Copy battery_monitoring.yaml to packages/ folder\n")
        f.write("2. Add entity includes to recorder and InfluxDB configs\n")
        f.write("3. Set up battery dashboard in Lovelace\n")
        f.write("4. Test notifications using dashboard buttons\n")
        f.write("5. Access dashboard: " + HA_URL + "/lovelace/battery-monitoring\n")
    
    print(f"📄 File summary saved to: {summary_file}")
    return summary_file

def generate_yaml_configs(categories):
    """Generate complete YAML configuration files"""
    
    # Generate automations for specific devices
    automations = []
    
    for category, devices in categories.items():
        for device in devices:
            entity_id = device['entity_id']
            device_name = device['name']
            
            # Create specific automation for critical devices
            if category in ['mobile_devices', 'sonoff_devices']:
                automation = f"""
  - id: battery_alert_{entity_id.replace('.', '_')}
    alias: "Battery Alert: {device_name}"
    description: "Alert when {device_name} battery is low"
    trigger:
      - platform: numeric_state
        entity_id: {entity_id}
        below: 20
        for:
          minutes: 30
    condition:
      - condition: state
        entity_id: input_boolean.battery_alerts_enabled
        state: 'on'
    action:
      - service: notify.email
        data:
          title: "🔋 Battery Alert: {device_name}"
          message: >
            {device_name} battery is at {{{{ states('{entity_id}') }}}}%
            
            Please charge or replace the battery soon.
            
            Time: {{{{ now().strftime('%Y-%m-%d %H:%M:%S') }}}}
      - service: notify.telegram
        data:
          title: "🔋 {device_name} Battery Low"
          message: "Battery level: {{{{ states('{entity_id}') }}}}%"
"""
                automations.append(automation)
    
    return automations
    """Generate complete YAML configuration files"""
    
    # Generate automations for specific devices
    automations = []
    
    for category, devices in categories.items():
        for device in devices:
            entity_id = device['entity_id']
            device_name = device['name']
            
            # Create specific automation for critical devices
            if category in ['mobile_devices', 'sonoff_devices']:
                automation = f"""
  - id: battery_alert_{entity_id.replace('.', '_')}
    alias: "Battery Alert: {device_name}"
    description: "Alert when {device_name} battery is low"
    trigger:
      - platform: numeric_state
        entity_id: {entity_id}
        below: 20
        for:
          minutes: 30
    condition:
      - condition: state
        entity_id: input_boolean.battery_alerts_enabled
        state: 'on'
    action:
      - service: notify.email
        data:
          title: "🔋 Battery Alert: {device_name}"
          message: >
            {device_name} battery is at {{{{ states('{entity_id}') }}}}%
            
            Please charge or replace the battery soon.
            
            Time: {{{{ now().strftime('%Y-%m-%d %H:%M:%S') }}}}
      - service: notify.telegram
        data:
          title: "🔋 {device_name} Battery Low"
          message: "Battery level: {{{{ states('{entity_id}') }}}}%"
"""
                automations.append(automation)
    
    return automations

def main():
    """Main function"""
    print("🔍 Discovering battery devices in Home Assistant...")
    print(f"Connecting to: {HA_URL}")
    
    # Get all entities
    entities = get_all_entities()
    if not entities:
        print("❌ Failed to fetch entities. Check your HA_TOKEN and HA_URL.")
        return
    
    print(f"📊 Found {len(entities)} total entities")
    
    # Find battery entities
    battery_entities = find_battery_entities(entities)
    print(f"🔋 Found {len(battery_entities)} battery entities")
    
    # Categorize devices
    categories = categorize_devices(battery_entities)
    
    # Generate configuration
    config = generate_battery_config(categories)
    
    # Print report
    print_discovery_report(categories, config)
    
    # Save detailed report to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    json_file = f'battery_discovery_report_{timestamp}.json'
    with open(json_file, 'w') as f:
        report_data = {
            'timestamp': timestamp,
            'total_devices': len(battery_entities),
            'categories': categories,
            'config': config
        }
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"\n💾 Detailed report saved to: {json_file}")
    
    # Generate automation snippets
    automations = generate_yaml_configs(categories)
    yaml_file = None
    if automations:
        yaml_file = f'battery_automations_{timestamp}.yaml'
        with open(yaml_file, 'w') as f:
            f.write("# Additional battery automations for specific devices\n")
            f.write("automation:")
            for automation in automations:
                f.write(automation)
        
        print(f"🤖 Device-specific automations saved to: {yaml_file}")
    
    # Create file summary
    summary_file = create_file_summary(json_file, yaml_file, categories)
    
    # Generate report text for notifications
    report_summary = f"""Battery Discovery Complete - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Devices: {len(battery_entities)}
Home Assistant: {HA_URL}"""
    
    # Send notifications via HA services
    notifications_sent = send_ha_notifications(report_summary, categories, json_file, yaml_file)
    
    print("\n✅ Discovery complete!")
    print(f"\n📧 HA Notifications: {'✅ Sent successfully' if notifications_sent else '❌ Failed to send'}")
    print(f"\n📁 Generated Files:")
    print(f"   • JSON Report: {json_file}")
    if yaml_file:
        print(f"   • YAML Automations: {yaml_file}")
    print(f"   • Summary: {summary_file}")
    print("\n📋 Next steps:")
    if notifications_sent:
        print("1. Check your email/Telegram for the detailed report")
    print("2. Review the generated local files for configuration details")
    print("3. Copy the battery monitoring configuration to packages/battery_monitoring.yaml")
    print("4. Add the dashboard configuration to your Lovelace dashboards")
    print("5. Restart Home Assistant")
    print("6. Check the new battery monitoring dashboard")

if __name__ == "__main__":
    main()