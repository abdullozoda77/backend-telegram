#!/usr/bin/env bash
# Deploys this project with Gunicorn + Nginx (+ SSL if a domain is given).
# Usage (from the project folder on the server):
#   bash deploy/deploy.sh                 # IP only, HTTP
#   bash deploy/deploy.sh example.tj      # with domain + HTTPS via certbot
set -e

DOMAIN="$1"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE=my_project
RUN_USER="$(whoami)"
SERVER_IP="$(hostname -I | awk '{print $1}')"
HOSTS="${SERVER_IP},127.0.0.1,localhost${DOMAIN:+,$DOMAIN}"

echo "==> Project: $PROJECT_DIR  user: $RUN_USER  hosts: $HOSTS"

echo "==> Installing system packages"
sudo apt update
sudo apt install -y python3-venv python3-pip nginx

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
ExecStart=$PROJECT_DIR/.venv/bin/gunicorn --access-logfile - --workers 3 --bind 127.0.0.1:8000 core.wsgi:application

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE.service
sudo systemctl restart $SERVICE.service

echo "==> Nginx"
sudo tee /etc/nginx/sites-available/$SERVICE > /dev/null <<EOF
server {
    listen 80;
    server_name ${DOMAIN:-$SERVER_IP} $SERVER_IP;

    client_max_body_size 20M;

    location /static/ {
        root $PROJECT_DIR;
    }

    location /media/ {
        root $PROJECT_DIR;
    }

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF
sudo ln -sf /etc/nginx/sites-available/$SERVICE /etc/nginx/sites-enabled/$SERVICE
sudo rm -f /etc/nginx/sites-enabled/default

echo "==> Permissions so Nginx can read static/media"
sudo chown -R "$RUN_USER":www-data "$PROJECT_DIR"
dir="$PROJECT_DIR"
while [ "$dir" != "/" ]; do sudo chmod o+x "$dir"; dir="$(dirname "$dir")"; done
sudo chmod -R 755 "$PROJECT_DIR/static" "$PROJECT_DIR/media"
sudo chmod 775 "$PROJECT_DIR" "$PROJECT_DIR/media"
[ -f "$PROJECT_DIR/db.sqlite3" ] && sudo chmod 664 "$PROJECT_DIR/db.sqlite3"

sudo nginx -t
sudo systemctl restart nginx

if [ -n "$DOMAIN" ]; then
    echo "==> SSL for $DOMAIN"
    sudo apt install -y certbot python3-certbot-nginx
    sudo certbot --nginx -d "$DOMAIN"
fi

echo
sudo systemctl --no-pager status $SERVICE.service | head -5
echo
echo "Done! Open: http://${DOMAIN:-$SERVER_IP}/swagger/"
echo "Create an admin user with: .venv/bin/python manage.py createsuperuser"
