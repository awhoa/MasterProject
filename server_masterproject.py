from flask import Flask, request, jsonify
from web3 import Web3
import subprocess

app = Flask(__name__)

# Helper function to run shell commands
def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return stdout.strip(), stderr.strip()



@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    try:
        if request.method == 'POST':
            # Get account_name and account_password from the form data
            account_name = request.form.get('account_name')
            account_password = request.form.get('account_password')
        else:
            # Use default account_name and account_password for GET request
            account_name = "testchain16"
            account_password = "mypi1"

        # Use an absolute path for the datadir to avoid issues with the current working directory
        datadir = f"/home/raspberry-node/.{account_name}"

        # Create a temporary password file with the account password
        password_file = "/tmp/account_password.txt"
        with open(password_file, 'w') as f:
            f.write(account_password)

        command = f"geth --datadir {datadir} account new --password {password_file}"
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.stdout, process.stderr

        # Remove the temporary password file
        subprocess.run(f"rm -f {password_file}", shell=True)

        if "Your new key was generated" in stdout:
            return jsonify({"status": "success", "message": "Account created successfully."})
        else:
            return jsonify({"status": "error", "message": f"Failed to create account. Error: {stderr.strip()}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})




@app.route('/delete_account', methods=['POST'])
def delete_account():
    try:
        account_name = request.form.get('account_name')
        if not account_name:
            return jsonify({"status": "error", "message": "Account name not provided."}), 400

        # Use an absolute path for the datadir to avoid issues with the current working directory
        datadir = f"/home/raspberry-node/.{account_name}"
        command = f"rm -rf {datadir}/geth"
        os.system(command)

        return jsonify({"status": "success", "message": f"Ethereum Account deleted successfully for account '{account_name}'."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/initialize_blockchain', methods=['POST'])
def initialize_blockchain():
    try:
        account_name = request.form.get('account_name')
        if not account_name:
            return jsonify({"status": "error", "message": "Account name is required"})

        # Use an absolute path for the datadir to avoid issues with the current working directory
        datadir = f"/home/raspberry-node/.{account_name}"
        custom_genesis_path = "/home/raspberry-node/Documents/testchain_final.json"


        command = f"geth --datadir {datadir} init {custom_genesis_path}"
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.stdout, process.stderr

        if "Successfully wrote genesis state" in stdout:
            return jsonify({"status": "success", "message": f"Blockchain initialized for account '{account_name}'."})
        else:
            return jsonify({"status": "error", "message": f"Failed to initialize blockchain for account '{account_name}'. Error: {stderr.strip()}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/start_node', methods=['POST'])
def start_node():
    try:
        account_name = request.form.get('account_name')
        print("Account_Name: ",account_name)
        datadir = f"/home/raspberry-node/.{account_name}"
        port = 4242
        networkid = 42

        command = f"geth --datadir {datadir} --port {port} --networkid {networkid} console --nodiscover"
        subprocess.Popen(command, shell=True)

        return jsonify({"status": "success", "message": "Node started successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})




def stop_node(account_name):
    try:
        datadir = f"/home/raspberry-node/.{account_name}"
        port = 4242
        networkid = 42
        

        command = f'geth --datadir {datadir} --port {port} --networkid {networkid} console --nodiscover --exec "console.log("exit worked")"'
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        time.sleep(5)  # Add a delay to ensure the node has time to stop

        return "Node stopped successfully."
    except Exception as e:
        return f"Error: {str(e)}"

import time
@app.route('/stop_node', methods=['POST'])
def stop_node_endpoint():
    try:
        account_name = request.form.get('account_name')
        time.sleep(5)  # Add a delay to ensure the node has time to stop
        return stop_node(account_name)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})











def get_enode_url(account_name):
    try:
        datadir = f"/home/raspberry-node/.{account_name}"
        port = 4242
        networkid = 42

        # Start the Geth node and execute the command to get the enode URL
        command = f"geth --datadir {datadir} --port {port} --networkid {networkid} console --nodiscover --exec 'admin.nodeInfo.enode'"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        enode_result, _ = process.communicate()
        enode_url = enode_result.decode().strip()

        return enode_url
    except Exception as e:
        return str(e)

@app.route('/get_node_url', methods=['POST'])
def get_node_url():
    try:
        account_name = request.form.get('account_name')
        enode_url = get_enode_url(account_name)
        return jsonify({"status": "success", "enode_url": enode_url})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/add_peer', methods=['POST'])
def add_peer():
    try:
        account_name = request.form.get('account_name')
        enode_url = request.form.get('enode_url')
        
        # Construct the command to add a peer
        add_peer_command = (
            f"geth --datadir /home/raspberry-node/.{account_name} --exec 'admin.addPeer(\"{enode_url}\")'"
        )
        
        # Execute the command to add a peer
        add_peer_process = subprocess.Popen(add_peer_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        add_peer_process.wait()
        
        if add_peer_process.returncode == 0:
            return jsonify({"status": "success", "message": "Peer added successfully."})
        else:
            error_message = add_peer_process.stderr.read().decode('utf-8')
            return jsonify({"status": "error", "message": f"Error adding peer: {error_message}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/get_peers', methods=['GET'])
def get_peers():
    try:
        # Use an absolute path for the datadir to avoid issues with the current working directory
        datadir = "/home/raspberry-node"
        command = f"geth --datadir {datadir} --http --http.api admin --exec 'admin.peers' attach"
        stdout, stderr = run_command(command)

        peers = []
        for line in stdout.splitlines():
            peer_data = line.strip().split()
            if len(peer_data) == 3:
                peers.append({"name": peer_data[0], "id": peer_data[1], "address": peer_data[2]})

        return jsonify({"status": "success", "peers": peers})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/get_accounts', methods=['GET'])
def get_accounts():
    try:
        # Use an absolute path for the datadir to avoid issues with the current working directory
        datadir = "/home/raspberry-node"
        command = f"geth --datadir {datadir} account list"
        stdout, stderr = run_command(command)

        accounts = [account.strip().split()[1] for account in stdout.splitlines()]
        return jsonify({"status": "success", "accounts": accounts})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/set_minerbase', methods=['POST'])
def set_minerbase():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON data"})

        account_address = data.get('account_address')
        if not account_address:
            return jsonify({"status": "error", "message": "Account address is required"})

        # Use an absolute path for the datadir to avoid issues with the current working directory
        datadir = "/home/raspberry-node"
        command = f"geth --datadir {datadir} --http --http.api admin,miner --exec 'miner.setEtherbase(\"{account_address}\")' attach"
        stdout, stderr = run_command(command)

        if "true" in stdout:
            return jsonify({"status": "success", "message": "Miner base set successfully."})
        else:
            return jsonify({"status": "error", "message": f"Failed to set miner base. Error: {stderr}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

import os

# ... (Previous code)

@app.route('/start_mining', methods=['GET'])
def start_mining():
    try:
        # Use an absolute path for the datadir to avoid issues with the current working directory
        datadir = "/home/raspberry-node"
        command = f"geth --datadir {datadir} --http --http.api eth,net,web3 --allow-insecure-unlock --unlock 0 --password /path/to/password.txt --mine"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()

        if process.returncode == 0:
            return jsonify({"status": "success", "message": "Mining started successfully."})
        else:
            return jsonify({"status": "error", "message": "Failed to start mining."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/stop_mining', methods=['GET'])
def stop_mining():
    try:
        # Use an absolute path for the datadir to avoid issues with the current working directory
        datadir = "/home/raspberry-node"
        command = f"geth --datadir {datadir} --http --http.api miner --exec 'miner.stop()' attach"
        stdout, stderr = run_command(command)

        if not stderr:
            return jsonify({"status": "success", "message": "Mining stopped successfully."})
        else:
            return jsonify({"status": "error", "message": f"Failed to stop mining. Error: {stderr}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/delete_blockchain/<account_name>', methods=['GET'])
def delete_blockchain(account_name):
    try:
        # Use an absolute path for the datadir to avoid issues with the current working directory
        datadir = f"/home/raspberry-node/.{account_name}"
        command = f"rm -rf {datadir}/geth"
        os.system(command)

        return jsonify({"status": "success", "message": "Blockchain deleted successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
