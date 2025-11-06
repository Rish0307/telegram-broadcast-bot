# Oracle Cloud Free Setup for Telegram Bot

## Step 1: Create Oracle Cloud Account
1. Go to https://oracle.com/cloud/free
2. Click "Start for free"
3. Fill in details (requires phone verification)
4. **No credit card required for Always Free tier**

## Step 2: Create Ubuntu VM
1. Go to "Create a VM instance"
2. Choose:
   - **Image**: Ubuntu 20.04 or 22.04
   - **Shape**: VM.Standard.E2.1.Micro (Always Free)
   - **RAM**: 1GB (Always Free)
3. Download SSH keys (save the private key file)
4. Click "Create"

## Step 3: Connect to VM
```bash
# Windows (use PuTTY or WSL)
ssh -i your-private-key.pem ubuntu@YOUR-VM-IP

# Or use Oracle Cloud Shell (browser-based)
```

## Step 4: Setup Bot on VM
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip git -y

# Clone your repository
git clone https://github.com/Rish0307/telegram-broadcast-bot.git
cd telegram-broadcast-bot

# Install requirements
pip3 install -r requirements.txt

# Create .env file
echo "BOT_TOKEN=8209185155:AAHWUrMimRj06E18wuRcji8IF8EtPezDGt0" > .env

# Test bot
python3 scheduled_broadcast_bot.py
```

## Step 5: Create Systemd Service (24/7 Running)
```bash
# Create service file
sudo nano /etc/systemd/system/telegram-bot.service

# Paste this content:
[Unit]
Description=Telegram Broadcast Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/telegram-broadcast-bot
ExecStart=/usr/bin/python3 scheduled_broadcast_bot.py
Restart=always
RestartSec=10
Environment=BOT_TOKEN=8209185185155:AAHWUrMimRj06E18wuRcji8IF8EtPezDGt0

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Check status
sudo systemctl status telegram-bot
```

## Your bot is now running 24/7 for FREE! ✅

### Management Commands:
- Check status: `sudo systemctl status telegram-bot`
- Stop bot: `sudo systemctl stop telegram-bot`
- Start bot: `sudo systemctl start telegram-bot`
- View logs: `journalctl -u telegram-bot -f`