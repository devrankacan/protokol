#!/bin/bash
# Genexa CRO — VPS Deployment Script
# Ubuntu 22.04 / 24.04
# Çalıştır: bash deploy.sh

set -e

APP_DIR="/opt/genexa-cro"
SERVICE_NAME="genexa-cro"
PORT=8000

echo "======================================================"
echo "  Genexa CRO — VPS Kurulum Scripti"
echo "======================================================"

# ── 1. Sistem paketleri ────────────────────────────────────────────────────────
echo ""
echo ">> Sistem paketleri güncelleniyor..."
apt-get update -qq

echo ">> Gerekli paketler kuruluyor..."
apt-get install -y -qq \
  python3 python3-pip python3-venv git \
  libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 \
  libffi-dev libcairo2 libpangocairo-1.0-0 \
  fonts-liberation fonts-dejavu \
  ufw curl

echo "   ✓ Sistem paketleri hazır"

# ── 2. Uygulama dizini ─────────────────────────────────────────────────────────
echo ""
echo ">> Uygulama dizini hazırlanıyor: $APP_DIR"
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/uploads"
mkdir -p "$APP_DIR/reports"
echo "   ✓ Dizinler oluşturuldu"

# ── 3. Repo klonla veya güncelle ───────────────────────────────────────────────
echo ""
if [ -d "$APP_DIR/.git" ]; then
  echo ">> Mevcut repo güncelleniyor..."
  git -C "$APP_DIR" pull origin claude/discuss-website-project-MwN4j
else
  echo ">> Repo klonlanıyor..."
  git clone \
    --branch claude/discuss-website-project-MwN4j \
    https://github.com/devrankacan/protokol.git \
    "$APP_DIR"
fi
echo "   ✓ Kod hazır"

# ── 4. Python sanal ortamı ─────────────────────────────────────────────────────
echo ""
echo ">> Python virtual environment oluşturuluyor..."
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip -q
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q
echo "   ✓ Python bağımlılıkları kuruldu"

# ── 5. .env dosyası ────────────────────────────────────────────────────────────
echo ""
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo ""
  echo "   ⚠️  .env dosyası oluşturuldu."
  echo "   Lütfen aşağıdaki komutla API key ve şifreyi girin:"
  echo ""
  echo "   nano $APP_DIR/.env"
  echo ""
  echo "   Gerekli değerler:"
  echo "   ANTHROPIC_API_KEY=sk-ant-..."
  echo "   APP_PASSWORD=güçlü-bir-şifre"
  echo "   SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
  echo ""
  read -p "   .env düzenlemeyi şimdi yapmak ister misiniz? (e/h): " answer
  if [ "$answer" = "e" ]; then
    nano "$APP_DIR/.env"
  fi
else
  echo "   ✓ .env dosyası zaten mevcut"
fi

# ── 6. Systemd servisi ─────────────────────────────────────────────────────────
echo ""
echo ">> Systemd servisi yapılandırılıyor..."

cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Genexa CRO Protocol Analyzer
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}/backend
Environment="PATH=${APP_DIR}/.venv/bin"
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
echo "   ✓ Systemd servisi oluşturuldu ve etkinleştirildi"

# ── 7. Firewall ────────────────────────────────────────────────────────────────
echo ""
echo ">> Firewall yapılandırılıyor..."
ufw allow ssh
ufw allow "${PORT}/tcp"
ufw --force enable
echo "   ✓ Port ${PORT} açıldı"

# ── 8. Servisi başlat ──────────────────────────────────────────────────────────
echo ""
echo ">> Servis başlatılıyor..."
systemctl restart "${SERVICE_NAME}"
sleep 3

if systemctl is-active --quiet "${SERVICE_NAME}"; then
  echo "   ✓ Servis çalışıyor!"
else
  echo "   ✗ Servis başlatılamadı. Log:"
  journalctl -u "${SERVICE_NAME}" --no-pager -n 20
  exit 1
fi

# ── Özet ───────────────────────────────────────────────────────────────────────
echo ""
echo "======================================================"
echo "  KURULUM TAMAMLANDI ✓"
echo "======================================================"
echo ""
echo "  Adres:   http://$(curl -s ifconfig.me 2>/dev/null || echo 'IP_ADRESINIZ'):${PORT}"
echo "  Şifre:   .env dosyasındaki APP_PASSWORD değeri"
echo ""
echo "  Faydalı komutlar:"
echo "  Durum   → systemctl status ${SERVICE_NAME}"
echo "  Log     → journalctl -u ${SERVICE_NAME} -f"
echo "  Restart → systemctl restart ${SERVICE_NAME}"
echo "  Durdur  → systemctl stop ${SERVICE_NAME}"
echo ""
