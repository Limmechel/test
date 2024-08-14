import sys
import grequests
from bs4 import BeautifulSoup
from requests.auth import HTTPDigestAuth
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import httpx
from httpx import DigestAuth, Limits
from concurrent.futures import ThreadPoolExecutor, as_completed


class PoolManager:
    def __init__(self, username, passwords):
        self.username = username
        self.passwords = passwords

        # Настройка клиента с лимитами на количество соединений
        limits = Limits(max_connections=100, max_keepalive_connections=20)
        self.session = httpx.Client(limits=limits)
        self.session.headers.update({'Connection': 'keep-alive'})
        self.cached_auth = None

    def get_auth(self, ip):
        if self.cached_auth:
            return self.cached_auth

        for pwd in self.passwords:
            auth = httpx.DigestAuth(self.username, pwd)
            try:
                # Пробуем авторизацию без таймаута
                response = self.session.get(f'http://{ip}/cgi-bin/get_system_info.cgi', auth=auth)
                if response.status_code == 200:
                    self.cached_auth = auth
                    return auth
            except httpx.RequestError:
                continue  # Неправильный пароль, пробуем следующий

        return None

    async def apply_pools_async(self, ip, pools):
        url = f"http://{ip}/cgi-bin/set_miner_conf.cgi"
        data = {"pools": pools}
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Host': ip,
            'Origin': f'http://{ip}',
            'Referer': f'http://{ip}/',
            'User-Agent': 'AoS_Tools',
            'X-Requested-With': 'XMLHttpRequest'
        }

        auth = self.get_auth(ip)
        if not auth:
            return False, f"Ошибка аутентификации для {ip} со всеми паролями"

        try:
            async with httpx.AsyncClient(auth=auth, limits=Limits(max_connections=100, max_keepalive_connections=20)) as client:
                response = await client.post(url, json=data, headers=headers)
                if response.status_code == 200:
                    return True, f"Пулы успешно применены для {ip}"
                else:
                    return False, f"Ошибка при применении пулов для {ip}. Код ответа: {response.status_code}"
        except httpx.RequestError as e:
            return False, f"Error applying pools for {ip}: {str(e)}"

    async def apply_pools_batch_async(self, ips, pools, batch_size=10):
        tasks = []
        results = []
        for ip in ips:
            task = asyncio.ensure_future(self.apply_pools_async(ip, pools))
            tasks.append(task)
            if len(tasks) >= batch_size:
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
                tasks = []
        if tasks:
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        return results

    def apply_pools(self, ips, pools, batch_size=10):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.apply_pools_batch_async(ips, pools, batch_size))

    async def set_miner_conf_async(self, ip, settings):
        url = f"http://{ip}/cgi-bin/set_miner_conf.cgi"
        headers = {
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Host': ip,
            'Origin': f'http://{ip}',
            'Referer': f'http://{ip}/',
            'User-Agent': 'AoS_Tools',
            'X-Requested-With': 'XMLHttpRequest'
        }

        auth = self.get_auth(ip)
        if not auth:
            return ip, False, f"Ошибка аутентификации для {ip} со всеми паролями"

        try:
            async with httpx.AsyncClient(auth=auth, limits=Limits(max_connections=100, max_keepalive_connections=20)) as client:
                response = await client.post(url, json=settings, headers=headers)
                if response.status_code == 200:
                    return ip, True, f"Настройки отправлены для {ip}"
                else:
                    return ip, False, f"Ошибка при отправке настроек для {ip}: {response.status_code}"
        except httpx.RequestError as e:
            return ip, False, f"Ошибка при отправке настроек для {ip}: {str(e)}"

    async def set_miner_conf_batch_async(self, ips, settings, batch_size=5):
        tasks = []
        results = []
        for ip in ips:
            task = asyncio.ensure_future(self.set_miner_conf_async(ip, settings))
            tasks.append(task)
            if len(tasks) >= batch_size:
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
                tasks = []
        if tasks:
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        return results

    def set_miner_conf(self, ips, settings, batch_size=5):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.set_miner_conf_batch_async(ips, settings, batch_size))
import json
import requests
import ipaddress
import socket
import re
import os
import string
import itertools
import asyncio
import asyncssh
import ipaddress
import random
import socket
import threading
import setproctitle
import subprocess
import json
import paramiko
import logging
from datetime import datetime
import time
import traceback
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QProgressBar, QListWidget, QInputDialog,
    QMessageBox, QHeaderView, QFrame, QAbstractItemView, QGridLayout, QFormLayout,
    QSplitter, QSpacerItem, QSizePolicy, QCheckBox, QProgressDialog, QDesktopWidget, QMenu, QTableWidgetSelectionRange, QDialog, QTextEdit, QDialogButtonBox, QListWidgetItem, QComboBox, QSpinBox, QButtonGroup, QRadioButton, QGroupBox, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QRunnable, QThreadPool, QRect, QThread, QTimeLine, QMetaObject, Q_ARG, QEventLoop, pyqtSlot, QSortFilterProxyModel, QCoreApplication
from PyQt5.QtGui import QClipboard, QFont, QIcon
from fabric import Connection
from queue import Queue


# Флаг мониторинга
monitoring = False

def create_crash_log(exc_type, exc_value, exc_traceback):
    log_filename = f"crash_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(filename=log_filename, level=logging.ERROR,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.error("Программа завершилась с ошибкой:", exc_info=(exc_type, exc_value, exc_traceback))

def exception_handler(exc_type, exc_value, exc_traceback):
    create_crash_log(exc_type, exc_value, exc_traceback)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
def check_api(ip, port=4028, timeout=1):
    start_time = time.time()  # Начало замера времени
  #  print(f"Checking {ip}...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((ip, port))
        sock.send(json.dumps({"command": "version"}).encode())
        response = sock.recv(4096)  # Увеличьте размер буфера
        response = response.strip(b'\x00')
        try:
            json.loads(response)
            return True
        except json.JSONDecodeError:
            return False
    except socket.timeout:
        return False
    except ConnectionRefusedError:
        return False
    except Exception as e:
        return False
    finally:
        sock.close()
        end_time = time.time()  # Конец замера времени
        elapsed_time = end_time - start_time
      #  print(f"Execution time for {ip}: {elapsed_time:.4f} seconds")
        
def ip_range_to_list(ip_ranges):
    all_ips = set()
    for ip_range in ip_ranges.split(','):
        ip_range = ip_range.strip()
        if '-' in ip_range:
            start_ip, end_ip = ip_range.split('-')
            try:
                start_ip = ipaddress.IPv4Address(start_ip.strip())
                end_ip = ipaddress.IPv4Address(end_ip.strip())
                all_ips.update(str(ipaddress.IPv4Address(ip)) for ip in range(int(start_ip), int(end_ip) + 1))
            except ipaddress.AddressValueError as e:
                print(f"Invalid IP address in range {ip_range}: {e}")
        else:
            try:
                ipaddress.IPv4Address(ip_range)  # Validate single IP
                all_ips.add(ip_range)
            except ipaddress.AddressValueError as e:
                print(f"Invalid IP address: {ip_range}: {e}")
    return list(all_ips)

# Функция для получения данных с /cgi-bin/stats.cgi
def get_stats(ip):
    data = {}   
    # Получение данных pools
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # Увеличиваем таймаут до 10 секунд
        sock.connect((ip, 4028))
        
        try:
            sock.send(json.dumps({"command": "pools"}).encode())
            pools_response = sock.recv(4096).decode('utf-8')
            pools_response = pools_response.strip('\x00')
            try:
                pools_data = json.loads(pools_response)
                data["pools"] = pools_data["POOLS"]  # Сохраняем только значение ключа "POOLS"
             #   print(f"Received pools data from {ip}: {pools_data}")  # Добавленный вывод
            except json.JSONDecodeError:
            #    print(f"Failed to parse pools data from {ip}")  # Добавленный вывод
                pass
        except (socket.timeout, socket.error):
         #   print(f"Failed to receive pools data from {ip}")  # Добавленный вывод
            pass
    except (socket.timeout, socket.error, ConnectionRefusedError) as e:
        print(f"Error getting pools from {ip}: {str(e)}")
    finally:
        sock.close()  # Закрываем соединение после получения данных pools
    
    # Получение данных stats
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # Увеличиваем таймаут до 10 секунд
        sock.connect((ip, 4028))
        
        try:
           # print(f"Sending stats command to {ip}")  # Добавленный вывод
            sock.send(json.dumps({"command": "stats"}).encode())
           # print(f"Sent stats command to {ip}")  # Добавленный вывод
            
            stats_response = sock.recv(4096).decode('utf-8')
         #   print(f"Received stats response from {ip}: {stats_response}")  # Добавленный вывод
            
            stats_response = stats_response.strip('\x00')
         #   print(f"Stripped stats response from {ip}: {stats_response}")  # Добавленный вывод
            
            try:
                stats_data = json.loads(stats_response)
             #   print(f"Parsed stats data from {ip}: {stats_data}")  # Добавленный вывод
                data["stats"] = stats_data
            except json.JSONDecodeError:
            #    print(f"Failed to parse stats data from {ip}")  # Добавленный вывод
                data["stats"] = {}  # Устанавливаем пустой словарь, если не удалось распарсить данные статистики
        except (socket.timeout, socket.error):
         #   print(f"Failed to receive stats data from {ip}")  # Добавленный вывод
            data["stats"] = {}  # Устанавливаем пустой словарь, если не удалось получить данные статистики
    except (socket.timeout, socket.error, ConnectionRefusedError) as e:
        print(f"Error getting stats from {ip}: {str(e)}")
    finally:
        sock.close()  # Закрываем соединение после получения данных stats
    
    if not data:
      #  print(f"No data received from {ip}")  # Добавленный вывод
        return None
    
    return data

# Функция для получения текущего конфигурационного файла
def get_config(ip):
    url = f"http://{ip}/cgi-bin/get_miner_conf.cgi"    
    def try_password(pwd):
        try:
            response = requests.get(url, auth=HTTPDigestAuth(username, pwd), 
                                    headers={'Accept-Encoding': 'gzip, deflate'}, 
                                    timeout=1)
            if response.status_code == 200:
                return response.json(), pwd
        except requests.RequestException:
            pass
        return None, pwd
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_pwd = {executor.submit(try_password, pwd): pwd for pwd in password}
        for future in as_completed(future_to_pwd):
            result, pwd = future.result()
            if result:
               # print(f"Received config from {ip} with password: {pwd}")
                return result
        #    else:
              #  print(f"Failed to get config from {ip} with password: {pwd}")
 #   print(f"Failed to get config from {ip} with any password")
    return None
        
def get_power(ip):
    url = f"http://{ip}/cgi-bin/get_system_info.cgi"
    def try_password(pwd):
        try:
            response = requests.get(url, auth=HTTPDigestAuth(username, pwd),
                                    headers={'Accept-Encoding': 'gzip, deflate'},
                                    timeout=1)
            if response.status_code == 200:
                data = response.json()
                return data.get("power", None), pwd
        except requests.RequestException:
            pass
        return None, pwd
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_pwd = {executor.submit(try_password, pwd): pwd for pwd in password}
        for future in as_completed(future_to_pwd):
            power, pwd = future.result()
            if power is not None:
               # print(f"Received power info from {ip} with password: {pwd}")
                return power
          #  else:
              #  print(f"Failed to get power info from {ip} with password: {pwd}")
 #   print(f"Failed to get power info from {ip} with any password")
    return None

# Логин и пароль для авторизации
username = "root"
password = []

# Преобразуем данные в JSON строку
data = {
    "bitmain-fan-ctrl": False,
    "bitmain-fan-pwm": "100",
    "bitmain-hashrate-percent": "100",
    "miner-mode": "0",
    "freq-level": "100",
    "mode-chain": "1",
    "freq-prof": "150",
    "volt-chain": "13.4",
    "freq-chain": "590",
    "freq-chain0": "590",
    "freq-chain1": "590",
    "freq-chain2": "590",
    "volt-cor": "0",
    "fan-chek": False,
    "wdt-chek": False,
    "wdt-proc": "5",
    "temp-target": "67",
    "volt-corr": True,
    "chain-chek": True,
    "first-start": False,
    "diff-freq": True,
    "hot-switch": False,
    "pools": [
        {"url": "sadgdf", "user": "fdgdfgh", "pass": ""},
        {"url": "", "user": "", "pass": ""},
        {"url": "", "user": "", "pass": ""}
    ]
}

json_data = json.dumps(data)

class FastScanWorker(QRunnable):
    def __init__(self, ip_list, callback):
        super().__init__()
        self.ip_list = ip_list
        self.callback = callback

    def run(self):
        open_addresses = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_api, ip) for ip in self.ip_list]
            for future in futures:
                if future.result():
                    open_addresses.append(future.result())
        self.callback(open_addresses)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class BaseWindowMixin:
    def setup_window(self, title=None):
        app = QApplication.instance()
        if title:
            self.setWindowTitle(f"{app.applicationName()} - {title}")
        else:
            self.setWindowTitle(app.applicationName())

class BaseMainWindow(QMainWindow, BaseWindowMixin):
    def __init__(self, title=None):
        super().__init__()
        self.setup_window(title)

class BaseWindow(QWidget, BaseWindowMixin):
    def __init__(self, title=None):
        super().__init__()
        self.setup_window(title)
            
class AsicSettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Настройки AoS")
        self.selected_ips = [] 
        self.profile_data = {}
        
        self.scale = parent.scale if parent else 1
        self.setGeometry(300, 300, int(700 * self.scale), int(400 * self.scale))

        self.label_font = QFont()
        self.label_font.setPointSize(int(9 * self.scale))
        
        self.checkbox_font = QFont()
        self.checkbox_font.setPointSize(int(9 * self.scale))
        
        self.button_font = QFont()
        self.button_font.setPointSize(int(9 * self.scale))
        
        self.input_font = QFont()
        self.input_font.setPointSize(int(9 * self.scale))

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        stock_mode_group_box = QGroupBox("Сток режимы асика")
        stock_mode_group_box.setFont(self.label_font)
        stock_mode_layout = QHBoxLayout(stock_mode_group_box)
        stock_mode_layout.setSpacing(10)

        self.stock_mode_button_group = QButtonGroup()

        self.normal_mode_checkbox = QRadioButton("Нормал")
        self.normal_mode_checkbox.setFont(self.checkbox_font)
        self.normal_mode_checkbox.setChecked(True)  # Выбрано по умолчанию
        self.stock_mode_button_group.addButton(self.normal_mode_checkbox)
        stock_mode_layout.addWidget(self.normal_mode_checkbox)

        self.sleep_mode_checkbox = QRadioButton("Сон")
        self.sleep_mode_checkbox.setFont(self.checkbox_font)
        self.stock_mode_button_group.addButton(self.sleep_mode_checkbox)
        stock_mode_layout.addWidget(self.sleep_mode_checkbox)

        layout.addWidget(stock_mode_group_box)

        mode_group_box = QGroupBox("Режим")
        mode_group_box.setFont(self.label_font)
        mode_layout = QHBoxLayout(mode_group_box)
        mode_layout.setSpacing(20)

        self.mode_button_group = QButtonGroup()

        self.stock_mode_checkbox = QRadioButton("Сток режим")
        self.stock_mode_checkbox.setFont(self.checkbox_font)
        self.mode_button_group.addButton(self.stock_mode_checkbox)
        mode_layout.addWidget(self.stock_mode_checkbox)

        self.profile_mode_checkbox = QRadioButton("Профиля")
        self.profile_mode_checkbox.setFont(self.checkbox_font)       
        self.mode_button_group.addButton(self.profile_mode_checkbox)
        mode_layout.addWidget(self.profile_mode_checkbox)

        self.manual_mode_checkbox = QRadioButton("Ручной режим")
        self.manual_mode_checkbox.setFont(self.checkbox_font)
        self.mode_button_group.addButton(self.manual_mode_checkbox)
        mode_layout.addWidget(self.manual_mode_checkbox)

        layout.addWidget(mode_group_box)

        self.settings_group_box = QGroupBox("Настройки")
        self.settings_group_box.setFont(self.label_font)
        self.settings_layout = QGridLayout(self.settings_group_box)
        self.settings_layout.setSpacing(10)
        layout.addWidget(self.settings_group_box)

        self.profile_label = QLabel("Профиль:")
        self.profile_label.setFont(self.label_font)
        self.settings_layout.addWidget(self.profile_label, 0, 0)
        
        self.profile_combo = QComboBox()
        self.profile_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.profile_combo.setMinimumWidth(250)
        self.profile_combo.setMinimumHeight(30)
        self.profile_combo.setFont(self.input_font)
        self.settings_layout.addWidget(self.profile_combo, 0, 1, 1, 3)

        voltage_corr_label = QLabel("Корр.вольтажа:")
        voltage_corr_label.setFont(self.label_font)
        self.settings_layout.addWidget(voltage_corr_label, 1, 0)

        self.voltage_corr_input = QLineEdit()
        self.voltage_corr_input.setFont(self.input_font)
        self.voltage_corr_input.setFixedSize(180, 30)
        self.settings_layout.addWidget(self.voltage_corr_input, 1, 1)

        fan_mode_label = QLabel("Режим кулеров:")
        fan_mode_label.setFont(self.label_font)
        self.settings_layout.addWidget(fan_mode_label, 2, 0)

        self.fan_mode_button_group = QButtonGroup()

        self.manual_fan_toggle = QRadioButton("Ручной")
        self.manual_fan_toggle.setFont(self.checkbox_font)
        self.manual_fan_toggle.toggled.connect(self.on_manual_fan_toggled)
        self.fan_mode_button_group.addButton(self.manual_fan_toggle)
        self.settings_layout.addWidget(self.manual_fan_toggle, 2, 1)

        self.manual_fan_input = QLineEdit()
        self.manual_fan_input.setFont(self.input_font)
        self.manual_fan_input.setPlaceholderText("%")
        self.manual_fan_input.setFixedSize(70, 30)
        self.manual_fan_input.hide()
        self.settings_layout.addWidget(self.manual_fan_input, 2, 2)

        self.autofan_toggle = QRadioButton("Автофан")
        self.autofan_toggle.setFont(self.checkbox_font)
        self.autofan_toggle.toggled.connect(self.on_autofan_toggled)
        self.fan_mode_button_group.addButton(self.autofan_toggle)
        self.settings_layout.addWidget(self.autofan_toggle, 3, 1)

        self.autofan_input = QLineEdit()
        self.autofan_input.setFont(self.input_font)
        self.autofan_input.setPlaceholderText("°C")
        self.autofan_input.setFixedSize(70, 30)
        self.autofan_input.hide()
        self.settings_layout.addWidget(self.autofan_input, 3, 2)

        self.immersion_toggle = QRadioButton("Иммерсия")
        self.immersion_toggle.setFont(self.checkbox_font)
        self.fan_mode_button_group.addButton(self.immersion_toggle)
        self.settings_layout.addWidget(self.immersion_toggle, 4, 1)

        hashboard_check_label = QLabel("Проверка хэш плат:")
        hashboard_check_label.setFont(self.label_font)
        self.settings_layout.addWidget(hashboard_check_label, 5, 0)

        self.hashboard_check_button_group = QButtonGroup()

        self.hashboard_check_on_toggle = QRadioButton("вкл")
        self.hashboard_check_on_toggle.setFont(self.checkbox_font)
        self.hashboard_check_button_group.addButton(self.hashboard_check_on_toggle)
        self.settings_layout.addWidget(self.hashboard_check_on_toggle, 5, 1)

        self.hashboard_check_off_toggle = QRadioButton("выкл")
        self.hashboard_check_off_toggle.setFont(self.checkbox_font)
        self.hashboard_check_button_group.addButton(self.hashboard_check_off_toggle)
        self.settings_layout.addWidget(self.hashboard_check_off_toggle, 5, 2)

        autorestart_label = QLabel("Авторестарт:")
        autorestart_label.setFont(self.label_font)
        self.settings_layout.addWidget(autorestart_label, 6, 0)

        self.autorestart_button_group = QButtonGroup()

        self.autorestart_on_toggle = QRadioButton("вкл")
        self.autorestart_on_toggle.setFont(self.checkbox_font)
        self.autorestart_on_toggle.toggled.connect(self.on_autorestart_toggled)
        self.autorestart_button_group.addButton(self.autorestart_on_toggle)
        self.settings_layout.addWidget(self.autorestart_on_toggle, 6, 1)

        self.autorestart_input = QLineEdit()
        self.autorestart_input.setFont(self.input_font)
        self.autorestart_input.setPlaceholderText("%")
        self.autorestart_input.setFixedSize(60, 30)
        self.autorestart_input.hide()
        self.settings_layout.addWidget(self.autorestart_input, 6, 1, 1, 1, Qt.AlignRight)

        self.autorestart_off_toggle = QRadioButton("выкл")
        self.autorestart_off_toggle.setFont(self.checkbox_font)
        self.autorestart_button_group.addButton(self.autorestart_off_toggle)
        self.settings_layout.addWidget(self.autorestart_off_toggle, 6, 2)

        voltage_adaptation_label = QLabel("Адаптация вольтажа:")
        voltage_adaptation_label.setFont(self.label_font)
        self.settings_layout.addWidget(voltage_adaptation_label, 7, 0)

        self.voltage_adaptation_button_group = QButtonGroup()

        self.voltage_adaptation_on_toggle = QRadioButton("вкл")
        self.voltage_adaptation_on_toggle.setFont(self.checkbox_font)
        self.voltage_adaptation_button_group.addButton(self.voltage_adaptation_on_toggle)
        self.settings_layout.addWidget(self.voltage_adaptation_on_toggle, 7, 1)

        self.voltage_adaptation_off_toggle = QRadioButton("выкл")
        self.voltage_adaptation_off_toggle.setFont(self.checkbox_font)
        self.voltage_adaptation_button_group.addButton(self.voltage_adaptation_off_toggle)
        self.settings_layout.addWidget(self.voltage_adaptation_off_toggle, 7, 2)

        fast_start_label = QLabel("Быстрый старт:")
        fast_start_label.setFont(self.label_font)
        self.settings_layout.addWidget(fast_start_label, 8, 0)

        self.fast_start_button_group = QButtonGroup()

        self.fast_start_on_toggle = QRadioButton("вкл")
        self.fast_start_on_toggle.setFont(self.checkbox_font)
        self.fast_start_button_group.addButton(self.fast_start_on_toggle)
        self.settings_layout.addWidget(self.fast_start_on_toggle, 8, 1)

        self.fast_start_off_toggle = QRadioButton("выкл")
        self.fast_start_off_toggle.setFont(self.checkbox_font)
        self.fast_start_button_group.addButton(self.fast_start_off_toggle)
        self.settings_layout.addWidget(self.fast_start_off_toggle, 8, 2)
        
            # --------------Ручной режим-------------
       
        self.manual_settings_group_box = QGroupBox("Ручные настройки")
        self.manual_settings_group_box.setFont(self.label_font)
        self.manual_settings_layout = QGridLayout(self.manual_settings_group_box)
        self.manual_settings_layout.setSpacing(10)
        layout.addWidget(self.manual_settings_group_box)

        frequency_label = QLabel("Частота:")
        frequency_label.setFont(self.label_font)
        self.manual_settings_layout.addWidget(frequency_label, 0, 0)

        self.frequency_input = QLineEdit()
        self.frequency_input.setFont(self.input_font)
        self.frequency_input.setPlaceholderText("MHz")
        self.frequency_input.setFixedSize(180, 30)
        self.manual_settings_layout.addWidget(self.frequency_input, 0, 1, 1, 3)  # Занимает 3 столбца

        voltage_label = QLabel("Вольтаж:")
        voltage_label.setFont(self.label_font)
        self.manual_settings_layout.addWidget(voltage_label, 1, 0)

        self.voltage_input = QLineEdit()
        self.voltage_input.setFont(self.input_font)
        self.voltage_input.setPlaceholderText("V")
        self.voltage_input.setFixedSize(180, 30)
        self.manual_settings_layout.addWidget(self.voltage_input, 1, 1, 1, 3)  # Занимает 3 столбца

        fan_mode_label = QLabel("Режим кулеров:")
        fan_mode_label.setFont(self.label_font)
        self.manual_settings_layout.addWidget(fan_mode_label, 2, 0)

        self.manual_fan_mode_button_group = QButtonGroup()

        self.manual_fan_manual_toggle = QRadioButton("Ручной")
        self.manual_fan_manual_toggle.setFont(self.checkbox_font)
        self.manual_fan_manual_toggle.toggled.connect(self.on_manual_fan_manual_toggled)
        self.manual_fan_mode_button_group.addButton(self.manual_fan_manual_toggle)
        self.manual_settings_layout.addWidget(self.manual_fan_manual_toggle, 2, 1)

        self.manual_fan_manual_input = QLineEdit()
        self.manual_fan_manual_input.setFont(self.input_font)
        self.manual_fan_manual_input.setPlaceholderText("%")
        self.manual_fan_manual_input.setFixedSize(70, 30)
        self.manual_fan_manual_input.hide()
        self.manual_settings_layout.addWidget(self.manual_fan_manual_input, 2, 2)

        self.manual_fan_auto_toggle = QRadioButton("Автофан")
        self.manual_fan_auto_toggle.setFont(self.checkbox_font)
        self.manual_fan_auto_toggle.toggled.connect(self.on_manual_fan_auto_toggled)
        self.manual_fan_mode_button_group.addButton(self.manual_fan_auto_toggle)
        self.manual_settings_layout.addWidget(self.manual_fan_auto_toggle, 3, 1)

        self.manual_fan_auto_input = QLineEdit()
        self.manual_fan_auto_input.setFont(self.input_font)
        self.manual_fan_auto_input.setPlaceholderText("°C")
        self.manual_fan_auto_input.setFixedSize(70, 30)
        self.manual_fan_auto_input.hide()
        self.manual_settings_layout.addWidget(self.manual_fan_auto_input, 3, 2)

        self.manual_fan_immersion_toggle = QRadioButton("Иммерсия")
        self.manual_fan_immersion_toggle.setFont(self.checkbox_font)
        self.manual_fan_mode_button_group.addButton(self.manual_fan_immersion_toggle)
        self.manual_settings_layout.addWidget(self.manual_fan_immersion_toggle, 4, 1, 1, 2)  # Занимает 2 столбца

        hashboard_check_label = QLabel("Проверка хэш плат:")
        hashboard_check_label.setFont(self.label_font)
        self.manual_settings_layout.addWidget(hashboard_check_label, 5, 0)

        self.manual_hashboard_check_button_group = QButtonGroup()

        self.manual_hashboard_check_on_toggle = QRadioButton("вкл")
        self.manual_hashboard_check_on_toggle.setFont(self.checkbox_font) 
        self.manual_hashboard_check_button_group.addButton(self.manual_hashboard_check_on_toggle)
        self.manual_settings_layout.addWidget(self.manual_hashboard_check_on_toggle, 5, 1)

        self.manual_hashboard_check_off_toggle = QRadioButton("выкл")  
        self.manual_hashboard_check_off_toggle.setFont(self.checkbox_font)
        self.manual_hashboard_check_button_group.addButton(self.manual_hashboard_check_off_toggle)
        self.manual_settings_layout.addWidget(self.manual_hashboard_check_off_toggle, 5, 2)

        autorestart_label = QLabel("Авторестарт:")
        autorestart_label.setFont(self.label_font) 
        self.manual_settings_layout.addWidget(autorestart_label, 6, 0)

        self.manual_autorestart_button_group = QButtonGroup()

        self.manual_autorestart_on_toggle = QRadioButton("вкл")
        self.manual_autorestart_on_toggle.setFont(self.checkbox_font)
        self.manual_autorestart_on_toggle.toggled.connect(self.on_manual_autorestart_toggled)
        self.manual_autorestart_button_group.addButton(self.manual_autorestart_on_toggle)  
        self.manual_settings_layout.addWidget(self.manual_autorestart_on_toggle, 6, 1)

        self.manual_autorestart_input = QLineEdit()
        self.manual_autorestart_input.setFont(self.input_font)
        self.manual_autorestart_input.setPlaceholderText("%") 
        self.manual_autorestart_input.setFixedSize(60, 30)
        self.manual_autorestart_input.hide()
        self.manual_settings_layout.addWidget(self.manual_autorestart_input, 6, 1, 1, 1, Qt.AlignRight)

        self.manual_autorestart_off_toggle = QRadioButton("выкл")
        self.manual_autorestart_off_toggle.setFont(self.checkbox_font)
        self.manual_autorestart_button_group.addButton(self.manual_autorestart_off_toggle)
        self.manual_settings_layout.addWidget(self.manual_autorestart_off_toggle, 6, 2)   

        voltage_adaptation_label = QLabel("Адаптация вольтажа:")
        voltage_adaptation_label.setFont(self.label_font)
        self.manual_settings_layout.addWidget(voltage_adaptation_label, 7, 0)

        self.manual_voltage_adaptation_button_group = QButtonGroup()

        self.manual_voltage_adaptation_on_toggle = QRadioButton("вкл") 
        self.manual_voltage_adaptation_on_toggle.setFont(self.checkbox_font)
        self.manual_voltage_adaptation_button_group.addButton(self.manual_voltage_adaptation_on_toggle)
        self.manual_settings_layout.addWidget(self.manual_voltage_adaptation_on_toggle, 7, 1)

        self.manual_voltage_adaptation_off_toggle = QRadioButton("выкл")
        self.manual_voltage_adaptation_off_toggle.setFont(self.checkbox_font)
        self.manual_voltage_adaptation_button_group.addButton(self.manual_voltage_adaptation_off_toggle)  
        self.manual_settings_layout.addWidget(self.manual_voltage_adaptation_off_toggle, 7, 2)

        fast_start_label = QLabel("Быстрый старт:")  
        fast_start_label.setFont(self.label_font)
        self.manual_settings_layout.addWidget(fast_start_label, 8, 0)

        self.manual_fast_start_button_group = QButtonGroup()

        self.manual_fast_start_on_toggle = QRadioButton("вкл")
        self.manual_fast_start_on_toggle.setFont(self.checkbox_font)
        self.manual_fast_start_button_group.addButton(self.manual_fast_start_on_toggle)
        self.manual_settings_layout.addWidget(self.manual_fast_start_on_toggle, 8, 1)  

        self.manual_fast_start_off_toggle = QRadioButton("выкл") 
        self.manual_fast_start_off_toggle.setFont(self.checkbox_font)
        self.manual_fast_start_button_group.addButton(self.manual_fast_start_off_toggle)
        self.manual_settings_layout.addWidget(self.manual_fast_start_off_toggle, 8, 2)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        layout.addLayout(button_layout)

        self.ok_button = QPushButton("OK")
        self.ok_button.setFont(self.button_font)
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setFont(self.button_font)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.pool_manager = self.parent().pool_manager

        # Подключение обработчика события
        self.profile_mode_checkbox.toggled.connect(self.on_profile_mode_toggled)
        self.manual_mode_checkbox.toggled.connect(self.on_manual_mode_toggled)
        
        # Изначально скрываем настройки
        self.settings_group_box.hide()
        self.manual_settings_group_box.hide()
                
        def set_profile_data(self, profile_data):
            self.profile_data = profile_data
            
            # Обновляем элементы управления в соответствии с данными профиля
            self.profile_combo.clear()
         #   print(f"Profile data in set_profile_data: {profile_data}")  # Добавляем отладочный вывод

            if profile_data:
                for ip, profiles in profile_data.items():
                    if profiles:
                        for profile_name, value in profiles.items():
                            self.profile_combo.addItem(f"{profile_name} - {value}")
                            #print(f"Added profile: {profile_name} - {value}")  # Добавляем отладочный вывод
                    else:
                        self.profile_combo.addItem(f"Нет данных профиля для {ip}")
                      #  print(f"Added 'Нет данных профиля для {ip}'")  # Добавляем отладочный вывод
            else:
                self.profile_combo.addItem("Нет данных профиля")
              #  print("Added 'Нет данных профиля'")  # Добавляем отладочный вывод

            pass  
    def on_manual_fan_toggled(self, checked):
        self.manual_fan_input.setVisible(checked)
    
    def on_autofan_toggled(self, checked):
        self.autofan_input.setVisible(checked)
        
    def on_autorestart_toggled(self, checked):
        self.autorestart_input.setVisible(checked)
        
    def set_selected_ips(self, ips):
        self.selected_ips = ips
        self.load_profiles()
        
    def load_profiles(self):
        profile_data = {}
        for ip in self.selected_ips:
            profile = self.parse_profile_data(ip)
            if profile:
                profile_data[ip] = profile

        self.set_profile_data(profile_data)
    
    def on_profile_mode_toggled(self, checked):
        self.settings_group_box.setVisible(checked)
        if checked:
            # Очищаем комбобокс профилей
            self.profile_combo.clear()
            
            # Проверяем, есть ли данные профиля
            if self.profile_data:
                # Получаем первый IP-адрес с непустыми данными профиля
                first_ip_with_profile = next(iter(self.profile_data))
                profiles = self.profile_data[first_ip_with_profile]
                
                # Добавляем профили в комбобокс
                for profile_name, value in profiles.items():
                    self.profile_combo.addItem(f"{profile_name} - {value}")
            else:
                self.profile_combo.addItem("Нет данных профиля")

    def get_settings(self):
        mode_chain = "0" if self.stock_mode_checkbox.isChecked() else "1" if self.profile_mode_checkbox.isChecked() else "2"

        settings = {
            "mode-chain": mode_chain,
            "volt-cor": self.voltage_corr_input.text(),
            "fan-chek": False,
            "wdt-chek": self.autorestart_on_toggle.isChecked(),
            "volt-corr": self.voltage_adaptation_on_toggle.isChecked(),
            "first-start": self.fast_start_on_toggle.isChecked()
        }

        if self.autorestart_on_toggle.isChecked():
            settings["wdt-proc"] = self.autorestart_input.text()

        if mode_chain in ["1", "2"]:  # если выбран режим "Профиля" или ручной режим
            if mode_chain == "1":
                profile_value = self.get_selected_profile()
                if profile_value:
                    settings["freq-prof"] = profile_value
            else:  # mode_chain == "2"
                settings["freq-chain"] = self.frequency_input.text()
                settings["volt-chain"] = self.voltage_input.text()

            if self.manual_fan_toggle.isChecked() or self.manual_fan_manual_toggle.isChecked():
                settings["bitmain-fan-ctrl"] = True
                settings["bitmain-fan-pwm"] = self.manual_fan_input.text() if mode_chain == "1" else self.manual_fan_manual_input.text()
            elif self.autofan_toggle.isChecked() or self.manual_fan_auto_toggle.isChecked():
                settings["bitmain-fan-ctrl"] = False
                settings["temp-target"] = self.autofan_input.text() if mode_chain == "1" else self.manual_fan_auto_input.text()
            elif self.immersion_toggle.isChecked() or self.manual_fan_immersion_toggle.isChecked():
                settings["bitmain-fan-ctrl"] = False
                settings["fan-chek"] = True
            else:
                settings["bitmain-fan-ctrl"] = False
            
            settings["wdt-chek"] = self.autorestart_on_toggle.isChecked() if mode_chain == "1" else self.manual_autorestart_on_toggle.isChecked()
            
            if settings["wdt-chek"]:
                settings["wdt-proc"] = self.autorestart_input.text() if mode_chain == "1" else self.manual_autorestart_input.text()
            
            settings["volt-corr"] = self.voltage_adaptation_on_toggle.isChecked() if mode_chain == "1" else self.manual_voltage_adaptation_on_toggle.isChecked()
            settings["first-start"] = self.fast_start_on_toggle.isChecked() if mode_chain == "1" else self.manual_fast_start_on_toggle.isChecked()

        if self.normal_mode_checkbox.isChecked():
            settings["miner-mode"] = "0"
        elif self.sleep_mode_checkbox.isChecked():
            settings["miner-mode"] = "1"


        return settings
            
    def parse_profile_data(self, ip):
        miner_html_url = f"http://{ip}/miner.html"
      #  print(f"Parsing profile data from {miner_html_url}")
        def try_password(pwd):
            try:
                response = requests.get(miner_html_url, auth=HTTPDigestAuth(username, pwd), 
                                        headers={'Accept-Encoding': 'gzip, deflate'}, 
                                        timeout=5)
                if response.status_code == 200:
                    html_content = response.text
                    match = re.search(r'<script.*?src="(/js/miner\.\w+\.js)"', html_content)
                    if match:
                        miner_js_path = match.group(1)
                        miner_js_url = f"http://{ip}{miner_js_path}"                        
                        response = requests.get(miner_js_url, auth=HTTPDigestAuth(username, pwd), 
                                                headers={'Accept-Encoding': 'gzip, deflate'}, 
                                                timeout=5)
                        if response.status_code == 200:
                            data = response.text                            
                            pattern = r"freqLevelS:\s*{(.*?)}"
                            match = re.search(pattern, data, re.DOTALL)
                            if match:
                                profile_data = match.group(1)                                
                                pairs = re.findall(r'"(.*?)"\s*:\s*(\d+)', profile_data)
                                profile_dict = {key: int(value) for key, value in pairs}                                
                                return profile_dict, pwd
                            else:
                                print("Profile data not found in miner.js")
                        else:
                            print(f"Failed to retrieve miner.js. Status code: {response.status_code}")
                else:
                    print(f"Failed to retrieve {miner_html_url} with password: {pwd}. Status code: {response.status_code}")
            except requests.RequestException:
                pass
            return None, pwd
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_pwd = {executor.submit(try_password, pwd): pwd for pwd in password}
            for future in as_completed(future_to_pwd):
                result, pwd = future.result()
                if result:
                    print(f"Received profile data from {ip} with password: {pwd}")
                    return result
                else:
                    print(f"Failed to get profile data from {ip} with password: {pwd}")
        print(f"Failed to get profile data from {ip} with any password")
        return None
     
    def get_selected_profile(self):
        selected_profile = self.profile_combo.currentText()
        if selected_profile:
            profile_value = selected_profile.split(" - ")[1]
            return profile_value
        return None
        
    def on_manual_mode_toggled(self, checked):
        self.manual_settings_group_box.setVisible(checked)
        if checked:
            # Здесь можно добавить логику для инициализации настроек ручного режима
            pass

    def on_manual_fan_manual_toggled(self, checked):
        self.manual_fan_manual_input.setVisible(checked)

    def on_manual_fan_auto_toggled(self, checked):
        self.manual_fan_auto_input.setVisible(checked)

    def on_manual_autorestart_toggled(self, checked):
        self.manual_autorestart_input.setVisible(checked)
        
    def set_profile_data(self, profile_data):
        self.profile_data = profile_data
        
        # Обновляем элементы управления в соответствии с данными профиля
        self.profile_combo.clear()
        if profile_data:
            for ip, profile in profile_data.items():
                if profile:
                    for profile_name, value in profile.items():
                        self.profile_combo.addItem(f"{profile_name} - {value}")
                else:
                    self.profile_combo.addItem(f"Нет данных профиля для {ip}")
        else:
            self.profile_combo.addItem("Нет данных профиля")
            
class SortFilterProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        leftData = self.sourceModel().data(left, Qt.UserRole)
        rightData = self.sourceModel().data(right, Qt.UserRole)
        
        if isinstance(leftData, (int, float)) and isinstance(rightData, (int, float)):
            return leftData < rightData
        
        return super().lessThan(left, right)
        
class AsicNameSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки имени асика")
        
        self.scale = parent.scale if parent else 1
        self.setGeometry(300, 200, int(300 * self.scale), int(200 * self.scale))

        self.label_font = QFont()
        self.label_font.setPointSize(int(8.5 * self.scale))
        
        self.checkbox_font = QFont()
        self.checkbox_font.setPointSize(int(8.5 * self.scale))
        
        self.button_font = QFont()
        self.button_font.setPointSize(int(8.5 * self.scale))
        
        self.input_font = QFont()
        self.input_font.setPointSize(int(8.5 * self.scale))

        self.layout = QVBoxLayout(self)

        type_name_label = QLabel("Тип настройки имени:")
        type_name_label.setFont(self.label_font)
        self.layout.addWidget(type_name_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Фиксированное имя", "Последовательная нумерация", "По IP", "Конструктор"])
        self.type_combo.currentIndexChanged.connect(self.update_settings_visibility)
        self.type_combo.setFont(self.input_font)
        self.type_combo.setFixedSize(int(300 * self.scale), int(40 * self.scale))
        self.layout.addWidget(self.type_combo)

        fixed_name_label = QLabel("Фиксированное имя:")
        fixed_name_label.setFont(self.label_font)
        self.layout.addWidget(fixed_name_label)

        self.fixed_name_input = QLineEdit()
        self.fixed_name_input.setFont(self.input_font)
        self.fixed_name_input.setFixedSize(int(300 * self.scale), int(40 * self.scale))
        self.layout.addWidget(self.fixed_name_input)

        start_num_label = QLabel("Начальный номер:")
        start_num_label.setFont(self.label_font)
        self.layout.addWidget(start_num_label)

        self.start_num_input = QSpinBox()
        self.start_num_input.setMinimum(1)
        self.start_num_input.setMaximum(9999)
        self.start_num_input.setFont(self.input_font)
        self.start_num_input.setFixedSize(int(150 * self.scale), int(40 * self.scale))
        self.layout.addWidget(self.start_num_input)

        self.constructor_widget = QWidget()
        self.constructor_layout = QVBoxLayout(self.constructor_widget)
        self.part_layouts = []
        for i in range(3):
            part_layout = QHBoxLayout()
            part_label = QLabel(f"Часть {i+1}:")
            part_label.setFont(self.label_font)
            part_combo = QComboBox()
            part_combo.addItems(["Не использовать", "Порядковый номер", "IP-адрес", "Фиксированное имя"])
            part_combo.setFont(self.input_font)
            part_input = QLineEdit()
            part_input.setPlaceholderText("Введите фиксированное имя")
            part_input.setEnabled(False)
            part_input.setFont(self.input_font)
            part_combo.currentIndexChanged.connect(lambda _, i=i: self.toggle_part_input(i))
            part_layout.addWidget(part_label)
            part_layout.addWidget(part_combo)
            part_layout.addWidget(part_input)
            self.part_layouts.append((part_combo, part_input))
            self.constructor_layout.addLayout(part_layout)

        self.separator_label = QLabel("Разделитель:")
        self.separator_label.setFont(self.label_font)
        self.separator_input = QLineEdit(".")
        self.separator_input.setFont(self.input_font)
        self.separator_input.setFixedSize(int(150 * self.scale), int(40 * self.scale))
        self.constructor_layout.addWidget(self.separator_label)
        self.constructor_layout.addWidget(self.separator_input)

        self.constructor_start_num_label = QLabel("Начальный номер:")
        self.constructor_start_num_label.setFont(self.label_font)
        self.constructor_start_num_input = QSpinBox()
        self.constructor_start_num_input.setMinimum(1)
        self.constructor_start_num_input.setMaximum(9999)
        self.constructor_start_num_input.setFont(self.input_font)
        self.constructor_start_num_input.setFixedSize(int(150 * self.scale), int(40 * self.scale))
        self.constructor_layout.addWidget(self.constructor_start_num_label)
        self.constructor_layout.addWidget(self.constructor_start_num_input)

        self.layout.addWidget(self.constructor_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.setFont(self.button_font)
        self.layout.addWidget(self.button_box)

        self.update_settings_visibility()

    def toggle_part_input(self, index):
        combo, input_field = self.part_layouts[index]
        input_field.setEnabled(combo.currentText() == "Фиксированное имя")

    def update_settings_visibility(self):
        self.fixed_name_input.setVisible(self.type_combo.currentText() == "Фиксированное имя")
        self.start_num_input.setVisible(self.type_combo.currentText() == "Последовательная нумерация")
        self.constructor_widget.setVisible(self.type_combo.currentText() == "Конструктор")  # Управляем видимостью виджета конструктора

    def get_settings(self):
        if self.type_combo.currentText() == "Конструктор":
            parts = []
            for combo, input_field in self.part_layouts:
                if combo.currentText() == "Фиксированное имя":
                    parts.append(input_field.text())
                elif combo.currentText() != "Не использовать":
                    parts.append(combo.currentText())

            return {
                "type": "Конструктор",
                "parts": parts,
                "separator": self.separator_input.text(),
                "start_num": self.constructor_start_num_input.value()
            }
        else:
            return {
                "type": self.type_combo.currentText(),
                "fixed_name": self.fixed_name_input.text(),
                "start_num": self.start_num_input.value()
            }

class PoolsListWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Список сохраненных пулов")
        
        self.scale = parent.scale if parent else 1
        
        self.button_font = QFont()
        self.button_font.setPointSize(int(9 * self.scale))
        
        self.label_font = QFont()
        self.label_font.setPointSize(int(9 * self.scale))
        
        self.setGeometry(100, 100, int(800 * self.scale), int(600 * self.scale))

        layout = QVBoxLayout(self)

        self.pools_list = QListWidget()
        self.pools_list.setFont(self.label_font)
        layout.addWidget(self.pools_list)

        buttons_layout = QHBoxLayout()
        
        self.select_button = self.create_scaled_button("Выбрать", self.on_select)
        buttons_layout.addWidget(self.select_button)

        self.add_button = self.create_scaled_button("Добавить новый", self.on_add)
        buttons_layout.addWidget(self.add_button)

        self.delete_button = self.create_scaled_button("Удалить", self.on_delete)
        buttons_layout.addWidget(self.delete_button)

        layout.addLayout(buttons_layout)

    def create_scaled_button(self, text, connection):
        button = QPushButton(text, self)
        button.clicked.connect(connection)
        button.setFont(self.button_font)
        return button

    def update_pools_list(self, saved_pools):
        self.pools_list.clear()
        for pools in saved_pools:
            pool_info = []
            for pool in pools:
                if pool["url"] and pool["user"]:
                    pool_info.append(f"{pool['url']} ({pool['user']})")
            self.pools_list.addItem(" | ".join(pool_info))

    def on_select(self):
        selected = self.pools_list.currentRow()
        if selected >= 0:
            self.parent().load_selected_pools(selected)
            self.close()

    def on_add(self):
        add_window = AddPoolsWindow(self)
        if add_window.exec_() == QDialog.Accepted:
            new_pools = add_window.get_pools()
            self.parent().saved_pools.append(new_pools)
            self.update_pools_list(self.parent().saved_pools)

    def on_delete(self):
        selected = self.pools_list.currentRow()
        if selected >= 0:
            del self.parent().saved_pools[selected]
            self.update_pools_list(self.parent().saved_pools)
            
class AddPoolsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить новые пулы")
        
        self.scale = parent.scale if parent else 1
        
        self.button_font = QFont()
        self.button_font.setPointSize(int(9 * self.scale))
        
        self.label_font = QFont()
        self.label_font.setPointSize(int(9 * self.scale))
        
        self.input_font = QFont()
        self.input_font.setPointSize(int(9 * self.scale))
        
        self.setGeometry(100, 100, int(1000 * self.scale), int(800 * self.scale))
        
        self.main_layout = QVBoxLayout(self)

        self.pool_inputs = []
        for i in range(3):
            pool_layout = QFormLayout()
            url_input = QLineEdit(self)
            worker_input = QLineEdit(self)
            password_input = QLineEdit(self)
            
            url_input.setFont(self.input_font)
            worker_input.setFont(self.input_font)
            password_input.setFont(self.input_font)
            
            pool_layout.addRow(QLabel(f"URL пула {i+1}:", self), url_input)
            pool_layout.addRow(QLabel(f"Воркер {i+1}:", self), worker_input)
            pool_layout.addRow(QLabel(f"Пароль {i+1}:", self), password_input)
            
            for j in range(pool_layout.rowCount()):
                pool_layout.itemAt(j, QFormLayout.LabelRole).widget().setFont(self.label_font)
            
            self.pool_inputs.append((url_input, worker_input, password_input))
            self.main_layout.addLayout(pool_layout)

        self.save_button = QPushButton("Сохранить", self)
        self.save_button.setFont(self.button_font)
        self.save_button.clicked.connect(self.accept)
        self.main_layout.addWidget(self.save_button)

    # ... (остальные методы остаются без изменений)

    def get_pools(self):
        return [
            {
                "url": inputs[0].text(),
                "user": inputs[1].text(),
                "pass": inputs[2].text()
            }
            for inputs in self.pool_inputs
        ]
 
       
class WorkerSignals(QObject):
    progress = pyqtSignal(int, int)  # Current progress, total
    data_fetched = pyqtSignal(tuple)
    stop_signal = pyqtSignal()
    finished = pyqtSignal()
    

class Worker(QRunnable):
    def __init__(self, choice, ip_list, signals, found_ips=None):
        super().__init__()
        self.choice = choice
        self.ip_queue = Queue()
        for ip in ip_list:
            self.ip_queue.put(ip)
        self.signals = signals
        self.found_ips = found_ips if found_ips else set()
        self._is_running = True
        self.signals.stop_signal.connect(self.stop)
        self.handle_cvitek = None

    def run(self):
        total = self.ip_queue.qsize()
        combined_data = []

        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            while not self.ip_queue.empty() and self._is_running:
                ip = self.ip_queue.get()
                if ip not in self.found_ips:
                    future = executor.submit(self.process_ip, ip)
                    futures.append(future)

            for index, future in enumerate(futures):
                if not self._is_running:
                    break
                ip_data = future.result()
                if ip_data[1]:  # If stats is not None, treat it as a found IP
                    if self.handle_cvitek:
                        self.handle_cvitek(ip_data[0])
                    self.found_ips.add(ip_data[0])
                combined_data.append(ip_data)
                self.signals.data_fetched.emit(ip_data)
                self.signals.progress.emit(index + 1, total)
        self.signals.finished.emit()

    def process_ip(self, ip):
        if check_api(ip):
            stats = get_stats(ip)
            if stats:
                config = get_config(ip)
            else:
                config = None
            return ip, stats, config
        else:
            return ip, None, None

    def stop(self):
        self._is_running = False
        
class ApplySettingsThread(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(bool)

    def __init__(self, pool_manager, ips, settings, batch_size=10):
        super().__init__()
        self.pool_manager = pool_manager
        self.ips = ips
        self.settings = settings
        self.batch_size = batch_size  # Добавляем атрибут batch_size
        self.canceled = False

    def run(self):
        results = self.pool_manager.set_miner_conf(self.ips, self.settings, batch_size=self.batch_size)
        for index, (ip, success, message) in enumerate(results, 1):
            if self.canceled:
                self.finished.emit(False)
                return
            self.progress_updated.emit(index)
            QEventLoop().processEvents()  # Обрабатываем события интерфейса

        self.finished.emit(True)

    def cancel(self):
        self.canceled = True

def show_apply_settings_progress(self, ips, settings):
    progress_dialog = QProgressDialog("Настройки применяются. Пожалуйста, подождите...", "Отмена", 0, len(ips), self)
    progress_dialog.setWindowTitle("Применение настроек")
    progress_dialog.setFixedSize(400, 120)
    progress_dialog.setWindowModality(Qt.ApplicationModal)

    # Создаем и запускаем поток
    apply_thread = ApplySettingsThread(self.pool_manager, ips, settings, batch_size=10)
    apply_thread.progress_updated.connect(progress_dialog.setValue)
    apply_thread.finished.connect(progress_dialog.accept)

    # Подключаем кнопку отмены
    progress_dialog.canceled.connect(apply_thread.cancel)

    apply_thread.start()
    progress_dialog.exec()

    if progress_dialog.wasCanceled():
        self.show_message("Применение настроек", "Применение настроек было отменено.", duration=5)
        print("Настройки были отменены пользователем.")
    else:
        self.show_message("Применение настроек", "Настройки были применены.", duration=5)
        print("Настройки успешно применены.")
    
class ApplyPoolsThread(QThread):
    progress_updated = pyqtSignal(int, int, str)
    finished = pyqtSignal()

    def __init__(self, selected_ips, selected_pools, pool_manager):
        super().__init__()
        self.selected_ips = selected_ips
        self.selected_pools = selected_pools
        self.pool_manager = pool_manager

    def run(self):
        total_ips = len(self.selected_ips)
        for index, ip in enumerate(self.selected_ips, 1):
            try:
                results = self.pool_manager.apply_pools([ip], self.selected_pools)
                for success, message in results:
                    if not success:
                        print(f"Не удалось применить пулы для {ip}: {message}")
            except Exception as e:
                print(f"Ошибка при применении пулов для {ip}: {str(e)}")
            finally:
                self.progress_updated.emit(index, total_ips, ip)
        
class MainWindow(BaseMainWindow):        
    def __init__(self):
        super().__init__()
        self.app_name = "AoS_Tools"
        self.signals = WorkerSignals()
        self.signals.data_fetched.connect(self.update_table_async, Qt.QueuedConnection)
        self.is_applying = False
        self.operation_cancelled = False
        self.operation_finished = False
        self.saved_pools = []  # Список для хранения сохраненных пулов
        self.pool_inputs = []
        self.apply_threads = []
        self.column_widths = []
        self.completed_threads = 0
        self.progress_dialog = None
        self.ip_to_index = {}
        self.asic_name_settings = None
        self.scale = self.calculate_scale()
        self.cvitek_lock = threading.Lock()
        self.auth_passwords = []
        # Initialize fonts
        self.label_font = QFont()
        self.label_font.setPointSize(int(9 * self.calculate_font_scale()))
        
        self.button_font = QFont()
        self.button_font.setPointSize(int(9 * self.calculate_font_scale()))
        
        self.input_font = QFont()
        self.input_font.setPointSize(int(9 * self.calculate_font_scale()))
        
        self.cvitek_stats = {
            'total': 0,
            'activated': 0,
            'failed': 0,
        }
        self.cvitek_stats_label = QLabel()
        self.cvitek_stats_label.setFont(self.label_font)
        self.update_cvitek_stats()
        
        logging.basicConfig(filename='app.log', level=logging.DEBUG)
        
        screen_width = QApplication.primaryScreen().size().width()
        screen_height = QApplication.primaryScreen().size().height()
        self.window_width = int(screen_width * 0.5)
        self.window_height = int(screen_height * 0.5)
        self.setGeometry(50, 50, self.window_width, self.window_height)
        
        
        self.input_font = QFont()
        self.input_font.setPointSize(int(9 * self.calculate_font_scale()))
        self.pool_manager = PoolManager(username="root", passwords=password)
        
        self.initUI()
       
        min_width = int(2350 * self.scale)  # Минимальная ширина на основе вашего разрешения
        min_height = int(1250 * self.scale)  # Минимальная высота на основе вашего разрешения
        self.setMinimumSize(min_width, min_height)
        #  Проверяем наличие файла settings.json
        if os.path.exists("settings.json"):
            self.load_settings()
        else:
        # Если файл не найден, устанавливаем размер окна в соответствии с минимальным размером
            self.resize(min_width, min_height)
        self.load_settings()
        self.ip_ranges = []
        self.timer = QTimer()
        self.worker = None
        self.found_ips = set()
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(100)
        self.monitoring_timer = QTimer()
        self.delay_timer = QTimer()
        self.monitoring_timer.timeout.connect(self.run_monitoring_scan)
        self.delay_timer.timeout.connect(self.start_monitoring)
        self.label_font = QFont()
        self.label_font.setPointSize(int(9 * self.calculate_font_scale()))

        self.button_font = QFont()
        self.button_font.setPointSize(int(9 * self.calculate_font_scale()))
        #app.setStyleSheet(f"QLabel{{font-size: {scaled_font_size}pt;}}")
        #Label font

    def calculate_scale(self):
        screen = QDesktopWidget().screenNumber(self)
        screen_size = QDesktopWidget().screenGeometry(screen)
        width = screen_size.width()
        height = screen_size.height()
        
        # Базовое разрешение (ваш экран)
        base_width = 2736
        base_height = 1824
        
        # Вычисляем масштаб
        scale_width = width / base_width
        scale_height = height / base_height
        
        # Используем среднее значение масштаба
        return (scale_width + scale_height) / 2
        
    def calculate_font_scale(self):
        scale = self.calculate_scale()
        # Нелинейная корректировка для лучшей адаптации
        if scale < 1:
            scale = pow(scale, 0.3)  # Увеличиваем для меньших экранов
        elif scale > 1:
            scale = pow(scale, 1.2)  # Уменьшаем для больших экранов
        return max(scale, 0.8)  # Минимальный масштаб 0.8
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.restore_column_widths()
        self.auto_resize_columns()
        
        # Подгоняем высоту строк под содержимое
        self.table.resizeRowsToContents()
        
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        
        if self.width() < self.minimumWidth() or self.height() < self.minimumHeight():
            self.resize(self.minimumWidth(), self.minimumHeight())

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)   

    def save_settings(self):
        settings = {
            "ip_ranges": self.ip_ranges,
            "current_ip_range": self.ip_range_entry.text(),
            "pools": [
                {
                    "url": self.pool_inputs[i][0].text(),
                    "user": self.pool_inputs[i][1].text(),
                    "pass": self.pool_inputs[i][2].text(),
                    "selected": self.pool_toggles[i].isChecked()
                } for i in range(3)
            ],
            "window_size": {
                "width": self.width(),
                "height": self.height(),
                "column_widths": self.column_widths
            },
            "auth_passwords": password  # Используем глобальную переменную password
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f, indent=4)

    def load_settings(self):
        global password  # Указываем, что используем глобальную переменную
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                settings = json.load(f)
        
            self.ip_ranges = settings.get("ip_ranges", [])
            self.update_ip_ranges()
            self.ip_range_entry.setText(settings.get("current_ip_range", ""))
            window_size = settings.get("window_size", {})
            if window_size:
                self.resize(window_size.get("width", self.width()),
                        window_size.get("height", self.height()))
            
            for i, pool in enumerate(settings.get("pools", [])):
                self.pool_inputs[i][0].setText(pool.get("url", ""))
                self.pool_inputs[i][1].setText(pool.get("user", ""))
                self.pool_inputs[i][2].setText(pool.get("pass", ""))
                self.pool_toggles[i].setChecked(pool.get("selected", False))

            # Загрузка ширины столбцов из настроек
            self.column_widths = settings.get("column_widths", [])
            
            # Восстановление ширины столбцов
            self.restore_column_widths()

            # Загрузка паролей для авторизации
            password.clear()
            password.extend(settings.get("auth_passwords", []))
            
    def show_message(self, title, message, duration=None):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setDefaultButton(QMessageBox.Ok) 
            
            if duration:
                QTimer.singleShot(duration * 1000, msg_box.close)

            msg_box.exec_()

    def update_ip_ranges(self):
        self.ip_ranges_listbox.clear()
        for name, ip_range in self.ip_ranges:
            self.ip_ranges_listbox.addItem(f"{name}: {ip_range}")
        
        if not self.ip_ranges:
            self.ip_ranges_listbox.addItem("Нет сохраненных диапазонов IP")
            
    def add_ip_range(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить диапазон IP")
        layout = QVBoxLayout()
        dialog.setGeometry(100, 100, int(400 * self.scale), int(300 * self.scale))

        # Поле для ввода имени диапазона
        name_label = QLabel("Имя диапазона:")
        name_label.setFont(self.label_font)
        name_input = QLineEdit()
        name_input.setFont(self.input_font)
        layout.addWidget(name_label)
        layout.addWidget(name_input)

        # Поле для ввода диапазона IP
        range_label = QLabel("Диапазон IP (используйте '-' для диапазонов или ',' для отдельных IP):")
        range_label.setFont(self.label_font)
        range_input = QTextEdit()
        range_input.setFont(self.input_font)
        range_input.setFixedHeight(int(150 * self.scale))
        range_input.setPlaceholderText("Например:\n192.168.1.1-192.168.1.255\nили\n10.0.0.1,10.0.0.5,10.0.0.10-10.0.0.20")
        layout.addWidget(range_label)
        layout.addWidget(range_input)
        

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            name = name_input.text().strip()
            ip_range = range_input.toPlainText().strip()
            if name and ip_range:
                self.ip_ranges.append((name, ip_range))
                self.update_ip_ranges()
            else:
                QMessageBox.warning(self, "Предупреждение", "Имя диапазона и диапазон IP не могут быть пустыми.")

    def remove_ip_range(self):
        selected = self.ip_ranges_listbox.currentRow()
        if selected >= 0:
            del self.ip_ranges[selected]
            self.update_ip_ranges()

    def auto_import_range(self):
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        base_ip = ".".join(local_ip.split(".")[:-1])
        ip_range = f"{base_ip}.1-{base_ip}.255"
        self.ip_range_entry.setText(ip_range)

    def save_ip_range(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Сохранить диапазон IP")
        layout = QVBoxLayout()

        # Поле для ввода имени диапазона
        name_label = QLabel("Имя диапазона:")
        name_label.setFont(self.label_font)
        name_input = QLineEdit()
        name_input.setFont(self.input_font)
        layout.addWidget(name_label)
        layout.addWidget(name_input)

        # Поле для ввода диапазона IP
        range_label = QLabel("Диапазон IP (используйте '-' для диапазонов или ',' для отдельных IP):")
        range_label.setFont(self.label_font)
        range_input = QTextEdit()
        range_input.setFont(self.input_font)
        range_input.setPlainText(self.ip_range_entry.text())
        layout.addWidget(range_label)
        layout.addWidget(range_input)

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            name = name_input.text().strip()
            ip_range = range_input.toPlainText().strip()
            if name and ip_range:
                self.ip_ranges.append((name, ip_range))
                self.update_ip_ranges()
            else:
                QMessageBox.warning(self, "Предупреждение", "Имя диапазона и диапазон IP не могут быть пустыми.")
                
    def select_ip_range(self):
        selected_items = self.ip_ranges_listbox.selectedItems()
        if selected_items:
            selected_ranges = []
            for item in selected_items:
                name, ip_range = item.text().split(": ")
                selected_ranges.append(ip_range)
            self.ip_range_entry.setText("; ".join(selected_ranges))
        else:
            self.ip_range_entry.clear()   
    def show_ip_range_context_menu(self, position):
        item = self.ip_ranges_listbox.itemAt(position)
        if not item:
            return  # Если клик был не на элементе, ничего не делаем

        menu = QMenu()
        edit_action = menu.addAction("Редактировать")
        
        action = menu.exec_(self.ip_ranges_listbox.mapToGlobal(position))
        
        if action == edit_action:
            try:
                self.edit_ip_range(item)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Произошла ошибка при редактировании: {str(e)}")
            
    def edit_ip_range(self, item):
        text = item.text()
        if ": " in text:
            current_name, current_range = text.split(": ", 1)
        else:
            current_name = ""
            current_range = text

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать диапазон IP")
        layout = QVBoxLayout()
        dialog.setGeometry(100, 100, int(400 * self.scale), int(300 * self.scale))

        name_label = QLabel("Имя диапазона:")
        name_label.setFont(self.label_font)
        name_input = QLineEdit(current_name)
        name_input.setFont(self.input_font)
        layout.addWidget(name_label)
        layout.addWidget(name_input)

        range_label = QLabel("Диапазон IP:")
        range_label.setFont(self.label_font)
        range_input = QTextEdit()
        range_input.setFont(self.input_font)
        range_input.setPlainText(current_range)
        layout.addWidget(range_label)
        layout.addWidget(range_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            new_name = name_input.text().strip()
            new_range = range_input.toPlainText().strip()
            if new_name and new_range:
                index = self.ip_ranges_listbox.row(item)
                self.ip_ranges[index] = (new_name, new_range)
                self.update_ip_ranges()
            else:
                QMessageBox.warning(self, "Предупреждение", "Имя диапазона и диапазон IP не могут быть пустыми.")
            
    def start_action(self, choice):
        global monitoring
        if choice == "1":
            self.table.setRowCount(0)  # Очистка таблицы перед началом нового сканирования
            self.found_ips.clear()  # Очистка найденных IP перед сканированием
            if self.cvitek_toggle.isChecked():
                self.reset_cvitek_stats()
        
        try:
            # Получаем выбранные диапазоны
            selected_items = self.ip_ranges_listbox.selectedItems()
            if selected_items:
                ip_list = []
                for item in selected_items:
                    name, ip_range = item.text().split(": ")
                    ip_list.extend(ip_range_to_list(ip_range))
            else:
                # Если ничего не выбрано, используем текущий введенный диапазон
                ip_range = self.ip_range_entry.text()
                ip_list = ip_range_to_list(ip_range)
            
            if not ip_list:
                raise ValueError("Не найдено действительных IP-адресов")
            
            self.scan_button.setEnabled(False)
            self.monitor_button.setEnabled(False)
            self.stop_button.show()
            self.progress_bar.setRange(0, len(ip_list))
            self.progress_bar.setValue(0)
            self.progress_bar_label.setText("Сканирование сети...")
            if choice == "3":
                monitoring = True

            if self.worker is not None:
                self.worker.signals.stop_signal.emit()
                
            
            self.signals.progress.connect(self.report_progress)
            
            self.signals.finished.connect(self.task_finished)

            self.worker = Worker(choice, ip_list, self.signals, self.found_ips)
            self.threadpool.start(self.worker)
            if self.cvitek_toggle.isChecked():
                self.worker.handle_cvitek = self.handle_cvitek
            if self.overheat_toggle.isChecked():
                self.start_overheat_protection()
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return
            
    async def run_worker(self, worker):
        await worker.run()

    def run_monitoring_scan(self):
        if self.cvitek_toggle.isChecked():
            for ip in self.found_ips:
                self.handle_cvitek(ip)
        if monitoring:
            self.update_found_ips()
            self.start_action("3")

    def update_found_ips(self):
        # Получаем список IP адресов из таблицы
        ip_in_table = set()
        for row in range(self.table.rowCount()):
            ip = self.table.item(row, 0).text()
            ip_in_table.add(ip)
        self.found_ips = ip_in_table

    def report_progress(self, current, total):
        self.progress_bar.setValue(current)
        self.progress_bar_label.setText(f"Сканирование: {current}/{total}")
        
    def update_progress(self, current, total, ip):
        if self.progress_dialog is not None:
            percentage = int((current / total) * 100)
            self.progress_dialog.setValue(percentage)
            self.progress_dialog.setLabelText(f"Применение пулов... ({current}/{total})\nТекущий IP: {ip}")
            
            if current == total:
                unique_ips = len(set(self.selected_ips))
                QMessageBox.information(self, "Завершено", f"Пулы успешно будут применены к {unique_ips}  IP-адресам.")
                self.progress_dialog.close()

    def start_monitoring(self):
        if self.cvitek_toggle.isChecked():
            self.reset_cvitek_stats()  # Сброс статистики CVITEK перед началом мониторинга
        self.start_action("3")

    def stop_action(self):
        global monitoring
        monitoring = False
        self.monitoring_timer.stop()  # Остановить таймер для мониторинга
        self.delay_timer.stop()  # Остановить таймер задержки
        self.progress_bar.setRange(0, 0)
        self.progress_bar_label.setText("Идёт остановка...")
        if self.worker is not None:
            self.worker.signals.stop_signal.emit()
            self.task_finished()
        else:
            self.stop_button.hide()
            self.scan_button.setEnabled(True)
            self.monitor_button.setEnabled(True)
            self.timer.stop()
            self.task_finished()

    def task_finished(self):
        global monitoring
        if not monitoring:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
            self.progress_bar_label.setText(f"Остановлено. Найдено {self.table.rowCount()} IP адресов.")
            self.stop_button.hide()
            self.scan_button.setEnabled(True)
            self.monitor_button.setEnabled(True)
        else:
            self.delay_timer.start(10000)  # Задержка перед следующим циклом мониторинга (10 секунд)
            
    @pyqtSlot(tuple)
    def update_table_async(self, ip_data):
        self.update_table([ip_data])
        
    def update_table(self, data):
        for item in data:
            ip, stats, config = item
            if stats is None:
                # Удаление IP из таблицы, если связь потеряна
                for row in range(self.table.rowCount()):
                    cell_item = self.table.item(row, 0)
                    if cell_item is not None and cell_item.text() == ip:
                        self.table.removeRow(row)
                        break
                continue

            stats_data = stats.get("stats", {}).get("STATS", [{}])[1] if len(stats.get("stats", {}).get("STATS", [])) > 1 else {}

            miner_type = stats.get("stats", {}).get("STATS", [{}])[0].get("Type", "")
            compile_time = stats.get("stats", {}).get("STATS", [{}])[0].get("CompileTime", "")
            if "AoS" in compile_time:
                miner_type += " [AoS]"

            fan_speeds = [stats_data.get("fan1", 0), stats_data.get("fan2", 0), stats_data.get("fan3", 0), stats_data.get("fan4", 0)]
            fan_speeds_str = f"{fan_speeds[0]}/{fan_speeds[1]}\n{fan_speeds[2]}/{fan_speeds[3]}" if len(fan_speeds) >= 4 else ""

            elapsed_seconds = stats_data.get("Elapsed", 0)
            elapsed_days = elapsed_seconds // 86400
            elapsed_hours = (elapsed_seconds % 86400) // 3600
            elapsed_minutes = (elapsed_seconds % 3600) // 60
            elapsed_str = f"{elapsed_days}d {elapsed_hours}h {elapsed_minutes}m"

            max_temp_chips = [stats_data.get("temp2_1", 0), stats_data.get("temp2_2", 0), stats_data.get("temp2_3", 0)]
            max_temp_chips_str = '/'.join(map(str, max_temp_chips))

            hashrate_5s = stats_data.get("GHS 5s", 0)
            hashrate_avg = stats_data.get("GHS av", 0)

            power_value = get_power(ip)
            pools_data = stats.get("pools", [])

            profile = ""
            is_stock_mode = False
            config = get_config(ip)
            if config:
                if config.get("bitmain-mode-level") == "0":
                    profile = "Stock Mode"
                    is_stock_mode = True
                elif config.get("bitmain-mode-level") == "1":
                    profile = config.get("bitmain-freq-prof", "")
                elif config.get("bitmain-different-freq"):
                    profile = f'{config.get("bitmain-freq-chain", "")}\n{config.get("bitmain-volt-chain", "")}'
                else:
                    profile = f'{config.get("bitmain-freq-chain0", "")}/{config.get("bitmain-freq-chain1", "")}/{config.get("bitmain-freq-chain2", "")}\n{config.get("bitmain-volt-chain", "")}'
            else:
                profile = ""

            # Проверяем, есть ли уже такой IP в таблице
            row_position = None
            for row in range(self.table.rowCount()):
                cell_item = self.table.item(row, 0)
                if cell_item is not None and cell_item.text() == ip:
                    row_position = row
                    break

            # Если IP не найден, добавляем новую строку
            if row_position is None:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)

            self.update_row(row_position, ip, profile, power_value, max_temp_chips_str, max_temp_chips, fan_speeds_str, elapsed_str, elapsed_seconds, miner_type, pools_data, is_stock_mode, config, hashrate_5s, hashrate_avg)

        self.restore_column_widths()
        self.auto_resize_columns()
        self.update_model_filter()
        self.update_model_settings_button_state()
        self.update_selected_settings_button_state()
        self.table.resizeRowsToContents()

    def update_row(self, row, ip, profile, power_value, max_temp_chips_str, max_temp_chips, fan_speeds_str,     elapsed_str, elapsed_seconds, miner_type, pools_data, is_stock_mode, config, hashrate_5s, hashrate_avg):
    
        self.table.setItem(row, 0, QTableWidgetItem(ip))

        item_profile = QTableWidgetItem(profile)
        item_profile.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 1, item_profile)

        item_power = QTableWidgetItem(power_value)
        item_power.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        item_power.setData(Qt.DisplayRole, float(power_value) if power_value else 0)
        self.table.setItem(row, 2, item_power)

        # Объединение модели асика и информации о наличии "AoS"
        self.table.setItem(row, 3, QTableWidgetItem(miner_type))
        
        item_rate_5s = QTableWidgetItem()
        item_rate_5s.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        # Преобразуем Gh/s в Th/s и округляем до целого числа
        rate_5s_th = round(hashrate_5s / 1000)
        display_value = f"{rate_5s_th} Th/s"
        item_rate_5s.setText(display_value)
        item_rate_5s.setData(Qt.UserRole, hashrate_5s)  # Сохраняем оригинальное значение для сортировки
        self.table.setItem(row, 4, item_rate_5s)

        item_rate_avg = QTableWidgetItem()
        item_rate_avg.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        # Преобразуем Gh/s в Th/s и округляем до целого числа
        rate_avg_th = round(hashrate_avg / 1000)
        display_value_avg = f"{rate_avg_th} Th/s"
        item_rate_avg.setText(display_value_avg)
        item_rate_avg.setData(Qt.UserRole, hashrate_avg)  # Сохраняем оригинальное значение для сортировки
        self.table.setItem(row, 5, item_rate_avg)

        item_max_temp_chips = QTableWidgetItem(max_temp_chips_str)
        item_max_temp_chips.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        item_max_temp_chips.setData(Qt.UserRole, max(max_temp_chips) if max_temp_chips else 0)
        self.table.setItem(row, 6, item_max_temp_chips)

        target_temp = config.get("bitmain-temp-target", "") if config else ""
        if is_stock_mode:
            combined_temp_fans = fan_speeds_str
        else:
            if target_temp:
                target_temp += "°C"
            combined_temp_fans = f"{target_temp} | {fan_speeds_str}"
        item_combined_temp_fans = QTableWidgetItem(combined_temp_fans)
        item_combined_temp_fans.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 7, item_combined_temp_fans)

        elapsed_str_item = QTableWidgetItem(elapsed_str)
        elapsed_str_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        elapsed_str_item.setData(Qt.UserRole, elapsed_seconds)  # Сохраняем секунды для сортировки
        self.table.setItem(row, 8, elapsed_str_item)

        pool_url = ""
        worker_user = ""
        if pools_data and isinstance(pools_data, list) and len(pools_data) > 0:
            pool_data = pools_data[0]
            pool_url = pool_data.get("URL", "")
            pool_url = pool_url.replace("stratum+tcp://", "").replace("stratum+ssl://", "")
            worker_user = pool_data.get("User", "")
        self.table.setItem(row, 9, QTableWidgetItem(pool_url))
        self.table.setItem(row, 10, QTableWidgetItem(worker_user))
        
    def adjust_column_widths(self):
        total_width = self.table.viewport().width()
        column_count = self.table.columnCount()

        # Подгоняем под содержимое
        self.table.resizeColumnsToContents()

        # Задаем коэффициенты ширины для определенных столбцов
        width_factors = [1] * column_count
        pool_column = 9  # Индекс столбца "Pool 1"
        speed_target_column = 7  # Индекс столбца "Speed | Target"
        width_factors[pool_column] = 2  # Делаем "Pool 1" в 2 раза шире
        width_factors[speed_target_column] = 1.5  # Делаем "Speed | Target" в 1.5 раза шире

        # Вычисляем общую ширину с учетом коэффициентов и минимальных ширин
        content_widths = [max(self.table.columnWidth(i) * width_factors[i], self.min_column_widths[i]) for i in range(column_count)]
        total_content_width = sum(content_widths)

        if total_content_width < total_width:
            # Растягиваем столбцы
            extra_width = total_width - total_content_width
            for i in range(column_count):
                ratio = (content_widths[i] / total_content_width) * width_factors[i]
                extra = int(extra_width * ratio)
                new_width = max(int(content_widths[i] / width_factors[i]) + extra, self.min_column_widths[i])
                self.table.setColumnWidth(i, new_width)
        else:
            # Пропорционально уменьшаем ширину столбцов, но не меньше минимальной
            ratio = total_width / total_content_width
            for i in range(column_count):
                new_width = max(int((content_widths[i] / width_factors[i]) * ratio), self.min_column_widths[i])
                self.table.setColumnWidth(i, new_width)

        self.save_column_widths()
    
    def restore_column_widths(self):
        for i, width in enumerate(self.column_widths):
            self.table.setColumnWidth(i, width)
  
    def auto_resize_columns(self):
        header = self.table.horizontalHeader()
        for column in range(self.table.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width = max(header.sectionSize(column), self.min_column_widths[column])
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            self.table.setColumnWidth(column, width)
            
    def save_column_widths(self):
        self.column_widths = [self.table.columnWidth(i) for i in range(self.table.columnCount())]

    def on_header_section_resized(self, logical_index, old_size, new_size):
        self.save_column_widths()

    def on_header_clicked(self, logical_index):
        if self.current_sort_column == logical_index:
            # Если тот же столбец, меняем порядок сортировки
            if self.current_sort_order == Qt.AscendingOrder:
                self.current_sort_order = Qt.DescendingOrder
            else:
                self.current_sort_order = Qt.AscendingOrder
        else:
            # Если новый столбец, устанавливаем возрастающий порядок
            self.current_sort_column = logical_index
            self.current_sort_order = Qt.AscendingOrder

        self.proxy_model.sort(self.current_sort_column, self.current_sort_order)
        self.table.horizontalHeader().setSortIndicator(self.current_sort_column, self.current_sort_order)
        
    def sort_table(self, column):
        current_order = self.table.horizontalHeader().sortIndicatorOrder()
        if self.table.horizontalHeader().sortIndicatorSection() == column:
            # Если кликнули на тот же столбец, меняем порядок сортировки
            new_order = Qt.DescendingOrder if current_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            # Если кликнули на новый столбец, начинаем с возрастающего порядка
            new_order = Qt.AscendingOrder
        
        self.table.sortItems(column, new_order)
        self.table.horizontalHeader().setSortIndicator(column, new_order)
        
    def on_row_double_click(self, index):
        row = index.row()
        ip = self.table.item(row, 0).text()
        url = f"http://{ip}/"
        webbrowser.open(url)
  
    def show_context_menu(self, position):
        menu = QMenu()
        copy_action = menu.addAction("Копировать")
        action = menu.exec_(self.table.viewport().mapToGlobal(position))
        if action == copy_action:
            self.copy_selected_data()
            
    def copy_selected_data(self):
        current_item = self.table.currentItem()
        if not current_item:
            return

        cell_text = current_item.text()
        clipboard = QApplication.clipboard()
        clipboard.setText(cell_text)
 
    def update_model_filter(self):
        models = set()
        for row in range(self.table.rowCount()):
            model = self.table.item(row, 3).text()
            models.add(model)

        self.model_filter.clear()
        self.model_filter.addItem("All Models")
        self.model_filter.addItems(sorted(models))   
    def filter_table(self, index):
        model = self.model_filter.itemText(index)
        for row in range(self.table.rowCount()):
            item_model = self.table.item(row, 3).text()
            if model == "All Models" or item_model == model:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)
        self.update_model_settings_button_state()
        self.update_selected_settings_button_state()
         
    def update_model_settings_button_state(self):
        selected_model = self.model_filter.currentText()
        self.model_settings_button.setEnabled("AoS" in selected_model)

    def update_selected_settings_button_state(self):
        selected_rows = self.table.selectionModel().selectedRows()
        has_aos = any("AoS" in self.table.item(index.row(), 3).text() for index in selected_rows)
        self.selected_settings_button.setEnabled(has_aos)

    def open_model_settings(self):
        selected_model = self.model_filter.currentText()
        if selected_model != "All Models":
            aos_ips = [self.table.item(row, 0).text() for row in range(self.table.rowCount())
                       if self.table.item(row, 3).text() == selected_model]

            if aos_ips:
                # Выбираем случайный IP-адрес из списка aos_ips
                random_ip = random.choice(aos_ips)
                
                dialog = AsicSettingsDialog(self)
                profile_data = dialog.parse_profile_data(random_ip)
                
                if profile_data:
                    dialog.set_profile_data({random_ip: profile_data})
                    
                    if dialog.exec_() == QDialog.Accepted:
                        settings = dialog.get_settings()
                        self.show_apply_settings_progress(aos_ips, settings)
            else:
                QMessageBox.warning(self, "Предупреждение", f"Нет доступных асиков модели {selected_model}.")
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите модель для настройки.")

    def open_selected_settings(self):
        # Получаем выбранные строки в таблице
        selected_rows = self.table.selectionModel().selectedRows()

        # Фильтруем выбранные IP-адреса, у которых в столбце Type указано "AoS"
        aos_ips = [self.table.item(index.row(), 0).text() for index in selected_rows
                   if "AoS" in self.table.item(index.row(), 3).text()]

        if aos_ips:
            dialog = AsicSettingsDialog(self)

            # Выбираем случайный IP-адрес из отфильтрованных
            first_ip = random.choice(aos_ips)
            profile = dialog.parse_profile_data(first_ip)

            if profile:
                # Передаем данные профиля в диалоговое окно
                dialog.set_profile_data({first_ip: profile})

                if dialog.exec_() == QDialog.Accepted:
                    settings = dialog.get_settings()
                    self.show_apply_settings_progress(aos_ips, settings)
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите асики с прошивкой AoS для настройки.")

    def apply_settings_to_all(self, settings):
        aos_ips = []
        for row in range(self.table.rowCount()):
            miner_type = self.table.item(row, 3).text()
            if "AoS" in miner_type:
                ip = self.table.item(row, 0).text()
                aos_ips.append(ip)

        for ip in aos_ips:
                    # Здесь будет реализована логика сохранения настроек и применения их к асикам с указанным IP
             pass

    def apply_settings_to_selected(self, settings):
        aos_ips = []
        selected_rows = self.table.selectionModel().selectedRows()
        for index in selected_rows:
            row = index.row()
            miner_type = self.table.item(row, 3).text()
            if "AoS" in miner_type:
                ip = self.table.item(row, 0).text()
                aos_ips.append(ip)

        for ip in aos_ips:
            # Здесь будет реализована логика сохранения настроек и применения их к асикам с указанным IP
            pass       

    def show_apply_settings_progress(self, ips, settings):
        progress_dialog = QProgressDialog("Настройки применяются. Пожалуйста, подождите ~20cек - ∞", "Отмена", 0, len(ips), self)
        progress_dialog.setWindowTitle("Применение настроек")
        progress_dialog.setFixedSize(650, 150)
        progress_dialog.setWindowModality(Qt.ApplicationModal)

        # Создаем и запускаем поток
        apply_thread = ApplySettingsThread(self.pool_manager, ips, settings)
        apply_thread.progress_updated.connect(progress_dialog.setValue)
        apply_thread.finished.connect(progress_dialog.accept)

        # Подключаем кнопку отмены
        progress_dialog.canceled.connect(apply_thread.cancel)

        apply_thread.start()
        progress_dialog.exec()

        if progress_dialog.wasCanceled():
            self.show_message("Применение настроек", "Применение настроек было отменено.", duration=5)
            print("Настройки были отменены пользователем.")
        else:
            self.show_message("Применение настроек", "Настройки были применены.", duration=5)
            print("Настройки успешно применены.")

    def on_thread_finished(self):
        self.completed_threads += 1
        if self.completed_threads == len(self.apply_threads):
            if self.progress_dialog is not None:
                self.progress_dialog.setValue(self.progress_dialog.maximum())
                self.progress_dialog.close()
             
            self.completed_threads = 0
            self.apply_threads = []
            if not self.operation_cancelled:
                QMessageBox.information(self, "Завершено", f"Пулы успешно применены к {len(self.selected_ips)} IP-адресам.")
            self.operation_cancelled = False

    def cvitek_toggled(self, checked):
        if checked:
            self.cvitek_toggle.setText("CVITEK (ON)")
            self.cvitek_stats_label.show()
        else:
            self.cvitek_toggle.setText("CVITEK")
            self.cvitek_stats_label.hide()
        self.reset_cvitek_stats()

    def check_cvitek(self, ip):
        url = f"http://{ip}/cgi-bin/miner_type.cgi"

        for pwd in password:  # Используем глобальный список паролей
            try:
                response = requests.get(url, auth=requests.auth.HTTPDigestAuth(username, pwd), timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("subtype", "").startswith("CVCtrl_"):
                        logging.info(f"Successful authentication for {ip} with password: {pwd}")
                        return True
            except requests.RequestException as e:
                logging.error(f"Error in check_cvitek for {ip} with password {pwd}: {str(e)}")

        logging.info(f"Failed to authenticate and check cvitek for {ip} with all passwords.")
        return False

    async def activate_cvitek_async(self, ip, username='miner', password='miner'):
        try:
            async with asyncssh.connect(ip, username=username, password=password, known_hosts=None) as conn:
                result = await conn.run('/nvdata/AntminerOS/aos_fw')
                logging.info(f"CVITEK activation command executed successfully on {ip}")
                return True

        except asyncssh.misc.PermissionDenied:
            logging.info(f"Authentication failed for {ip}. Firmware is already activated.")
            return "already_activated"

        except Exception as e:
            logging.error(f"Error in activate_cvitek for {ip}: {str(e)}")
            return False

    def handle_cvitek(self, ip):
        try:
            if self.check_cvitek(ip):
                with self.cvitek_lock:
                    self.cvitek_stats['total'] += 1

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.activate_cvitek_async(ip, 'miner', 'miner'))
                loop.close()

                if result is True:
                    logging.info(f"CVITEK activated for {ip}")
                    with self.cvitek_lock:
                        self.cvitek_stats['activated'] += 1
                elif result == "already_activated":
                    logging.info(f"CVITEK is already activated for {ip}")
                    with self.cvitek_lock:
                        self.cvitek_stats['activated'] += 1
                else:
                    logging.warning(f"CVITEK activation failed for {ip}")
                    with self.cvitek_lock:
                        self.cvitek_stats['failed'] += 1

            self.update_cvitek_stats()
        except Exception as e:
            logging.error(f"Error in handle_cvitek for {ip}: {str(e)}")
                        
    def update_cvitek_stats(self):
        try:
            with self.cvitek_lock:
                stats = self.cvitek_stats.copy()
            stats_text = (f"CVITEK Статистика: Всего CVCtrl_: {stats['total']}, "
                          f"Активировано: {stats['activated']}, "
                          f"Не удалось: {stats['failed']}")
           # print(f"Обновление статистики CVITEK: {stats_text}")  # Отладочный вывод
            QMetaObject.invokeMethod(self.cvitek_stats_label, "setText", 
                                     Qt.QueuedConnection,
                                     Q_ARG(str, stats_text))
        except Exception as e:
            logging.error(f"Error in update_cvitek_stats: {str(e)}")
            
    def reset_cvitek_stats(self):
        print("Сброс статистики CVITEK")  # Отладочный вывод
        self.cvitek_stats = {
            'total': 0,
            'activated': 0,
            'failed': 0
        }
        self.update_cvitek_stats()

    def start_overheat_protection(self):
        try:
            import overheat
            overheat.start_protection(self.found_ips)
        except ImportError:
            QMessageBox.warning(self, "Ошибка", "Файл overheat.py не найден.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось запустить защиту от перегрева: {str(e)}")

    def open_asic_name_settings(self):
        dialog = AsicNameSettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.asic_name_settings = dialog.get_settings()
            QMessageBox.information(self, "Успех", "Настройки имени асика сохранены")                    
        
    def update_asic_name_settings(self, new_settings):
        self.asic_name_settings = new_settings
        # Сбрасываем счетчики при изменении настроек
        self.ip_counters = {}
        self.global_counter = new_settings['start_num']
        
    def show_pools_list(self):
        self.pools_list_window = PoolsListWindow(self)
        self.pools_list_window.scale = self.scale  # Передаем масштаб
        self.pools_list_window.update_pools_list(self.saved_pools)
        self.pools_list_window.show()
        
    def save_current_pools(self):
        current_pools = []
        for i in range(3):
            pool_address, worker, password = self.pool_inputs[i]
            current_pools.append({
                "url": pool_address.text(),
                "user": worker.text(),
                "pass": password.text()
            })
        self.saved_pools.append(current_pools)
        QMessageBox.information(self, "Сохранено", "Пулы успешно сохранены")
        if hasattr(self, 'pools_list_window'):
            self.pools_list_window.update_pools_list(self.saved_pools)
           
    def on_save_pools_clicked(self):
        self.save_current_pools()
                
    def load_selected_pools(self, index):
        selected_pools = self.saved_pools[index]
        for i, pool in enumerate(selected_pools):
            if i < len(self.pool_inputs):
                self.pool_inputs[i][0].setText(pool["url"])
                self.pool_inputs[i][1].setText(pool["user"])
                self.pool_inputs[i][2].setText(pool["pass"])
        
    def get_new_worker_name(self, ip, worker, original_worker):
        settings = self.asic_name_settings
        print(f"Формирование имени воркера для IP: {ip}")
        print(f"Текущие настройки: {settings}")

        if not hasattr(self, 'ip_counters'):
            self.ip_counters = {}

        if not hasattr(self, 'global_counter') or self.global_counter < settings['start_num']:
            self.global_counter = settings['start_num']

        if settings['type'] == "Фиксированное имя":
            new_name = settings['fixed_name']
            print(f"Выбрано фиксированное имя: {new_name}")
        elif settings['type'] == "Последовательная нумерация":
            if ip not in self.ip_counters:
                self.ip_counters[ip] = self.global_counter
                self.global_counter += 1
            new_name = str(self.ip_counters[ip])
            print(f"Выбрана последовательная нумерация. IP: {ip}, Индекс: {new_name}")
        elif settings['type'] == "По IP":
            new_name = ip.replace(".", "_")
            print(f"Выбрано имя по IP: {new_name}")
        elif settings['type'] == "Конструктор":
            if ip not in self.ip_counters:
                self.ip_counters[ip] = self.global_counter
                self.global_counter += 1
            
            name_parts = []
            for part in settings['parts']:
                if part == "Порядковый номер":
                    name_parts.append(str(self.ip_counters[ip]))
                elif part == "IP-адрес":
                    name_parts.append(ip.replace(".", "_"))
                else:
                    name_parts.append(part)
            new_name = settings['separator'].join(name_parts)
            print(f"Выбран конструктор имени. Части: {settings['parts']}, Результат: {new_name}")
        else:
            print("Неизвестный тип настройки имени воркера")
            new_name = ""

        if "." in original_worker:
            worker_name, _ = original_worker.split(".", 1)
            result = f"{worker_name}.{new_name}"
        else:
            result = f"{original_worker}.{new_name}"

        print(f"Результат: {result}\n")
        return result
                
    def apply_selected_pools(self):
        selected_pools = []
        for i, toggle in enumerate(self.pool_toggles):
            pool_address, worker, password = self.pool_inputs[i]
            if toggle.isChecked():
                selected_pools.append({
                    "url": pool_address.text(),
                    "user": worker.text(),
                    "pass": password.text()
                })
            else:
                selected_pools.append({
                    "url": "",
                    "user": "",
                    "pass": ""
                })
        
        if any(pool["url"] for pool in selected_pools):
            dialog = QDialog(self)
            dialog.setWindowTitle("Выбор применения пулов")
            dialog.setFixedSize(600, 170)

            layout = QVBoxLayout()

            button_layout = QHBoxLayout()

            apply_all_button = QPushButton("Применить всем")
            apply_all_button.setFixedSize(int(220 * self.scale), int(40 * self.scale))
            apply_all_button.setFont(self.button_font)
            apply_all_button.clicked.connect(lambda: self.process_pool_application(selected_pools, True))
            button_layout.addWidget(apply_all_button)

            apply_selected_button = QPushButton("Применить выбранным")
            apply_selected_button.setFixedSize(int(280 * self.scale), int(40 * self.scale))
            apply_selected_button.setFont(self.button_font)
            apply_selected_button.clicked.connect(lambda: self.process_pool_application(selected_pools, False))
            button_layout.addWidget(apply_selected_button)

            layout.addLayout(button_layout)

            cancel_button = QPushButton("Отмена")
            cancel_button.setFixedSize(int(200 * self.scale), int(40 * self.scale))
            cancel_button.setFont(self.button_font)
            cancel_button.clicked.connect(dialog.reject)
            layout.addWidget(cancel_button, alignment=Qt.AlignHCenter)

            dialog.setLayout(layout)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "Предупреждение", "Пожалуйста, выберите хотя бы один пул для применения.")

    def process_pool_application(self, selected_pools, apply_to_all):
        if apply_to_all:
            selected_ips = [self.table.item(row, 0).text() for row in range(self.table.rowCount())]
        else:
            selected_ips = [self.table.item(row, 0).text() for row in range(self.table.rowCount()) 
                            if self.table.item(row, 0).isSelected()]
        
        if not selected_ips:
            QMessageBox.warning(self, "Предупреждение", "Пожалуйста, выберите IP-адреса в таблице.")
            return
                    
        self.selected_ips = selected_ips    
        
        self.progress_dialog = QProgressDialog("Применение пулов...", "Отмена", 0, len(selected_ips), self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setFixedSize(450, 150)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.canceled.connect(self.cancel_apply_pools)
        self.progress_dialog.show()

        self.completed_threads = 0
        self.apply_threads = []
        self.operation_cancelled = False
        
        for ip in selected_ips:
            if self.asic_name_settings:
                ip_pool_settings = []
                for pool in selected_pools:
                    if pool["url"]:
                        new_pool = pool.copy()
                        new_pool["user"] = self.get_new_worker_name(ip, pool["user"], pool["user"])
                        ip_pool_settings.append(new_pool)
                    else:
                        ip_pool_settings.append(pool)
            else:
                ip_pool_settings = selected_pools

            thread = ApplyPoolsThread([ip], ip_pool_settings, self.pool_manager)
            thread.progress_updated.connect(self.update_progress)
            thread.finished.connect(self.on_thread_finished)
            self.apply_threads.append(thread)
            thread.start()
            
            if self.asic_name_settings and self.asic_name_settings['type'] == "Конструктор" and "Порядковый номер" in self.asic_name_settings['parts']:
                if ip not in self.ip_to_index:
                    self.ip_to_index[ip] = self.asic_name_settings['start_num']
                self.ip_to_index[ip] += len(selected_pools)
        
        # Закрываем диалоговое окно выбора применения пулов
        self.sender().parent().accept()

    def cancel_apply_pools(self):
        self.operation_cancelled = True
        for thread in self.apply_threads:
            thread.terminate()
        self.completed_threads = 0
        self.apply_threads = []
        self.progress_dialog.close() 

    def show_progress_dialog(self, selected_ips):
        self.progress_dialog = QProgressDialog("Применение пулов...", "Отмена", 0, len(selected_ips), self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        #self.progress.setMinimumWidth(400)
        self.progress_dialog.show()  

    def open_settings_dialog(self):
        from settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.update_passwords, self)
        dialog.exec_()
    def update_passwords(self, passwords):
        global password
        password.clear()
        password.extend(passwords)
      #  print("Текущие пароли:", password)
        self.save_settings()
        
    def send_reboot_command(self, ip):
        url_reboot = f"http://{ip}/cgi-bin/reboot.cgi"
        
        def try_password(pwd):
            try:
                response = requests.get(url_reboot, auth=HTTPDigestAuth(username, pwd),
                                        headers={'Accept-Encoding': 'gzip, deflate'},
                                        timeout=1)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            return False
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_pwd = {executor.submit(try_password, pwd): pwd for pwd in password}
            for future in as_completed(future_to_pwd):
                if future.result():
                    return

    def reboot_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        selected_ips = [self.table.item(row.row(), 0).text() for row in selected_rows]
        if not selected_ips:
            QMessageBox.warning(self, "Предупреждение", "Выберите адреса для перезагрузки.")
            return

        if not self.show_reboot_confirmation(selected=True):
            return
        
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.send_reboot_command, ip) for ip in selected_ips]
            for _ in as_completed(futures):
                pass

    def reboot_all(self):
        if not self.table:
            return

        if not self.show_reboot_confirmation(selected=False):
            return

        ips = []
        for row in range(self.table.rowCount()):
            ip = self.table.item(row, 0).text()
            ips.append(ip)

        if not ips:
            return

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.send_reboot_command, ip) for ip in ips]
            for _ in as_completed(futures):
                pass

    def show_reboot_confirmation(self, selected=False):
        if selected:
            selected_rows = self.table.selectionModel().selectedRows()
            selected_ips = [self.table.item(row.row(), 0).text() for row in selected_rows]
            if not selected_ips:
                return False
            message = f"Перезапустить выбранные {len(selected_ips)} асиков?"
        else:
            total_ips = self.table.rowCount()
            if total_ips == 0:
                return False
            message = f"Перезапустить все {total_ips} асиков?"

        reply = QMessageBox.question(self, 'Подтверждение перезагрузки', message,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        return reply == QMessageBox.Yes
  
    def blink_selected(self):
        # Логика для моргания выбранным асиком
        pass

    def download_log(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            print("Нет выбранных IP-адресов")
            return

        save_dir = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения логов")
        if not save_dir:
            return

        for row in selected_rows:
            ip = self.table.item(row.row(), 0).text()
            url = f"http://{ip}/cgi-bin/hlog.cgi"
            log_data = None

            def try_password(pwd):
                try:
                    response = requests.get(url, auth=HTTPDigestAuth(username, pwd),
                                            headers={'Accept-Encoding': 'gzip, deflate'},
                                            timeout=1)
                    if response.status_code == 200:
                        return response.text, pwd
                except requests.RequestException:
                    pass
                return None, pwd

            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_pwd = {executor.submit(try_password, pwd): pwd for pwd in password}
                for future in as_completed(future_to_pwd):
                    log_data, pwd = future.result()
                    if log_data is not None:
                        break

            if log_data is not None:
                file_name = f"{ip.replace('.', '_')}.txt"
                file_path = os.path.join(save_dir, file_name)
                with open(file_path, 'w') as file:
                    file.write(log_data)
                print(f"Лог для {ip} сохранен в {file_path}")
            else:
                print(f"Не удалось получить лог для {ip}")
            
    def open_ip_reporter(self):
        # Логика для открытия IP Reporter
        pass
    def initUI(self):
        super().__init__()
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.progress_bar = None
        self.scale = self.calculate_scale()
        self.window_width = int(2736 * self.scale)
        self.window_height = int(1824 * self.scale)
        self.setGeometry(50, 50, self.window_width, self.window_height)
        self.label_font = QFont()
        self.label_font.setPointSize(int(8.5 * self.calculate_font_scale()))
        self.min_column_widths = [180, 180, 100, 100, 100, 100, 150, 210, 180, 200, 200]  # Замените на 

        self.button_font = QFont()
        self.button_font.setPointSize(int(8.5 * self.calculate_font_scale())) #button font
       # scaled_font_size = max(9, min(20, int(base_font_size * self.calculate_font_scale())))
        base_font_size = 9
                 
        # Create a splitter for the upper frame
        upper_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(upper_splitter)

        # Create a splitter for the upper frame
        upper_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(upper_splitter)

        # Left frame (IP ranges)
        left_frame = QWidget()
        left_layout = QVBoxLayout(left_frame)
        
        buttons_frame = QHBoxLayout()
        left_layout.addLayout(buttons_frame)
        buttons_frame.setSpacing(1) 

        add_button = QPushButton("+", self)
        add_button.setFont(self.button_font)
        add_button.setMaximumWidth(int(100 * self.scale))
        add_button.setMaximumHeight(int(50 * self.scale))
        add_button.clicked.connect(self.add_ip_range)
        buttons_frame.addWidget(add_button)

        remove_button = QPushButton("-", self)
        remove_button.setFont(self.button_font)
        remove_button.setMaximumWidth(int(100 * self.scale))
        remove_button.setMaximumHeight(int(50 * self.scale))
        remove_button.clicked.connect(self.remove_ip_range)
        buttons_frame.addWidget(remove_button)

        auto_button = QPushButton("Auto", self)        
        auto_button.setFont(self.button_font)
        auto_button.setMaximumWidth(int(100 * self.scale))
        auto_button.setMaximumHeight(int(50 * self.scale)) 
        auto_button.clicked.connect(self.auto_import_range)
        buttons_frame.addWidget(auto_button)

        ip_ranges_label = QLabel("IP Ranges:", self)
        ip_ranges_label.setFont(self.label_font)
        left_layout.addWidget(ip_ranges_label)

        self.ip_ranges_listbox = QListWidget(self)
        self.ip_ranges_listbox.setMaximumHeight(int(260 * self.scale))
        self.ip_ranges_listbox.setMaximumWidth(int(350 * self.scale))
        self.ip_ranges_listbox.setSelectionMode(QAbstractItemView.MultiSelection)
        self.ip_ranges_listbox.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ip_ranges_listbox.customContextMenuRequested.connect(self.show_ip_range_context_menu)
        left_layout.addWidget(self.ip_ranges_listbox)

        # Set minimum and maximum width for the left frame
        left_frame.setMinimumWidth(int(self.window_width * 0.1 * self.scale))  # 10% of window width
        left_frame.setMaximumWidth(int(self.window_width * 0.2 * self.scale))  # 20% of window width

        upper_splitter.addWidget(left_frame)

        # Middle frame (IP input and scan buttons)
        middle_frame = QWidget()
        middle_layout = QVBoxLayout(middle_frame)

        ip_range_label = QLabel("Введите диапазон IP-адресов (192.168.1.1-192.168.1.255):", self)
        ip_range_label.setFont(self.label_font)
        middle_layout.addWidget(ip_range_label)

        ip_range_entry_frame = QHBoxLayout()
        middle_layout.addLayout(ip_range_entry_frame)

        self.ip_range_entry = QLineEdit(self)
        self.ip_range_entry.setFont(self.input_font)
        ip_range_entry_frame.addWidget(self.ip_range_entry)

        save_button = QPushButton("Сохранить", self)
        save_button.setFont(self.button_font)
        save_button.clicked.connect(self.save_ip_range)
        ip_range_entry_frame.addWidget(save_button)

                # Верхний блок: Скан монитор стоп
        scan_monitor_frame = QHBoxLayout()
        middle_layout.addLayout(scan_monitor_frame)
        middle_layout.addSpacerItem(QSpacerItem(20, 25, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        self.scan_button = QPushButton("Сканировать сеть", self)
        self.scan_button.setFont(self.button_font)
        self.scan_button.clicked.connect(lambda: self.start_action("1"))
        scan_monitor_frame.addWidget(self.scan_button)

        self.monitor_button = QPushButton("Мониторить сеть", self)
        self.monitor_button.setFont(self.button_font)
        self.monitor_button.clicked.connect(self.start_monitoring)
        scan_monitor_frame.addWidget(self.monitor_button)

        self.stop_button = QPushButton("СТОП", self)  
        self.stop_button.setFont(self.button_font)
        self.stop_button.clicked.connect(self.stop_action)
        self.stop_button.hide()
        scan_monitor_frame.addWidget(self.stop_button)
   
        # Создаем основной контейнер для нижнего блока кнопок
        buttons_frame = QHBoxLayout()
        middle_layout.addLayout(buttons_frame)

        # Левый блок: Ребуты
        left_buttons_frame = QVBoxLayout()
        buttons_frame.addLayout(left_buttons_frame)

        reboot_frame = QHBoxLayout()
        reboot_frame.setSpacing(1)
        left_buttons_frame.addLayout(reboot_frame)

        self.reboot_selected_button = QPushButton("Ребут", self)
        self.reboot_selected_button.setFont(self.button_font)
        reboot_frame.addWidget(self.reboot_selected_button)

        self.reboot_all_button = QPushButton("Ребут всем", self)
        self.reboot_all_button.setFont(self.button_font)
        reboot_frame.addWidget(self.reboot_all_button)

        blink_frame = QHBoxLayout()
        blink_frame.setSpacing(1)
        left_buttons_frame.addLayout(blink_frame)

        self.blink_selected_button = QPushButton("Поморгать асиком", self)
        self.blink_selected_button.setFont(self.button_font)
        blink_frame.addWidget(self.blink_selected_button)

        self.download_log_button = QPushButton("Скачать лог", self)
        self.download_log_button.setFont(self.button_font)
        blink_frame.addWidget(self.download_log_button)
        
        left_buttons_frame.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        self.blink_selected_button.clicked.connect(self.blink_selected)
        self.download_log_button.clicked.connect(self.download_log)

        # Привязка функций к кнопкам
        self.reboot_selected_button.clicked.connect(self.reboot_selected)
        self.reboot_all_button.clicked.connect(self.reboot_all)

        # Правый блок: Майнинг и CVITEK
        right_buttons_frame = QVBoxLayout()
        buttons_frame.addLayout(right_buttons_frame)

        cvitek_frame = QHBoxLayout()
        cvitek_frame.setSpacing(1)
        right_buttons_frame.addLayout(cvitek_frame)

        self.overheat_toggle = QPushButton("Майним без перегрева", self)
        self.overheat_toggle.setFont(self.button_font)
        self.overheat_toggle.setCheckable(True)
        cvitek_frame.addWidget(self.overheat_toggle)

        self.cvitek_toggle = QPushButton("CVITEK", self)
        self.cvitek_toggle.setFont(self.button_font)
        self.cvitek_toggle.setCheckable(True)
        self.cvitek_toggle.toggled.connect(self.cvitek_toggled)
        cvitek_frame.addWidget(self.cvitek_toggle)        

        ip_reporter_button = QPushButton("IP Reporter", self)
        ip_reporter_button.setFont(self.button_font)  
        ip_reporter_button.clicked.connect(self.open_ip_reporter)
        right_buttons_frame.addWidget(ip_reporter_button)

        right_buttons_frame.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Fixed))
     # Установим минимальную ширину для среднего фрейма
        middle_frame.setMinimumWidth(int(self.window_width * 0.3 * self.scale))  # 30% от ширины окна

        upper_splitter.addWidget(middle_frame)

        # Right frame (Pools)
        right_frame = QWidget()
        right_layout = QGridLayout(right_frame)
        
        self.pool_toggles = []
        self.pool_inputs = []
        toggle_buttons_layout = QHBoxLayout() 
              
        for i in range(3):
            pool_column_layout = QVBoxLayout()
            right_layout.addLayout(pool_column_layout, 0, i)

            pool_label = QLabel(f"Pool address {i + 1}:", self)
            pool_label.setFont(self.label_font)
            pool_column_layout.addWidget(pool_label)
            pool_address_input = QLineEdit(self)
            pool_address_input.setFont(self.input_font)
            pool_column_layout.addWidget(pool_address_input)

            worker_label = QLabel(f"Worker {i + 1}:", self)
            worker_label.setFont(self.label_font)
            pool_column_layout.addWidget(worker_label)
            worker_input = QLineEdit(self)
            worker_input.setFont(self.input_font)
            pool_column_layout.addWidget(worker_input)

            password_label = QLabel(f"Password {i + 1}:", self)
            password_label.setFont(self.label_font)
            pool_column_layout.addWidget(password_label)
            password_input = QLineEdit(self)
            password_input.setFont(self.input_font)
            pool_column_layout.addWidget(password_input)
            
            toggle_button = QPushButton(f"Применить {i + 1} пул", self)
            toggle_button.setMaximumWidth(int(420 * self.scale))
            toggle_button.setMaximumHeight(int(40 * self.scale))
            toggle_button.setFont(self.button_font)
            toggle_button.setCheckable(True)
            toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 2px solid #999999;
                    height: 40px;
                }
                QPushButton:checked {
                    background-color: #add8e6;
                    border: 2px solid #4a90e2;
                }
            """)
            pool_column_layout.addWidget(toggle_button)
            
                      
            self.pool_toggles.append(toggle_button)
            self.pool_inputs.append((pool_address_input, worker_input, password_input))
           # Добавляем соответствующие кнопки под каждым тогглом
            if i == 0:
                asic_name_button = QPushButton("Настройка имени асика", self)
                asic_name_button.setFont(self.button_font)
                asic_name_button.clicked.connect(self.open_asic_name_settings)
                asic_name_button.setFixedSize(int(300 * self.scale), int(55 * self.scale))
                button_layout = QHBoxLayout()
                button_layout.addStretch()
                button_layout.addWidget(asic_name_button)
                button_layout.addStretch()
                pool_column_layout.addLayout(button_layout)
            elif i == 1:
                apply_pools_button = QPushButton("Применить пулы", self)
                apply_pools_button.setFont(self.button_font)
                apply_pools_button.clicked.connect(self.apply_selected_pools)
                apply_pools_button.setFixedSize(int(300 * self.scale), int(55 * self.scale))
                button_layout = QHBoxLayout()
                button_layout.addStretch()
                button_layout.addWidget(apply_pools_button)
                button_layout.addStretch()
                pool_column_layout.addLayout(button_layout)
            elif i == 2:
                buttons_layout = QHBoxLayout()
                
                list_pools_button = QPushButton("Список пулов", self)
                list_pools_button.setFont(self.button_font)
                list_pools_button.clicked.connect(self.show_pools_list)
                list_pools_button.setFixedSize(int(210 * self.scale), int(55 * self.scale))
                
                save_pools_button = QPushButton("Сохранить пулы", self)
                save_pools_button.setFont(self.button_font)
                save_pools_button.clicked.connect(self.save_current_pools)
                save_pools_button.setFixedSize(int(210 * self.scale), int(55 * self.scale))
                
                buttons_layout.addStretch()
                buttons_layout.addWidget(list_pools_button)
                buttons_layout.addWidget(save_pools_button)
                buttons_layout.addStretch()

                pool_column_layout.addLayout(buttons_layout)

            # Добавляем растяжение снизу, чтобы кнопки не прижимались к нижнему краю
            pool_column_layout.addStretch()
        
        
        right_frame.setMinimumWidth(int(self.window_width * 0.3 * self.scale))  # 30% от ширины окна
        right_frame.setMaximumWidth(int(self.window_width * 0.6 * self.scale))  # 60% от ширины окна
       
        upper_splitter.addWidget(right_frame)

        # Set initial sizes for the splitter
        upper_splitter.setSizes([
         int(self.window_width * 0.17), 
         int(self.window_width * 0.22), 
         int(self.window_width * 0.45)
        ])
        
        self.model_filter = QComboBox(self)
        self.model_filter.addItem("All Models")
        self.model_filter.currentIndexChanged.connect(self.filter_table)
        self.model_filter.setFixedSize(int(280 * self.scale), int(35 * self.scale))
        
        font = QFont()
        font.setPointSize(int(9 * self.scale))  # Установите желаемый размер шрифта
        self.model_filter.setFont(font)
        
        combo_box_frame = QHBoxLayout()
        combo_box_frame.addWidget(self.model_filter)

        self.model_settings_button = QPushButton("AoS по модели", self)
        self.model_settings_button.setFont(self.button_font)
        self.model_settings_button.clicked.connect(self.open_model_settings)
        self.model_settings_button.setFixedSize(int(200 * self.scale), int(35 * self.scale))
        combo_box_frame.addWidget(self.model_settings_button)

        self.selected_settings_button = QPushButton("AoS выбранных", self)
        self.selected_settings_button.setFont(self.button_font)
        self.selected_settings_button.clicked.connect(self.open_selected_settings)
        self.selected_settings_button.setFixedSize(int(200 * self.scale), int(35 * self.scale))
        combo_box_frame.addWidget(self.selected_settings_button)

        combo_box_frame.addStretch()
        middle_layout.addLayout(combo_box_frame)
        
        progress_bar_frame = QHBoxLayout()
        main_layout.addLayout(progress_bar_frame)

        self.progress_bar = QProgressBar(self)
        progress_bar_frame.addWidget(self.progress_bar)

        self.progress_bar_label = QLabel("Готово к сканированию.", self)
        self.progress_bar_label.setFont(self.label_font)
        progress_bar_frame.addWidget(self.progress_bar_label)
        

        self.table = QTableWidget(self)
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels(["IP", "Profile", "Power", "Type", "Hash Rate RT", "Hash Rate avg", "Temperature", "Speed | Target", "Elapsed", "Pool 1", "Worker 1"])
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        # Добавьте следующий код здесь
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #a0a0a0; /* бока */
                border: none; 
            }
            QTableWidget::item {
                border-bottom: 1px solid #a0a0a0; /* низы */
            }
            QTableWidget::item:selected {
                background-color: #e6f3ff;  /* Светло-голубой цвет для выбранных элементов */
                color: black;  /* Цвет текста в выбранных элементах */
            }
            QTableWidget::item:selected:focus {
                background-color: #cce8ff;  /* Немного более темный оттенок для элемента в фокусе */
            }
        """)
        self.table.setWordWrap(True)
        
        header = self.table.horizontalHeader()
        header.sectionResized.connect(self.on_header_section_resized)
        header.setSectionsMovable(True)
        header.setDragEnabled(True)
        header.setDragDropMode(QAbstractItemView.InternalMove)
        header.setStretchLastSection(True)
        
        
        # Новый код для сортировки
        self.proxy_model = SortFilterProxyModel()
        self.proxy_model.setSourceModel(self.table.model())
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        self.current_sort_column = -1
        self.current_sort_order = Qt.AscendingOrder

        self.update_model_filter()

        
        self.table.itemSelectionChanged.connect(self.update_selected_settings_button_state)

        for i in range(self.table.columnCount()):
            self.table.setColumnWidth(i, self.min_column_widths[i])
        #Размер
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(i, QHeaderView.Interactive)

        main_layout.addWidget(self.table)

# Установка начальной ширины столбцов           
        self.table.setColumnWidth(2, 10)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self.on_row_double_click)
        main_layout.addWidget(self.table)

        stats_layout = QHBoxLayout()

        self.cvitek_stats_label = QLabel()
        self.cvitek_stats_label.setFont(self.label_font)
        self.cvitek_stats_label.hide()  # Скрываем изначально
        stats_layout.addWidget(self.cvitek_stats_label)

        self.stats_label = QLabel(self)
        stats_layout.addWidget(self.stats_label)

        stats_layout.addStretch()

        settings_button = QPushButton("Настройки", self)
        settings_button.clicked.connect(self.open_settings_dialog)
        settings_button.setFixedSize(200, 35)
        stats_layout.addWidget(settings_button)

        main_layout.addLayout(stats_layout)

        self.adjust_column_widths()
        
def main():
    sys.excepthook = exception_handler       

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("AoS_Tools")
    app.setOrganizationName("AoS_Firmware")
    app.setApplicationVersion("1.0")
    
    icon_path = resource_path('aos.ico')  # Используйте .png или .ico, но одинаково везде
    
    app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())