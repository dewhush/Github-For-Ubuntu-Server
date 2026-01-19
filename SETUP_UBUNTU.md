# 🚀 Setup Guide untuk Ubuntu Server

Panduan lengkap untuk menjalankan GitHub Followers Bot di Ubuntu Server.

## 📋 Prerequisites

- Ubuntu Server 20.04+ (atau Debian-based distro)
- Python 3.10+
- Git

---

## 🔧 Step 1: Update System & Install Dependencies

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install Python dan pip
sudo apt install python3 python3-pip python3-venv git -y

# Verify installation
python3 --version
pip3 --version
```

---

## 📦 Step 2: Clone Repository

```bash
# Clone dari GitHub (ganti dengan repo URL kamu)
git clone https://github.com/dewhush/Github-For-Ubuntu-Server.git

# Masuk ke direktori project
cd Github-For-Ubuntu-Server
```

---

## 🐍 Step 3: Setup Virtual Environment

```bash
# Buat virtual environment
python3 -m venv venv

# Aktifkan virtual environment
source venv/bin/activate

# Pastikan pip up-to-date
pip install --upgrade pip
```

---

## 📥 Step 4: Install Requirements

```bash
pip install -r requirements.txt
```

---

## ⚙️ Step 5: Edit Config (Jika diperlukan)

```bash
# Edit config.json jika perlu ubah target
nano config.json

# Edit .env jika perlu ubah token
nano .env
```

---

## 🚀 Step 6: Jalankan Bot

### Option A: Jalankan Langsung (Foreground)
```bash
python3 main.py
```

### Option B: Jalankan dengan Screen (Background)
```bash
# Install screen jika belum ada
sudo apt install screen -y

# Buat session baru
screen -S github-bot

# Jalankan bot
source venv/bin/activate
python3 main.py

# Detach dari screen: tekan Ctrl+A lalu D
# Re-attach: screen -r github-bot
```

### Option C: Jalankan dengan tmux (Background)
```bash
# Install tmux
sudo apt install tmux -y

# Buat session baru
tmux new -s github-bot

# Jalankan bot
source venv/bin/activate
python3 main.py

# Detach dari tmux: tekan Ctrl+B lalu D
# Re-attach: tmux attach -t github-bot
```

---

## 🔄 Step 7: Setup Systemd Service (Auto-start on Boot)

Buat file service:
```bash
sudo nano /etc/systemd/system/github-bot.service
```

**Isi file:**
```ini
[Unit]
Description=GitHub Followers Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/Github-For-Ubuntu-Server
Environment="PATH=/home/YOUR_USERNAME/Github-For-Ubuntu-Server/venv/bin"
ExecStart=/home/YOUR_USERNAME/Github-For-Ubuntu-Server/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

> ⚠️ **Ganti `YOUR_USERNAME` dengan username Ubuntu kamu!**

**Enable dan start service:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable github-bot

# Start service
sudo systemctl start github-bot

# Cek status
sudo systemctl status github-bot
```

**Perintah berguna:**
```bash
# Stop bot
sudo systemctl stop github-bot

# Restart bot
sudo systemctl restart github-bot

# Lihat logs
sudo journalctl -u github-bot -f
```

---

## 🛠️ Troubleshooting

### Error: ModuleNotFoundError
```bash
# Pastikan virtual environment aktif
source venv/bin/activate
pip install -r requirements.txt
```

### Error: Permission denied
```bash
chmod +x main.py
chmod +x start.sh
```

### Melihat Log Bot
```bash
# Systemd logs
sudo journalctl -u github-bot -f --no-pager
```

---

## 🎉 Quick Start

```bash
chmod +x start.sh
./start.sh
```

---

*Created by: dewhush*
