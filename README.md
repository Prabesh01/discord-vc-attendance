https://discord.com/oauth2/authorize?client_id=1289062067214614539&permissions=2165312512&integration_type=0&scope=bot+applications.commands

nohup python3 -u /root/discord-vc-attendance/bot.py > /root/botlogs/hoh-bot.log 2>&1 &

nohup python3 -u /root/discord-vc-attendance/web/app.py > /root/botlogs/hoh-app.log 2>&1 &

server {
    listen 80;
    server_name hoh.cote.ws;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header User-Agent $http_user_agent;
    }
}

ln -s /etc/nginx/sites-available/hoh.conf /etc/nginx/sites-enabled/
