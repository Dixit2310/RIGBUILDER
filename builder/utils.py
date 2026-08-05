import re

def parse_tier(name):
    """Utility to guess performance tier from product name (CPU/GPU)"""
    name_upper = name.upper()
    
    # GPU Tiers
    if "4090" in name_upper or "7900 XTX" in name_upper:
        return 5 # Enthusiast
    if "4080" in name_upper or "4070 TI" in name_upper or "7900 XT" in name_upper:
        return 4.5 # High-end Enthusiast
    if "4070" in name_upper or "3080" in name_upper or "7800 XT" in name_upper:
        return 4 # High-end
    if "4060 TI" in name_upper or "3070" in name_upper or "6700 XT" in name_upper:
        return 3.5 # Upper Mid-range
    if "4060" in name_upper or "3060" in name_upper or "7600" in name_upper:
        return 3 # Mid-range
    if "3050" in name_upper or "6500 XT" in name_upper or "1650" in name_upper:
        return 2 # Budget

    # CPU Tiers
    if "I9" in name_upper or "RYZEN 9" in name_upper or "7950X" in name_upper or "7900X" in name_upper:
        return 5
    if "I7" in name_upper or "RYZEN 7" in name_upper or "7800X3D" in name_upper or "7700X" in name_upper:
        return 4.5
    if "I5" in name_upper or "RYZEN 5" in name_upper or "7600X" in name_upper or "5600X" in name_upper:
        return 3.5
    if "I3" in name_upper or "RYZEN 3" in name_upper or "4100" in name_upper:
        return 2

    return 3 # Default Mid-tier

def calculate_performance_scores(build):
    """Calculates Gaming, Productivity, and Streaming scores out of 100"""
    cpu_tier = parse_tier(build.cpu.name) if build.cpu else 1
    gpu_tier = parse_tier(build.gpu.name) if build.gpu else 1
    ram_gb = 8
    
    if build.ram:
        # Try to extract RAM size e.g. "16GB" or "32GB" or "2x16GB"
        ram_name = build.ram.name.upper()
        match = re.search(r'(\d+)\s*GB', ram_name)
        if match:
            ram_gb = int(match.group(1))
            if "2X" in ram_name or "KIT" in ram_name:
                pass # Already got it or it's double, just keep it

    # Sub scores
    # Gaming is GPU heavy (70%) and CPU (20%) and RAM (10%)
    gaming_raw = (gpu_tier * 0.7) + (cpu_tier * 0.2) + ((min(ram_gb, 32) / 32.0) * 5 * 0.1)
    gaming_score = int((gaming_raw / 5.0) * 100)

    # Productivity is CPU heavy (60%) and RAM (30%) and GPU (10%)
    productivity_raw = (cpu_tier * 0.6) + ((min(ram_gb, 64) / 64.0) * 5 * 0.3) + (gpu_tier * 0.1)
    productivity_score = int((productivity_raw / 5.0) * 100)

    # Streaming is CPU heavy (50%), GPU heavy (Encoder) (40%), RAM (10%)
    streaming_raw = (cpu_tier * 0.5) + (gpu_tier * 0.4) + ((min(ram_gb, 32) / 32.0) * 5 * 0.1)
    streaming_score = int((streaming_raw / 5.0) * 100)

    return {
        'gaming': min(max(gaming_score, 10), 100),
        'productivity': min(max(productivity_score, 10), 100),
        'streaming': min(max(streaming_score, 10), 100),
    }

def estimate_fps(build):
    """Estimates FPS for 1080p, 1440p and 4K resolutions on selected games"""
    gpu_name = build.gpu.name.upper() if build.gpu else ""
    
    # Base performance factor based on GPU
    gpu_tier = parse_tier(gpu_name)
    
    games = [
        {"name": "Cyberpunk 2077", "base_fps": 35},
        {"name": "Valorant / CS2", "base_fps": 180},
        {"name": "Call of Duty: Warzone", "base_fps": 55},
        {"name": "Fortnite (Performance)", "base_fps": 120},
        {"name": "Red Dead Redemption 2", "base_fps": 45}
    ]
    
    resolutions = {
        "1080p": 1.0,
        "1440p": 0.7,
        "4K": 0.4
    }
    
    results = {}
    for res_name, multiplier in resolutions.items():
        res_games = []
        for game in games:
            # Scale FPS according to GPU tier and resolution
            calculated_fps = int(game["base_fps"] * (gpu_tier / 3.0) * multiplier)
            if build.cpu:
                cpu_tier = parse_tier(build.cpu.name)
                # CPU bottleneck scaling slightly for ultra high refresh rates
                if calculated_fps > 150:
                    calculated_fps = int(calculated_fps * (cpu_tier / 4.0))
            
            res_games.append({
                "game": game["name"],
                "fps": max(calculated_fps, 20)
            })
        results[res_name] = res_games
        
    return results

