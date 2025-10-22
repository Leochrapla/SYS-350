import json
import ssl

import getpass
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import socket  
from time import sleep
from tqdm import tqdm
#global variables
si = None
clear = lambda: print("\n" * 1) 
def progress_bar(duration):
    for _ in tqdm(range(duration), desc="Processing", colour= "green",ncols=70):
        sleep(1)

def load_config():    
    with open('vcenter-conf.json', 'r') as f:
        data = json.load(f)
        username = data['vcenter'][0]['vcenteradmin']
        host = data['vcenter'][0]['vcenterhost']
        return username, host 
    
def menu():
    clear()
    print("Main Menu")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("[0] Exit")
    print("[1] Session Info")
    print("[2] Vcenter Info")
    print("[3] VM Info")
    print("[4] Vm task menu")
      

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

def vm_power():
    print("choose a vm to power on or off")
    si.RetrieveContent()
    datacenter = si.content.rootFolder.childEntity[0]
    vms = datacenter.vmFolder.childEntity
    for vm in vms:
        print(vm.name)
    vmname=input("Enter the name of the VM to power on or off: ")
    if len(vmname) == 0:
        print("Operation cancelled.")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
    else:
        for i in vms:
            if vmname in str(i.name):
                print (i.name, "is currently:", i.runtime.powerState)
                doublecheck = input("toggler power? y/n: ")
                if doublecheck.lower() == 'y':
                    if i.runtime.powerState == "poweredOff":
                        print(i.name, "is being powered on")
                        
                        task = i.PowerOnVM_Task()
                        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                            progress_bar(2)
                        if task.info.state == vim.TaskInfo.State.success:
                            print(i.name, "has been powered on")
                            print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
                        else:
                            print("Failed to power on VM:", task.info.error)
                            print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
                    elif i.runtime.powerState == "poweredOn":
                        print(i.name, "is being powered off")
                        task = i.PowerOffVM_Task()
                        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                            progress_bar(2)
                        if task.info.state == vim.TaskInfo.State.success:
                            print(i.name, "has been powered off")
                            print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
                        else:
                            print("Failed to power off VM:", task.info.error)
                            print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
                    else:
                        print(i.name, "is in an unknown state and cannot be toggled.")
                        print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
                else:
                    print("Operation cancelled.")
                    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")

def vm_rename(): ## from Copilot
    print("choose a vm to rename")
    si.RetrieveContent()
    datacenter = si.content.rootFolder.childEntity[0]
    vms = datacenter.vmFolder.childEntity
    for vm in vms:
        print(vm.name)
    oldname=input("Enter the name of the VM to rename: ")
    newname=input("Enter the new name for the VM: ")
    if len(oldname) == 0 or len(newname) == 0:
        print("Operation cancelled.")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
    else:
        for i in vms:
            if oldname in str(i.name):
                print(i.name, "is being renamed to", newname)
                spec = vim.vm.ConfigSpec()
                spec.name = newname
                task = i.ReconfigVM_Task(spec)
                while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                    progress_bar(4)
                if task.info.state == vim.TaskInfo.State.success:
                    print(i.name, "has been renamed to", newname)
                    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
                else:
                    print("Failed to rename VM:", task.info.error)
                    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")

def vm_snapshot():

    print("choose a vm to snapshot")
    si.RetrieveContent()
    datacenter = si.content.rootFolder.childEntity[0]
    vms = datacenter.vmFolder.childEntity
    for vm in vms:
        print(vm.name)
    snapname=input("Enter the name of the VM to snapshot: ")
    if len(snapname) == 0:
        print("Operation cancelled.")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
    else:
        for i in vms:
            if snapname in str(i.name):
                print(i.name, "is being snapshotted")
                task = i.CreateSnapshot_Task(name="Snapshot1", description="Snapshot created by script", memory=False, quiesce=False)
                while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                    progress_bar(4)
                if task.info.state == vim.TaskInfo.State.success:
                    print(i.name, "has been snapshotted")
                    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
                else:
                    print("Failed to snapshot VM:", task.info.error)
                    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
      
