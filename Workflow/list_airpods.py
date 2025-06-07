#!/usr/bin/python3

import json
import os
import subprocess
import sys

# [ProductID]:"[icon file base name]"
AIRPD_PRODUCT_INDX = {
    8194: "AirPods OG",
    8207: "AirPods 2",
    8211: "AirPods 3",
    8219: "AirPods 4",
    8202: "AirPods Max",
    8206: "AirPods Pro",
    8212: "AirPods Pro 2",
    8228: "AirPods Pro 2 with MagSafe Charging Case (USB-C)",
    8203: "Powerbeats Pro",
}


def get_paired_airpods() -> dict:
    """
    Get paired AirPods including info

    Returns:
        dict: dict with paired AirPods name including dict with info
    """
    jsn: dict = json.loads(os.popen('system_profiler SPBluetoothDataType -json').read())
    bt_data: dict = jsn['SPBluetoothDataType'][0] if jsn else None
    # With 12.3 and newer, json response has changed
    # macos < 12.3
    try:
        devices: dict = bt_data['devices_list']
        connected_devices = False
    # macos >= 12.3
    except KeyError as e:
        connected_devices: list = bt_data['device_connected'] if 'device_connected' in bt_data else []
        not_connected_devices: list = bt_data['device_not_connected']
        devices = connected_devices + not_connected_devices if 'device_not_connected' in bt_data else []
    out_dict = {}
    for i in devices:
        for d_name, d_info in i.items():
            address: str = d_info.get('device_address')
            if 'device_productID' in d_info:  # check if device is a supported headset
                prod_id = int(d_info.get('device_productID', 0), 16)
                vendor_id: str = int(d_info.get('device_vendorID', 0), 16)
                prod_label = AIRPD_PRODUCT_INDX.get(prod_id)
                if connected_devices:  # macos >= 12.3
                    device_connected: str = "Yes" if i in connected_devices else "No"
                else:  # macos < 12.3
                    device_connected: str = d_info.get('device_connected')
                out_dict.update(
                    {d_name:
                        {"address": address,
                            "connected": device_connected,
                            "prod_label": prod_label
                         }
                     }
                ) if prod_id in AIRPD_PRODUCT_INDX else {}
    return out_dict


def is_tool_installed(tool_name):
    try:
        result = subprocess.run([tool_name, "-h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check the return code
        if result.returncode == 0:
            return True
        else:
            return False
    except FileNotFoundError:
        return False

def custom_sort_key(key: str):
    def sort_key(item, key=key) -> int:
        # Keep a device always on top
        if key in item["title"]:
            return 0
        else:
            return 1
    return sort_key


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    favorite_device = os.getenv("favorite_device", "")
    items = []
    
    if is_tool_installed("blueutil"):
        for ap_name, status in get_paired_airpods().items():
            adr: str = status.get('address')
            ap_type: str = status.get('prod_label')
            is_connected: bool = True if status.get('connected') == 'Yes' else False
            con_str: str = "\u23CE to disconnect." if is_connected else "\u23CE to connect."
            ico: str = f"icons_for_earphones/{ap_type}.png" if is_connected else f"icons_for_earphones/{ap_type} Case.png"
            con_switch: str = "1" if is_connected else "0"
            if query == "" or query.lower() in ap_name.lower():
                item = {
                    "title": f"{ap_name} {'✅️' if is_connected else '🚫'}",
                    "subtitle": f"{con_str}",
                    "arg": f"{adr};{con_switch}",
                    "icon": {
                        "path": ico,
                        "type": "image"
                    }
                }
                items.append(item)
    else:
        item = {
            "title": "The workflow requires ‘blueutil’",
            "subtitle": "Press ↵ to let Alfred resolve dependencies...",
            "valid": True,
            "arg": "blueutil"
        }
        items.append(item)

    if favorite_device:
        items = sorted(items, key=custom_sort_key(key=favorite_device))
    
    # Create the final output structure
    output = {"rerun": 2, "items": items}
    
    # Write the JSON to stdout
    sys.stdout.write(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
