import re
import json

def parse_input_devices_to_json():
    """
    解析/proc/bus/input/devices文件为结构化JSON，提取干净的字段值
    
    返回:
        str: 格式化的JSON字符串
        None: 解析失败时返回None
    """
    try:
        with open("/proc/bus/input/devices", "r") as f:
            content = f.read()
        
        # 按设备分割（每个设备以"I: Bus="开头）
        device_blocks = re.split(r'\n(?=I: Bus=)', content.strip())
        devices = {}
        
        for block in device_blocks:
            device_info = {}
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            
            for line in lines:
                # 提取类型标识（如I, N, P等）
                match = re.match(r'^([A-Z]): (.*)$', line)
                if not match:
                    continue
                    
                key = match.group(1)
                value_str = match.group(2)
                
                # 解析不同类型的字段
                if key == 'I':  # Bus信息
                    # 提取Bus、Vendor、Product、Version
                    bus_info = {}
                    for item in value_str.split():
                        if '=' in item:
                            k, v = item.split('=', 1)
                            bus_info[k.lower()] = v
                    device_info['bus'] = bus_info
                    
                elif key == 'N':  # 设备名称
                    # 提取引号中的名称（如Name="Power Button" → Power Button）
                    name_match = re.search(r'Name="([^"]+)"', value_str)
                    if name_match:
                        device_info['name'] = name_match.group(1)
                        
                elif key == 'P':  # 物理位置
                    phys_match = re.search(r'Phys=([^ ]+)', value_str)
                    if phys_match:
                        device_info['phys'] = phys_match.group(1)
                        
                elif key == 'S':  # sysfs路径
                    sysfs_match = re.search(r'Sysfs=([^ ]+)', value_str)
                    if sysfs_match:
                        device_info['sysfs'] = sysfs_match.group(1)
                        
                elif key == 'U':  # 唯一标识符
                    uniq_match = re.search(r'Uniq=([^ ]*)', value_str)
                    if uniq_match:
                        device_info['uniq'] = uniq_match.group(1)
                        
                elif key == 'H':  # 处理程序
                    handlers_match = re.search(r'Handlers=(.*)', value_str)
                    if handlers_match:
                        device_info['handlers'] = handlers_match.group(1).split()
                    for handler in device_info['handlers']:
                        if handler.startswith('event'):
                            device_info['path'] = f"/dev/input/{handler}"
                            break

                        
                elif key == 'B':  # 属性字段
                    prop_parts = value_str.split('=', 1)
                    if len(prop_parts) == 2:
                        prop_name = prop_parts[0].strip()
                        prop_value = prop_parts[1].strip()
                        if 'properties' not in device_info:
                            device_info['properties'] = {}
                        device_info['properties'][prop_name] = prop_value
            
            devices[device_info['name']] = device_info
        
        return json.dumps(devices, indent=2, ensure_ascii=False)
        
    except FileNotFoundError:
        print("错误: 未找到/proc/bus/input/devices文件")
        return None
    except PermissionError:
        print("错误: 没有权限访问/proc/bus/input/devices，请使用root权限运行")
        return None
    except Exception as e:
        print(f"解析失败: {str(e)}")
        return None

def find_device_path(name):
    """
    查找设备名称对应的路径
    
    参数:
        name (str): 设备名称
        
    返回:
        str: 设备路径，如"/dev/input/event0"
        None: 如果未找到设备
    """
    devices = parse_input_devices_to_json()
    if not devices:
        return None
    
    devices = json.loads(devices)
    for dev_name, dev_info in devices.items():
        if dev_name == name:
            return dev_info.get('path')
    return None


# 使用示例
if __name__ == "__main__":
    path = find_device_path('pwr_button')
    if path:
        print(path)
    else:
        print("未找到设备")


    