#!/bin/bash
# Genexa CRO — VPS Deployment Script
# Ubuntu 22.04 / 24.04  |  Nginx reverse proxy pattern
# Çalıştır: bash deploy.sh

set -e

APP_DIR="/opt/genexa-protokol"
SERVICE_NAME="genexa-protokol"
INTERNAL_PORT=13055      # uvicorn bu portu dinler (localhost only)
PUBLIC_PORT=3055         # nginx dışarıya bu portu açar
NGINX_CONF="genexa-protokol"

echo "======================================================"
echo "  Genexa CRO Protokol Analizörü — VPS Kurulum"
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
  ufw

echo "   ✓ Sistem paketleri hazır"

# ── 2. Uygulama dizini ─────────────────────────────────────────────────────────
echo ""
echo ">> Uygulama dizini: $APP_DIR"
mkdir -p "$APP_DIR/uploads"
mkdir -p "$APP_DIR/reports"

# ── 3. Repo klonla veya güncelle ───────────────────────────────────────────────
echo ""
if [ -d "$APP_DIR/.git" ]; then
  echo ">> Mevcut repo güncelleniyor..."
  git -C "$APP_DIR" pull origin claude/discuss-website-project-MwN4j
else
  # Dizin var ama git repo değil — temizle ve klonla
  if [ -d "$APP_DIR" ]; then
    echo ">> Dizin mevcut ama git repo değil, temizleniyor..."
    # uploads ve reports klasörlerini koru
    cp -r "$APP_DIR/uploads" /tmp/genexa-uploads-backup 2>/dev/null || true
    cp -r "$APP_DIR/reports" /tmp/genexa-reports-backup 2>/dev/null || true
    rm -rf "$APP_DIR"
  fi
  echo ">> Repo klonlanıyor..."
  git clone \
    --branch claude/discuss-website-project-MwN4j \
    https://github.com/devrankacan/protokol.git \
    "$APP_DIR"
  # Yedekleri geri yükle
  cp -r /tmp/genexa-uploads-backup/. "$APP_DIR/uploads/" 2>/dev/null || true
  cp -r /tmp/genexa-reports-backup/. "$APP_DIR/reports/" 2>/dev/null || true
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
  GENERATED_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
  sed -i "s/change-this-to-a-random-secret-key-in-production/$GENERATED_KEY/" "$APP_DIR/.env"

  echo ""
  echo "   ⚠️  .env dosyası oluşturuldu. ANTHROPIC_API_KEY ve APP_PASSWORD girilmeli."
  echo ""
  echo "   Şimdi düzenlemek ister misiniz? (e/h):"
  read -r answer
  if [ "$answer" = "e" ]; then
    nano "$APP_DIR/.env"
  fi
else
  echo "   ✓ .env dosyası zaten mevcut"
fi

# ── 6. Systemd servisi ─────────────────────────────────────────────────────────
echo ""
echo ">> Systemd servisi oluşturuluyor..."

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
ExecStart=${APP_DIR}/.venv/bin/uvicorn main:app --host 127.0.0.1 --port ${INTERNAL_PORT} --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
echo "   ✓ Systemd servisi hazır (uvicorn → 127.0.0.1:${INTERNAL_PORT})"

# ── 7. Nginx yapılandırması ────────────────────────────────────────────────────
echo ""
echo ">> Nginx yapılandırması ekleniyor..."

cat > /etc/nginx/sites-available/${NGINX_CONF} << EOF
server {
    listen ${PUBLIC_PORT};
    server_name _;

    client_max_body_size 60M;

    # Zaman aşımı — Claude analizi uzun sürebilir
    proxy_read_timeout 180s;
    proxy_connect_timeout 10s;
    proxy_send_timeout 180s;

    location / {
        proxy_pass http://127.0.0.1:${INTERNAL_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }
}
EOF

# sites-enabled'a ekle (varsa üzerine yaz)
ln -sf /etc/nginx/sites-available/${NGINX_CONF} /etc/nginx/sites-enabled/${NGINX_CONF}

# Nginx yapılandırmasını test et
nginx -t
systemctl reload nginx
echo "   ✓ Nginx yapılandırması aktif (port ${PUBLIC_PORT} → 127.0.0.1:${INTERNAL_PORT})"

# ── 8. Firewall ────────────────────────────────────────────────────────────────
echo ""
echo ">> Firewall: port ${PUBLIC_PORT} açılıyor..."
ufw allow ssh
ufw allow "${PUBLIC_PORT}/tcp"
ufw --force enable
echo "   ✓ Port ${PUBLIC_PORT} açıldı"

# ── 9. Servisi başlat ──────────────────────────────────────────────────────────
echo ""
echo ">> Servis başlatılıyor..."
systemctl restart "${SERVICE_NAME}"
sleep 4

if systemctl is-active --quiet "${SERVICE_NAME}"; then
  echo "   ✓ Servis çalışıyor!"
else
  echo "   ✗ Servis başlatılamadı. Log:"
  journalctl -u "${SERVICE_NAME}" --no-pager -n 30
  exit 1
fi

# ── Özet ───────────────────────────────────────────────────────────────────────
echo ""
echo "======================================================"
echo "  KURULUM TAMAMLANDI ✓"
echo "======================================================"
echo ""
echo "  Adres  →  http://$(curl -s ifconfig.me 2>/dev/null || echo '158.220.115.16'):${PUBLIC_PORT}"
echo "  Şifre  →  .env dosyasındaki APP_PASSWORD değeri"
echo ""
echo "  Mevcut siteler etkilenmedi:"
echo "    genexacro  (port 8080)  → değişmedi"
echo "    diğer siteler           → değişmedi"
echo ""
echo "  Yönetim komutları:"
echo "    systemctl status ${SERVICE_NAME}"
echo "    journalctl -u ${SERVICE_NAME} -f"
echo "    systemctl restart ${SERVICE_NAME}"
echo ""
