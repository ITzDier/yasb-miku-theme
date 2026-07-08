import sys
import psutil
import subprocess
import argparse

def get_gpu_info():
    try:
        cmd = "nvidia-smi --query-gpu=utilization.gpu,temperature.gpu --format=csv,noheader,nounits"
        output = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        util, temp = output.split(', ')
        return f"{util}% ({temp}°C)"
    except Exception:
        return "0%"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['base', 'detailed'], default='base')
    args = parser.parse_args()

    cpu_usage = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    gpu_data = get_gpu_info()

    if args.mode == 'base':
        print(f"󰻠 CPU: {int(cpu_usage)}% | 󰍛 RAM: {int(ram.percent)}% | 󰢮 GPU: {gpu_data}")

if __name__ == "__main__":
    main()