def delete_snapshot():
    print("choose a vm to delete a snapshot from")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")

    si.RetrieveContent()
    datacenter = si.content.rootFolder.childEntity[0]
    vms = datacenter.vmFolder.childEntity
    for vm in vms:
        print(vm.name)
    snapname=input("Enter the name of the VM to delete a snapshot from: ")
    if len(snapname) == 0:
        print("Operation cancelled.")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
    else:
        for i in vms:
            if snapname in str(i.name):
                print(i.name, "is having a snapshot deleted")
                rootSnapshot = i.snapshot.rootSnapshotList
                if not rootSnapshot:
                    print("No snapshots found for this VM.")
                    return
                snapshot_to_delete = rootSnapshot[0].snapshot
                task = snapshot_to_delete.RemoveSnapshot_Task(removeChildren=False)
                while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                    progress_bar(4)
                if task.info.state == vim.TaskInfo.State.success:
                    print(i.name, "snapshot has been deleted")
                    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
                else:
                    print("Failed to delete snapshot:", task.info.error)
                    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")

def delete_vm():
    print("choose a vm to delete")
    si.RetrieveContent()
    datacenter = si.content.rootFolder.childEntity[0]
    vms = datacenter.vmFolder.childEntity
    for vm in vms:
        print(vm.name)
    delname=input("Enter the name of the VM to delete: ")
    if len(delname) == 0:
        print("Operation cancelled.")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
    else:
        for i in vms:
            if delname in str(i.name):
                print(i.name, "is being deleted")
                task = i.Destroy_Task()
                while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                    progress_bar(8)
                if task.info.state == vim.TaskInfo.State.success:
                    print(i.name, "has been deleted")
                    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
                else:
                    print("Failed to delete VM:", task.info.error)
                    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")      

def clone_vm():
    print("choose a vm to clone")
    si.RetrieveContent()
    datacenter = si.content.rootFolder.childEntity[0]
    vms = datacenter.vmFolder.childEntity
    for vm in vms:
        print(vm.name)
    clonename=input("Enter the name of the VM to clone: ")
    newname=input("Enter the new name for the cloned VM: ")
    if len(clonename) == 0 or len(newname) == 0:
        print("Operation cancelled.")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
    else:
        for i in vms:
            if clonename in str(i.name):
                print(i.name, "is being cloned to", newname)
                destfolder = i.parent
                resource_pool = i.resourcePool
                spec = vim.vm.CloneSpec()
                spec.location = vim.vm.RelocateSpec()
                spec.powerOn = False
                task = i.Clone(folder=destfolder, name=newname, spec=spec)
                while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                    progress_bar(36)
                if task.info.state == vim.TaskInfo.State.success:
                    print(i.name, "has been cloned to", newname)
                    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
                else:
                    print("Failed to clone VM:", task.info.error)
                    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")

def task_menu():
    
    clear()
    print("VM Task Menu")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("[0] Return to main menu")
    print("[1] Power On or Off a VM")
    print("[2] Rename a VM")
    print("[3] Snapshot a VM")
    print("[4] Delete a Snapshot")
    print("[5] Clone a VM")
    print("[6] Delete a Vm")
    Option = int(input("Choose an option: "))
    while Option != 0:
        if Option == 1:
            vm_power()
        elif Option == 2:
            vm_rename()
        elif Option == 3:
            vm_snapshot()
        elif Option == 4:
            delete_snapshot()
        elif Option == 5:
            clone_vm()
        elif Option == 6:
            delete_vm()
        else:
            print("Invalid option, please try again.")
        print("[0] Return to main menu")
        print("[1] Power On or Off a VM")
        print("[2] Rename a VM")
        print("[3] Snapshot a VM")
        print("[4] Delete a Snapshot")
        print("[5] Clone a VM")
        print("[6] Delete a VM")
        Option = int(input("Choose an option: "))
    print("Returning to main menu.")


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
        elif Option ==4:
            task_menu()
        else:
            print("Invalid option, please try again.")
        clear()    
        menu()
        Option = int(input("Choose an option: "))
    print("Exiting program.")




if __name__ == "__main__":
    main()
