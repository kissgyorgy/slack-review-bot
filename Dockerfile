FROM ubuntu:16.04

COPY systemd/ /root/units

CMD ["/bin/systemd", "--system", "--unit", "/root/units/gerrit-slack-bot.service"]
