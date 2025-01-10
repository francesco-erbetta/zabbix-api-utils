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
  apt install -y python3 python3-pip python3-venv sendmail
elif [ "$DISTRO" == "centos" ] || [ "$DISTRO" == "rhel" ] || [ "$DISTRO" == "almalinux" ] || [ "$DISTRO" == "rocky" ]; then
  yum install -y python3 python3-pip python3-venv sendmail
elif [ "$DISTRO" == "sles" ] || [ "$DISTRO" == "opensuse" ]; then
  zypper refresh
  zypper install -y python3 python3-pip python3-venv sendmail
else
  echo "Distro non riconosciuta, intervento manuale richiesto"
  exit 1
fi

#Crea nuovo utente per generazione report
useradd -m -s /bin/bash zabbix-reports
echo -n "Scegli una password per l'utente zabbix-reports
"
passwd zabbix-reports
cp -r ../../zabbix-api-utils /home/zabbix-reports
chown -R zabbix-reports:zabbix-reports /home/zabbix-reports/zabbix-api-utils
su zabbix-reports /home/zabbix-reports/zabbix-api-utils/repgen/custom.sh
