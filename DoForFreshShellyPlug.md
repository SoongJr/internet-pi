1. plug in the shelly-plug and connect with cellphone to its access point
    1. visit http://192.168.33.1
    1. configure your home WiFi in "Internet & Security" -> "WiFi Mode - Client"
1. set a hostname and/or static IP address for your device in your router.  
    This makes it reachable as http://<host-or-IP> (on my FritzBox I have to restart the router before the hostname is effective)
1. open a terminal and run these commands to apply default settings.
    1. set some variables used in later calls (using bash syntax here), username and password will be the credentials to access the plug:  
        ```
        username="<username>"
        password="<password>"
        hostname="<host-or-IP>"
        ```
    1. the first command sets a username and password that need to be used in consecutive calls:  
        `curl --silent -X POST "http://$hostname/settings/login" --data "enabled=true&unprotected/false&username=$username&password=$password"`  
    1. second command triggers firmware update "over the air":  
        `curl --user "$username:$password" --silent -X POST "http://$hostname/settings/ota" --data "update=true"`  
    1. these change behavior of your plug:  
        `curl --user "$username:$password" --silent -X POST "http://$hostname/settings/relay/0" --data "default_state=off&auto_on=0&auto_off=0&schedule=false"`  
        `curl --user "$username:$password" --silent -X POST "http://$hostname/settings" --data "led_status_disable=true&led_power_disable=true"`  
