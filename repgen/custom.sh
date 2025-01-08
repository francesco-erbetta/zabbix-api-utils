#!/bin/bash
#crea venv python e installa le dipendenze python
WORKDIR=/home/zabbix-reports/zabbix-api-utils
mkdir $WORKDIR/zabbix-reports-venv
python3 -m venv $WORKDIR/zabbix-reports-venv
source $WORKDIR/zabbix-reports-venv/bin/activate &&
pip install -r $WORKDIR/requirements.txt

#Customizzazione cliente
echo -n "Inserisci nome cliente: "
read cliente
sed -i "s/ACME Corporation/$cliente/g" $WORKDIR/repgen/gg.sh

echo -n "Inserisci lo username dell'utente zabbix: "
read zusr
echo -n "Inserisci la password dell'utente zabbix: "
read zpwd
echo -n "Inserisci la url del frontend zabbix (es. https://zabbix.cliente.local/zabbix/): "
read zurl
echo -n "Inserisci la mail alla quale si intende inviare il report"
read mailcliente

echo "[Zabbix API]
username=$zusr
password=$zpwd
api=$zurl
no_verify=true" > /home/zabbix-reports/.zabbix-api.conf

while true; do
    echo "A che cadenza devono essere generati i report?"
    echo "1) Settimanale"
    echo "2) Mensile"
    read -p "Inserisci 1 o 2: " choice

    if [[ "$choice" == "1" ]]; then
        echo "0 8 * * 1 $WORKDIR/repgen/gg.sh -s now-7d -t now && echo "Testo mail" | mail -s "Report settimanale $cliente" -a $WORKDIR/repgen/report.pdf $mailcliente" | crontab -
        break
    elif [[ "$choice" == "2" ]]; then
        sed -i 's/Last 7 days/Last 30 days/g' $WORKDIR/repgen/gg.sh
        echo "0 0 1 * * $WORKDIR/repgen/gg.sh -s now-30d -t now && echo "Testo mail" | mail -s "Report mensile $cliente" -a $WORKDIR/repgen/report.pdf $mailcliente" | crontab -
        break
    else
        echo "Input invalido. Inserisci 1 o 2."
    fi
done
