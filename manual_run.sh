Terminal manual commands

DD command to run. 
dd if=/dev/zero of=test bs=1000M oflag=direct status=progress

sudo dd if=/dev/zero of=/dev/nvme1n1 bs=1000M oflag=direct status=progress 
