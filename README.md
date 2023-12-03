# Windows Client

**A Windows Client Configuration for my personal devices**

This represents part of my personal Windows client setup to make reinstalling my PC easier.  
You may find this useful as a starting point for your own setup, but don't expect any support from me 😜  

## Setup

### prepare ansible host
  1. Clone this repository, then enter the repository directory: `cd internet-pi`.
  2. Procure some existing system with Python3 installed, ideally a linux machine. Consider using docker:
    `docker run --network=host --volume="$(pwd):/src:ro" --workdir="/src" --interactive --tty --detach --name ansi --pull=always python:3.11-slim`  
    (Note: pywinrm does not officially support latest python, hence using an older one here.)
  3. [Install Ansible on said machine](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html).  
  One way is using pip: `python3 -m venv .venv && . .venv/bin/activate && python3 -m pip install -r requirements.txt`  
  When using docker, prefix any commands with `docker start ansi; docker exec -it ansi ` and don't use virtual env:  
  `docker start ansi; docker exec -it ansi python3 -m pip install -r requirements.txt`
  4. Install requirements: `ansible-galaxy collection install -r requirements.yml` (if you see `ansible-galaxy: command not found`, restart your SSH session or reboot the machine and try again)
  5. Make copies of the following files and customize them to your liking:
     - `example.inventory.ini` to `inventory.ini` (replace IP address with your client's IP, or comment that line and uncomment the `connection=local` line if you're running it on the machine you're setting up).
     - `example.config.yml` to `config.yml`
  6. Create a file named `connection-password.txt` containing the windows password of the target.
  7. Create a file named `secrets.yml` containing secrets you do not wish to set in config.yml  
    (as that risks accidentally uploading them to github)

### prepare target client
1. Ensure [prerequisistes are fullfilled](https://docs.ansible.com/ansible/latest//os_guide/windows_setup.html#windows-setup).
   1. Make sure your network profile is "private" ("Network Status" -> "Properties")
   1. In elevated powershell: `winrm quickconfig`, granting admin access,  
   1. Then add your ansible host as trusted with `winrm set winrm/config/client '@{TrustedHosts="<ansible-host-ip>"}'`
1. Add a local user (as opposed to logging in with windows account) to be able to authenticate via NTLM. Don't forget to change the Role to Administrator. You never need to log in as that user.

### check the playbook
`ansible-lint . && yamllint -f parsable .`

### run the playbook
`ansible-playbook --connection-password-file=connection-password.txt main.yml`

### make your target more secure
1. disable WinRM:
   1.  `Get-NetFirewallRule | ? {$_.Displayname -eq "Windows Remote Management (HTTP-In)"} | Set-NetFirewallRule -Enabled "False"`
   2.  `Stop-Service winrm; Set-Service -Name winrm -StartupType Disabled`
   3.  `Get-NetFirewallRule | ? {$_.Displayname -eq "Windows Remote Management (HTTP-In)"} | Set-NetFirewallRule -Enabled "False"`
1. remove the local user you created

### Known Issues

**If running right after target has been booted**: the WinRM service needs a couple minutes to start up, so keep this in mind if you get connection timeouts and retry after a while.

**If running locally**: You may encounter an error like "Error while fetching server API version". If you do, please either reboot or log out and log back in, then run the playbook again.

**Chocolatey may issue Checksum errors** especially for Steam, if the setup package on their servers has changed but the choco package has not been updated with the new checksum yet. Check steam.yml for a workaround.
## License

MIT

## Author

This project was created in 2021 by [Jeff Geerling](https://www.jeffgeerling.com/) for an entirely different use-case (provisioning Raspberry Pis) and modified beyond recognition by SoongJr.
