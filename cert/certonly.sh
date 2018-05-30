#!/bin/bash
if [ "$EUID" -ne 0 ]; then
	echo "Please run as root"
	exit
fi

./certbot-auto certonly --nginx -d "$1"

if [ $? -ne 0 ]; then
	exit
fi

if grep --quiet -l "$1" -r /etc/nginx/sites-available/; then
	exit
fi

echo "
server {
        server_name $1;
        include /etc/nginx/sites-available/pi-basic;

        ssl_certificate /etc/letsencrypt/live/$1/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$1/privkey.pem;
}
" >> /etc/nginx/sites-available/pi-https

sed 'N;/^\n$/D;P;D;' -i /etc/nginx/sites-available/pi-https

systemctl restart nginx

