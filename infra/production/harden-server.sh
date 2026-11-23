#!/usr/bin/env bash
# Первоначальная настройка VPS Ubuntu: firewall, SSH, fail2ban, базовый аудит.
# Запускать от root. Скрипт идемпотентен по большинству шагов.
set -euo pipefail

SSH_PORT="${SSH_PORT:-22}"

echo "==> apt update + базовые пакеты"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
  ufw fail2ban nftables ca-certificates curl git openssl

echo "==> UFW: отказываем всё входящее, разрешаем SSH/HTTP/HTTPS"
ufw default deny incoming
ufw default allow outgoing
# 'limit' мягко ограничивает частоту новых SSH-подключений с одного IP.
ufw limit "${SSH_PORT}/tcp" comment 'SSH rate-limited'
ufw allow 80/tcp comment 'HTTP (redirect to HTTPS)'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
ufw status verbose

echo "==> SSH: пароль и прочие небезопасные методы выключаем, root по ключу оставляем"
# Имя сортируется раньше cloud-init'овского 50-cloud-init.conf, чтобы переопределить его.
cat > /etc/ssh/sshd_config.d/10-harden-piano.conf <<EOF
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitEmptyPasswords no
X11Forwarding no
AllowAgentForwarding no
PermitTunnel no
PermitRootLogin prohibit-password
MaxAuthTries 3
MaxSessions 6
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
PerSourcePenalties yes
EOF
sshd -t
systemctl reload ssh

echo "==> fail2ban: только nginx-jail (SSH- jail выключен из-за CVE-2026-109786)"
mkdir -p /etc/fail2ban/jail.d
cat > /etc/fail2ban/jail.d/10-piano-school.local <<'EOF'
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
banaction = nftables[type=multiport]
banaction_allports = nftables[type=allports]
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = false

[nginx-req-limit]
enabled  = true
port     = http,https
filter   = nginx-req-limit
logpath  = /var/log/nginx/error.log
maxretry = 2
findtime = 60
bantime  = 10m

[nginx-bad-host]
enabled  = true
port     = http,https
filter   = nginx-bad-host
logpath  = /var/log/nginx/access.log
maxretry = 4
findtime = 60
bantime  = 1h
EOF

cat > /etc/fail2ban/filter.d/nginx-req-limit.conf <<'EOF'
[Definition]
failregex = ^.*limiting requests, excess: .* by zone .*, client: <HOST>,.*$
ignoreregex =
EOF

# Access-log nginx в прод-стеке пишется в bind-файл infra/production/nginx-error.log;
# этот фильтр ловит сканеры, которые стучатся в несуществующие пути.
cat > /etc/fail2ban/filter.d/nginx-bad-host.conf <<'EOF'
[Definition]
failregex = ^<HOST> - - \[.*\] "(GET|POST|HEAD) /(wp-login|wp-admin|phpMyAdmin|\.env|\.git|xmlrpc\.php) HTTP/.*" 404 .*$
ignoreregex =
EOF

systemctl enable --now fail2ban
systemctl reload fail2ban || systemctl restart fail2ban
sleep 2
fail2ban-client status || true

echo "==> автоматические security-обновления"
cat > /etc/apt/apt.conf.d/99-piano-unattended <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

echo "==> проверка доступных портов"
ss -tulpn || true

echo "Готово. Проверьте из другого терминала: ssh root@$(hostname -I | awk '{print $1}')"
