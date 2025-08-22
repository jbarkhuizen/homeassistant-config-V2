# Opened Files
## File Name
custom_components/battery_discovery.py
## File Content
#!/usr/bin/env python3
"""
Battery Device Discovery Script for Home Assistant
Run this script to discover all battery-powered devices in your HA setup
"""

import requests
import json
import re
from datetime import datetime

# Configuration
HA_URL = "http://192.168.1.30:8123"  # Your HA URL
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI1MmI5NmRkZDE1ODk0MTY0YTA5ZTBjYTRkZDRmNTAwMCIsImlhdCI6MTc1NTg2NTkyMiwiZXhwIjoyMDcxMjI1OTIyfQ.qhwcOA9gZTBKfleSiv1LL34NYeJC_ils_6-1q6Rga8Q"  # Get from HA Profile -> Long-lived access tokens

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
        r'.*_bat
,
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
    
    with open(f'battery_discovery_report_{timestamp}.json', 'w') as f:
        report_data = {
            'timestamp': timestamp,
            'total_devices': len(battery_entities),
            'categories': categories,
            'config': config
        }
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"\n💾 Detailed report saved to: battery_discovery_report_{timestamp}.json")
    
    # Generate automation snippets
    automations = generate_yaml_configs(categories)
    if automations:
        with open(f'battery_automations_{timestamp}.yaml', 'w') as f:
            f.write("# Additional battery automations for specific devices\n")
            f.write("automation:")
            for automation in automations:
                f.write(automation)
        
        print(f"🤖 Device-specific automations saved to: battery_automations_{timestamp}.yaml")
    
    print("\n✅ Discovery complete!")
    print("\n📋 Next steps:")
    print("1. Update HA_TOKEN in this script with your actual token")
    print("2. Copy the battery monitoring configuration to packages/battery_monitoring.yaml")
    print("3. Add the dashboard configuration to your Lovelace dashboards")
    print("4. Restart Home Assistant")
    print("5. Check the new battery monitoring dashboard")

if __name__ == "__main__":
    main()
