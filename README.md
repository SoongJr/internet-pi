# Windows Client

**A Windows Client Configuration for my personal devices**

This represents part of my personal Windows client setup to make reinstalling my PC easier.  
You may find this useful as a starting point for your own setup, but don't expect any support from me 😜  

## Setup

### prepare ansible host
  1. [Install Ansible on some existing machine](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html). The easiest way (especially on Pi or a Debian system) is via Pip:
     1. (If on Pi/Debian): `sudo apt-get install -y python3-pip`
     2. (Everywhere): `python3 -m venv .venv && . .venv/bin/activate && python3 -m pip install -r requirements.txt`
  2. Clone this repository, then enter the repository directory: `cd internet-pi`.
  3. Install requirements: `ansible-galaxy collection install -r requirements.yml` (if you see `ansible-galaxy: command not found`, restart your SSH session or reboot the machine and try again)
  4. Make copies of the following files and customize them to your liking:
     - `example.inventory.ini` to `inventory.ini` (replace IP address with your client's IP, or comment that line and uncomment the `connection=local` line if you're running it on the machine you're setting up).
     - `example.config.yml` to `config.yml`
  5. Create a file named `connection-password.txt` containing the windows password of the target.

### prepare target client
  1. Set up a local user (as opposed to logging in with windows account) to be able to authenticate via NTLM.
  2. Ensure [prerequisistes are fullfilled](https://docs.ansible.com/ansible/latest//os_guide/windows_setup.html#windows-setup).  
    In elevated powershell: `winrm quickconfig` and `winrm set winrm/config/client '@{TrustedHosts="<ansible-host>"}'`

### run the playbook
`ansible-playbook --connection-password-file=connection-password.txt main.yml`

### Known Issues

**If running right after target has been booted**: the WinRM service needs a couple minutes to start up, so keep this in mind if you get connection timeouts and retry after a while.

**If running locally**: You may encounter an error like "Error while fetching server API version". If you do, please either reboot or log out and log back in, then run the playbook again.

## License

MIT

## Author

This project was created in 2021 by [Jeff Geerling](https://www.jeffgeerling.com/) for an entirely different use-case (provisioning Raspberry Pis) and modified beyond recognition by SoongJr.
