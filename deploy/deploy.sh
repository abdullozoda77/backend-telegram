#!/usr/bin/env bash
# Deploys this project with Gunicorn + Nginx (+ SSL if a domain is given).
# Usage (from the project folder on the server):
#   bash deploy/deploy.sh                 # IP only: http://SERVER_IP:8090
#   bash deploy/deploy.sh example.tj      # with domain on port 80 + HTTPS via certbot
set -e

DOMAIN="$1"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE=backend-telegram
APP_PORT=8020     # Gunicorn (internal only)
WEB_PORT=8090     # Nginx (public) when no domain is given
RUN_USER="$(whoami)"
SERVER_IP="$(hostname -I | awk '{print $1}')"
HOSTS="${SERVER_IP},127.0.0.1,localhost${DOMAIN:+,$DOMAIN}"

echo "==> Project: $PROJECT_DIR  user: $RUN_USER  hosts: $HOSTS"

echo "==> Removing the old 'my_project' setup from the first run"
if [ -f /etc/systemd/system/my_project.service ] && grep -q "$PROJECT_DIR" /etc/systemd/system/my_project.service; then
    sudo systemctl disable --now my_project.service || true
    sudo rm -f /etc/systemd/system/my_project.service
fi
if [ -f /etc/nginx/sites-available/my_project ] && grep -q "$PROJECT_DIR" /etc/nginx/sites-available/my_project; then
    sudo rm -f /etc/nginx/sites-enabled/my_project /etc/nginx/sites-available/my_project
fi

echo "==> Installing system packages"
sudo apt update
sudo apt install -y python3-venv python3-pip nginx redis-server
sudo systemctl enable --now redis-server

echo "==> Virtualenv + requirements"
cd "$PROJECT_DIR"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

SECRET_FILE="$PROJECT_DIR/.secret_key"
[ -f "$SECRET_FILE" ] || .venv/bin/python -c "import secrets; print(secrets.token_urlsafe(50))" > "$SECRET_FILE"
SECRET_KEY="$(cat "$SECRET_FILE")"

echo "==> Migrate + collectstatic"
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
mkdir -p media

echo "==> Gunicorn systemd service"
sudo tee /etc/systemd/system/$SERVICE.service > /dev/null <<EOF
[Unit]
Description=Gunicorn daemon for $SERVICE
After=network.target

[Service]
User=$RUN_USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="DJANGO_DEBUG=False"
Environment="DJANGO_ALLOWED_HOSTS=$HOSTS"
Environment="DJANGO_SECRET_KEY=$SECRET_KEY"
ExecStart=$PROJECT_DIR/.venv/bin/gunicorn --access-logfile - --workers 3 --bind 127.0.0.1:$APP_PORT core.wsgi:application

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE.service
sudo systemctl restart $SERVICE.service

echo "==> Nginx"
if [ -n "$DOMAIN" ]; then
    LISTEN=80; SERVER_NAME="$DOMAIN"; URL="http://$DOMAIN"
else
    LISTEN=$WEB_PORT; SERVER_NAME="$SERVER_IP"; URL="http://$SERVER_IP:$WEB_PORT"
fi
sudo tee /etc/nginx/sites-available/$SERVICE > /dev/null <<EOF
server {
    listen $LISTEN;
    server_name $SERVER_NAME;

    client_max_body_size 20M;

    location /static/ {
        root $PROJECT_DIR;
    }

    location /media/ {
        root $PROJECT_DIR;
    }

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:$APP_PORT;
    }
}
EOF
sudo ln -sf /etc/nginx/sites-available/$SERVICE /etc/nginx/sites-enabled/$SERVICE

echo "==> Permissions so Nginx can read static/media"
sudo chown -R "$RUN_USER":www-data "$PROJECT_DIR"
dir="$PROJECT_DIR"
while [ "$dir" != "/" ]; do sudo chmod o+x "$dir"; dir="$(dirname "$dir")"; done
sudo chmod -R 755 "$PROJECT_DIR/static" "$PROJECT_DIR/media"
sudo chmod 775 "$PROJECT_DIR" "$PROJECT_DIR/media"
[ -f "$PROJECT_DIR/db.sqlite3" ] && sudo chmod 664 "$PROJECT_DIR/db.sqlite3"

sudo nginx -t
sudo systemctl reload nginx

if [ -n "$DOMAIN" ]; then
    echo "==> SSL for $DOMAIN"
    sudo apt install -y certbot python3-certbot-nginx
    sudo certbot --nginx -d "$DOMAIN"
    URL="https://$DOMAIN"
fi

sleep 2
echo
sudo systemctl --no-pager status $SERVICE.service | head -5
echo
echo "Done! Open: $URL/swagger/"
echo "Create an admin user with: .venv/bin/python manage.py createsuperuser"
