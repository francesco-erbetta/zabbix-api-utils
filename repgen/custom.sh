#!/bin/bash
#crea venv python e installa le dipendenze python
WORKDIR=/home/zabbix-reports/zabbix-api-utils
mkdir $WORKDIR/zabbix-reports-venv
python3 -m venv $WORKDIR/zabbix-reports-venv
source $WORKDIR/zabbix-reports-venv/bin/activate &&
  pip install -r $WORKDIR/requirements.txt

#Customizzazione cliente
echo -n "Inserisci nome cliente: "
read -e cliente
sed -i "s/ACME Corporation/$cliente/g" $WORKDIR/repgen/gg.sh
sed -i "s/\[cliente\]/$cliente/g" $WORKDIR/repgen/sendmail.sh

echo -n "Inserisci lo username dell'utente zabbix: "
read -e zusr
echo -n "Inserisci la password dell'utente zabbix: "
read -e zpwd
echo -n "Inserisci la url del frontend zabbix (es. https://zabbix.cliente.local/zabbix/): "
read -e zurl
echo -n "Inserisci mail mittente per l'invio del report: "
read -e mittente
sed -i "/^FROM=/s/\".*\"/\"$mittente\"/" $WORKDIR/repgen/sendmail.sh
echo -n "Inserisci una o più mail (separate da virgola) alle quali si intende inviare il report: "
read -e mailcliente
sed -i "/^TO=/s/\".*\"/\"$mailcliente\"/" $WORKDIR/repgen/sendmail.sh
echo -n "Inserisci una o più mail (separate da virgola) da mettere in copia: "
read -e mailcopia
sed -i "/^CC=/s/\".*\"/\"$mailcopia\"/" $WORKDIR/repgen/sendmail.sh
echo -n "Inserisci la frase di congedo: "
read -e endsentence
sed -i "s/\[placeholder\]/$endsentence/g" $WORKDIR/repgen/sendmail.sh

echo "[Zabbix API] 
username=$zusr 
password=$zpwd
api=$zurl
no_verify=true" >/home/zabbix-reports/.zabbix-api.conf

while true; do
  echo "A che cadenza devono essere generati i report?"
  echo "1) Settimanale"
  echo "2) Mensile"
  read -p "Inserisci 1 o 2: " choice

  if [[ "$choice" == "1" ]]; then
    sed -i "s/\[cadenza\]/settimanale/g" $WORKDIR/repgen/sendmail.sh
    echo "0 8 * * 1 source $WORKDIR/zabbix-reports-venv/bin/activate; $WORKDIR/repgen/gg.sh -s now-1w -t now; $WORKDIR/repgen/sendmail.sh" | crontab -
    break
  elif [[ "$choice" == "2" ]]; then
    sed -i "s/\[cadenza\]/mensile/g" $WORKDIR/repgen/sendmail.sh
    echo "0 0 1 * * source $WORKDIR/zabbix-reports-venv/bin/activate; $WORKDIR/repgen/gg.sh -s now-1M -t now; $WORKDIR/repgen/sendmail.sh" | crontab -
    break
  else
    echo "Input invalido. Inserisci 1 o 2."
  fi
done
