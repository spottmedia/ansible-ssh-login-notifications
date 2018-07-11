# Ansible Role: SSH Login Notifications


Installs scripts to send a notification (by mail and/or Slack) when an user logs in using SSH.

The scripts use *pam_exec.so* in the PAM *open session* event to detect the login.

## Requirements

This role has been tested in Ubuntu 14.04 and Ubuntu 16.04 but it should be valid for any distribution that uses the PAM Linux system.

## Role Variables

The variables that can be passed to this role and a brief description about them are as follows.

```
# Notifications by email, set it to true to activate or false to deactivate
ssh_login_notifications_mail_enable: true

# Set the e-mail notification receiver
ssh_login_notifications_mail_receiver: "root"

# Notifications by Slack, set it to true to activate or false to deactivate
ssh_login_notifications_slack_enable: false

# Set the Slack custom integration webhook URL
ssh_login_notifications_slack_webhook: ""

# Keep track of IPs that logged in and only report to slack if a new one logs in
# NOTE: There isn't an email conterpart since normally you want your email log to be as detailed as possible
# for better forensic analysis
# Seen IPs' log is kept as a plaintext file under /var/log/ansible-ssh-login-notification.log
ssh_login_notifications_slack_only_unique: true
```

Notifications previously activated with this role can be deactivated by setting the variable to *false*. 

## Dependencies

None

## Example Playbook

```
- hosts: server
  roles:
    - { role: grzegorznowak.ansible_role_ssh_login_notifications }
```

## License

MIT / BSD

## Sponsored by

#### [Kwiziq.com](https://www.kwiziq.com) - The AI language education platform
#### [Spottmedia.com](http://www.spottmedia.com) - Technology design, delivery and consulting


## Author Information

python, ansible, slack & shell coding by [Grzegorz Nowak](https://www.linkedin.com/in/grzegorz-nowak-356b7360/) and Spottmedia.


the initial code was a fork from a work of:
[Fernando Membrive](https://membrive.net).