def calculate_bottleneck(build):
    """Calculates bottleneck percentage and details between CPU and GPU"""
    if not build.cpu or not build.gpu:
        return {"percentage": 0, "type": "N/A", "description": "Add both a CPU and GPU to calculate bottleneck."}
        
    cpu_tier = parse_tier(build.cpu.name)
    gpu_tier = parse_tier(build.gpu.name)
    
    diff = cpu_tier - gpu_tier
    percentage = int(abs(diff) * 15) # Scale diff to a percentage up to ~45%
    percentage = min(max(percentage, 2), 65) # Clamped
    
    if diff > 1.0:
        bottleneck_type = "GPU Bottleneck"
        description = (
            f"Your CPU ({build.cpu.brand.name} {build.cpu.name}) is significantly more powerful than "
            f"your GPU ({build.gpu.brand.name} {build.gpu.name}). In games, your GPU will run at 100% capacity "
            f"while the CPU sits idle, preventing higher graphics settings."
        )
    elif diff < -1.0:
        bottleneck_type = "CPU Bottleneck"
        description = (
            f"Your GPU ({build.gpu.brand.name} {build.gpu.name}) is too powerful for "
            f"your CPU ({build.cpu.brand.name} {build.cpu.name}). The CPU will struggle to feed instructions "
            f"to the GPU fast enough, causing stuttering or lower average frame rates."
        )
    else:
        percentage = int(abs(diff) * 5) + 3 # Balanced build
        bottleneck_type = "Balanced"
        description = "Your CPU and GPU are well balanced. Neither component will heavily bottleneck the other, ensuring optimal hardware utilization."
        
    return {
        "percentage": percentage,
        "type": bottleneck_type,
        "description": description
    }

def estimate_temperatures(build):
    """Estimates idle and load temperatures for CPU and GPU in Celsius"""
    # Baseline
    cpu_idle, cpu_load = 35, 75
    gpu_idle, gpu_load = 38, 78
    
    # Apply cooler factor
    if build.cpu_cooler:
        cooler_name = build.cpu_cooler.name.upper()
        if "LIQUID" in cooler_name or "AIO" in cooler_name or "WATER" in cooler_name:
            cpu_load -= 8
            cpu_idle -= 2
        else: # Air cooler
            cpu_load -= 3
            
    # Apply case fans factor
    fan_count = 1
    if build.case_fans:
        # Guess fan count from name, e.g. "3-Pack" or "120mm Fan"
        fan_name = build.case_fans.name.upper()
        if "3-PACK" in fan_name or "3X" in fan_name:
            fan_count = 3
        elif "5-PACK" in fan_name or "5X" in fan_name:
            fan_count = 5
            
    # Scale load temperatures down based on airflow
    airflow_reduction = min(fan_count * 1.5, 8.0)
    cpu_load -= int(airflow_reduction)
    gpu_load -= int(airflow_reduction * 1.2)
    
    # Adjust for TDP
    if build.cpu and build.cpu.power_consumption_watts > 125:
        cpu_load += 5
    if build.gpu and build.gpu.power_consumption_watts > 250:
        gpu_load += 5
        
    return {
        "cpu_idle": max(cpu_idle, 25),
        "cpu_load": min(cpu_load, 95),
        "gpu_idle": max(gpu_idle, 25),
        "gpu_load": min(gpu_load, 90)
    }

def estimate_build_time(build):
    """Estimates build difficulty and time in minutes"""
    if not build.cpu or not build.motherboard:
        return {"difficulty": "Easy", "time_range": "N/A", "minutes": 0}
        
    minutes = 45 # baseline
    difficulty = "Easy"
    
    # Add time for cooler complexity
    if build.cpu_cooler:
        cooler_name = build.cpu_cooler.name.upper()
        if "LIQUID" in cooler_name or "AIO" in cooler_name or "WATER" in cooler_name:
            minutes += 25
            difficulty = "Moderate"
            
    # Add time for extra fans and wiring
    if build.case_fans:
        minutes += 15
        
    # GPU installation
    if build.gpu:
        minutes += 10
        
    # RGB accessories
    if build.rgb_accessories:
        minutes += 20
        difficulty = "Moderate" if difficulty == "Easy" else "Hard"
        
    if minutes > 90:
        difficulty = "Advanced / Hard"
        
    return {
        "difficulty": difficulty,
        "time_range": f"{minutes - 10}-{minutes + 15} mins",
        "minutes": minutes
    }
