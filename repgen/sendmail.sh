#!/bin/bash
WORKDIR="/home/zabbix-reports/zabbix-api-utils/repgen"
FROM=""
TO=""
CC=""
SUBJECT="Report [cadenza] performances infrastruttura [cliente] $(date +"%d-%m-%Y")"
BODY="
 <html>
 <body>
 <p>Buongiorno,</br></br>
 in allegato il report settimanale di performances dell'infrastruttura [cliente].</br></br>
 Cordiali saluti,</br>
 BV-Tech</br></br>
 <img src="cid:myimage" /></br></br>
 
 <i>Questa è una mail automatica, si prega di non rispondere, per ogni esigenza [placeholder]</i></p>
 </body>
 </html>"
IMAGE_PATH="$WORKDIR/Logo_firma_BV.png"
ATTACHMENT="$WORKDIR/report$(date +%Y%m%d).pdf"

if [ $? -eq 0 ]; then
  {
    echo "From: $FROM"
    echo "To: $TO"
    echo "Cc: $CC"
    echo "Subject: $SUBJECT"
    echo "MIME-Version: 1.0"
    echo "Content-Type: multipart/mixed; boundary=boundary42"
    echo
    echo "--boundary42"
    echo "Content-Type: text/html; charset=utf-8"
    echo "Content-Transfer-Encoding: 8bit"
    echo
    echo "$BODY"
    echo "--boundary42"
    echo "Content-Type: image/png"
    echo "Content-Transfer-Encoding: base64"
    echo "Content-Disposition: inline; filename=Logo_firma_BV.png"
    echo "Content-ID: <myimage>"
    echo
    base64 "$IMAGE_PATH"
    echo "--boundary42"
    echo "Content-Type: application/octet-stream; name=$(basename $ATTACHMENT)"
    echo "Content-Transfer-Encoding: base64"
    echo "Content-Disposition: attachment; filename=$(basename $ATTACHMENT)"
    echo
    base64 "$ATTACHMENT"
    echo "--boundary42--"
  } | sendmail -t
fi
