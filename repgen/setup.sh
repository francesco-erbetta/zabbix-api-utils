#!/bin/bash

#Funzione per individuare distro corrente
get_distro() {
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "$ID"
  else
    echo "unknown"
  fi
}

DISTRO=$(get_distro)

#Installa le dipendenze usando il package manager appropriato
if [ "$DISTRO" == "ubuntu" ] || [ "$DISTRO" == "debian" ]; then
  apt update
  for pkg in python3 python3-pip python3-venv sendmail; do
    if ! dpkg -l | grep -qw "$pkg"; then
      apt install -y "$pkg"
    fi
  done
elif [ "$DISTRO" == "centos" ] || [ "$DISTRO" == "rhel" ] || [ "$DISTRO" == "almalinux" ] || [ "$DISTRO" == "rocky" ]; then
  for pkg in python3 python3-pip python3-venv sendmail; do
    if ! rpm -q "$pkg" >/dev/null 2>&1; then
      yum install -y "$pkg"
    fi
  done
elif [ "$DISTRO" == "sles" ] || [ "$DISTRO" == "opensuse" ]; then
  zypper refresh
  for pkg in python3 python3-pip python3-venv sendmail; do
    if ! rpm -q "$pkg" >/dev/null 2>&1; then
      zypper install -y "$pkg"
    fi
  done
else
  echo "Distro non riconosciuta, intervento manuale richiesto"
  exit 1
fi

#Crea nuovo utente per generazione report
useradd -m -s /bin/bash zabbix-reports
zabbpwd=$(cat /dev/urandom | tr -dc A-Za-z0-9 | fold -w 12 | head -n 1)
echo "zebbix-reports:$zabbpwd" | chpasswd
echo "La password per l'utente locale zabbix-reports è $zabbpwd"
echo "Assicurati che sia salvata in modo sicuro e premi qualunque tasto per continuare..."
read
cp -r ../../zabbix-api-utils /home/zabbix-reports
chown -R zabbix-reports:zabbix-reports /home/zabbix-reports/zabbix-api-utils
su zabbix-reports /home/zabbix-reports/zabbix-api-utils/repgen/custom.sh
