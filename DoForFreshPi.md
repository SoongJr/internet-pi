## for new pi:

### on PC and ansible docker container (or any machine accessing the pi):
``` bash
ssh-keygen -f "$HOME/.ssh/known_hosts" -R "internet-pi"; ssh-keygen -f "$HOME/.ssh/known_hosts" -R 192.168.42.51; ssh-keygen -f "$HOME/.ssh/known_hosts" -R 192.168.42.201
```

### on pi:
``` bash
sudo mkdir /media/oldpi
sudo mount /dev/sda2 /media/oldpi # might also be /dev/sdb2

sudo cp -a /media/oldpi/home/pi/.ssh "$HOME"
printf "\n\n# print temparature on every login\nvcgencmd measure_temp\n" >> "$HOME/.bashrc"

sudo apt update
sudo apt dist-upgrade -y

# attempt to transfer existing data from old SD card (didn't manage to get this to work though!)
#sudo apt update
#sudo apt dist-upgrade -y
#curl https://get.docker.com/ -o /tmp/get-docker.sh
#chmod +x /tmp/get-docker.sh
#/tmp/get-docker.sh
#sudo systemctl stop docker.service
# sudo cp -a /media/oldpi/home/pi/internet-pi "$HOME"
# sudo cp -a /media/oldpi/var/lib/docker /var/lib/docker
#sudo systemctl start docker.service
```
