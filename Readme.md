# Make sure to install the tools and they work

```
# Install the cli tool to control nvmes on terminal 
sudo apt install nvme-cli


# List all your nvmes 
sudo nvme list

# Running a test 

sudo nvme device-self-test /dev/nvme1n1 -s 2 

sudo nvme device-self-test /dev/nvme2n1 -s 2 

sudo nvme device-self-test /dev/nvme3n1 -s 2 

sudo nvme device-self-test /dev/nvme4n1 -s 2 

sudo nvme device-self-test /dev/nvme5n1 -s 2 


# Check info including temps about nvmes 
sudo watch nvme smart-log /dev/nvme1n1  

sudo watch nvme smart-log /dev/nvme2n1 

sudo watch nvme smart-log /dev/nvme3n1

sudo watch nvme smart-log /dev/nvme4n1

sudo watch nvme smart-log /dev/nvme5n1



/dev/nvme1n1                    
/dev/nvme2n1                      
/dev/nvme3n1                     
/dev/nvme4n1                    
/dev/nvme5n1
```bash 

# Custom GUI nvme benchmark for Linux.

What need to have: 

- NVME selection
- Run the test until hard drive is full
- Temperature monitor
- Critical temperature treshold notification
- Speed


