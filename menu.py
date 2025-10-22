import json
import ssl
import getpass
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import socket  

#global variable to store connection info
si = None


def load_config():    
    with open('vcenter-conf.json', 'r') as f:
        data = json.load(f)
        username = data['vcenter'][0]['vcenteradmin']
        host = data['vcenter'][0]['vcenterhost']
        return username, host 
def menu():
    print("[0] Exit")
    print("[1] Session Info")
    print("[2] Vcenter Info")
    print("[3] VM Info")
   

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally: 
        s.close() 
    return ip


def connect_to_vcenter(host, username):
    global si
    password = getpass.getpass(prompt='Enter vCenter password: ')
    context = ssl._create_unverified_context()
    si = SmartConnect(host=host, user=username, pwd=password, sslContext=context)
    aboutInfo = si.content.about
    return si , aboutInfo

def show_session_info(username, host):
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Session Information:")
    print("Vcenter Host:", host)
    print("Vcenter Admin:",username)
    print("Local IP Address:", get_local_ip())
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
def get_all_vms():
    content = si.RetrieveContent()
    container = content.rootFolder  
    viewType = [vim.VirtualMachine]  
    recursive = True  
    containerView = content.viewManager.CreateContainerView(container, viewType, recursive)
    vms = containerView.view
    containerView.Destroy()
    return vms
def search_vm(filter_name):
    vms = get_all_vms()
    if filter_name:
        print("Searching for VMs matching:", filter_name)
        matching_vms = []
        for vm in vms:
            if filter_name.lower() in vm.name.lower():
                matching_vms.append(vm)
    else:
        print("ALL VIRTUAL MACHINES")
        matching_vms = vms
    print(f"Found {len(matching_vms)} matching VMs.")

    for vm in matching_vms:
        print("--------------------------")
        print("VM Name:", vm.name)
        print("Power State:", vm.runtime.powerState)
        print("CPU Count:", vm.config.hardware.numCPU)
        print("Memory (MB):", vm.config.hardware.memoryMB) 

        ip = get_vm_ip(vm)
        print("IP Address:", ip)
        print("--------------------------")
    return matching_vms

def get_vm_ip(vm):
    if vm.guest is not None:
        ip = vm.guest.ipAddress
        if ip:
            return ip
        else:
            return "No IP assigned"
    else:
        return "No guest info available"        
def main():
    username, host = load_config()
    si, aboutInfo = connect_to_vcenter(host, username)
    menu()  
    Option = int(input("Choose an option: "))

    while Option != 0:
        if Option == 1:
               show_session_info(username, host)   
        elif Option == 2:
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print(aboutInfo)
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
        elif Option ==3:

            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            for all in get_all_vms():
                print(all.name)
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            filter_name = input("Enter VM name filter (leave blank for all VMs): ")
            search_vm(filter_name)
        else:
            print("Invalid option, please try again.")
        menu()
        Option = int(input("Choose an option: "))
    print("Exiting program.")

if __name__ == "__main__":
    main()
