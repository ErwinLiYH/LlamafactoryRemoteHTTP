# LlamafactoryRemoteHTTP

LlamafactoryRemoteHTTP is a Python package that provides an HTTP server and client for interacting with LLaMA-Factory models remotely. It allows users to run a server on a remote machine and send requests to perform various operations, such as managing configurations, running commands, and uploading files.

---

## Features

- Start an HTTP server to expose LLaMA-Factory functionality
- Perform operations like configuration management, file uploads, and command execution
- Interact with the server using Python or `curl`

---

## Installation

Make sure you have Python 3.8 or higher installed. Clone the repository and install the package:

```bash
git clone https://github.com/ErwinLiYH/LlamafactoryRemoteHTTP.git
cd LlamafactoryRemoteHTTP
pip install .
```

---

## Usage

### 1. Start the Server on the Remote Machine

Run the server on the remote machine, specifying the path to the LLaMA-Factory source code and the port to use:

```bash
python -m llf_server.llamafactory_server --llama_factory_path /path/to/llamafactory --port 8000
# or
llf-server --llama_factory_path /path/to/llamafactory --port 8000
```

- Replace `/path/to/llamafactory` with the actual path to your LLaMA-Factory source code.
- Replace `8000` with the desired port number.

---

### 2. Using the API

Once the server is running, you can interact with it using Python or `curl`. Below are examples for each functionality.

---

#### **Get Server Status**

**Python Example:**

```python
from llf_server.llamafactory_server_call import LLamaFactoryClient

client = LLamaFactoryClient("http://<remote-server-ip>:8000")
status = client.get_server_status()
print("Server Status:", status)
client.close()
```

**Curl Example:**

```bash
curl http://<remote-server-ip>:8000/status
```

---

#### **Run a Command**

The **Run Command** API allows you to create a new process on the remote server to execute a specified command. It streams the standard output and error (stdout & stderr) of the command in real-time, enabling you to monitor the execution progress directly. When running a command, the working directory (`pwd`) is set to the LLaMA-Factory path specified during server startup, and the environment variables (`env`) are inherited from the shell environment in which the server is running.

**Python Example:**

```python
from llf_server import LLamaFactoryClient

client = LLamaFactoryClient("http://<remote-server-ip>:8000")
process_id, output = client.run_command(
    command="llamafactory-cli train example/train_lora/xxx.yaml",
    output_file="output.log", # output the std of this command to file
    print_output=True, # print the std of this command
    process_id="test" # the name of process for this command (name using in /processes API)
)
print("Process ID:", process_id)
print("Command Output:", output)
client.close()
```

**Curl Example:**

```bash
curl -X POST http://<remote-server-ip>:8000/run_command \
-H "Content-Type: application/json" \
-d '{"command": "llamafactory-cli train example/train_lora/xxx.yaml", "process_id": "example_process"}'
```

> **Note:** If you interrupt the execution of Python or `curl` commands (e.g., using `Ctrl-C`), the corresponding process on the remote server will also be terminated.

> **Tip:** You can also use the **Run Command** API to start fine-tuned models with tools like `vllm`. This API can create a process to run any commands in remote server.

---

#### **List All Processes**

This API can list all processes currently running on the remote server that were initiated using the **Run Command** API.

**Response Structure:**

```json
{
    "processes": {
        "example_process": {
            "pid": 12345,
            "command": "llamafactory-cli train example/train_lora/xxx.yaml",
            "status": "running",
            "start_time": "2023-10-01T12:00:00Z"
        },
        "another_process": {
            "pid": 67890,
            "command": "llamafactory-cli evaluate example/eval.yaml",
            "status": "exited",
            "start_time": "2023-10-01T11:00:00Z",
            "returncode": 0
        }
    }
}
```

Each process includes details such as `pid` (process ID), `command` (the executed command), `status` (e.g., `running` or `exited`), `start_time` (when the process started), and `returncode` (exit code, if applicable).

**Python Example:**

```python
from llf_server import LLamaFactoryClient

client = LLamaFactoryClient("http://<remote-server-ip>:8000")
processes = client.list_processes()
print("Processes:", processes)
client.close()
```

**Curl Example:**

```bash
curl http://<remote-server-ip>:8000/processes
```

---

#### **Manually Clean Up Processes**

The **Manually Clean Up Processes** API is used to remove metadata of processes that have already exited from the server's process registry, ensuring the registry remains clean and up-to-date.

**Python Example:**

```python
from llf_server import LLamaFactoryClient

client = LLamaFactoryClient("http://<remote-server-ip>:8000")
cleanup_result = client.manual_cleanup()
print("Cleanup Result:", cleanup_result)
client.close()
```

**Curl Example:**

```bash
curl -X POST http://<remote-server-ip>:8000/cleanup
```

---

#### **Get Configuration File**

This function is designed to retrieve configuration data from a YAML config file or the `dataset.json` file.
It parses the content of the specified file and returns the corresponding data structure.

**Filepath must relative to the llamafactory path.**

**Python Example:**

```python
from llf_serverl import LLamaFactoryClient

client = LLamaFactoryClient("http://<remote-server-ip>:8000")
config = client.get_config("example/train_lora/llama_lora.yaml")
print("Config:", config)
client.close()
```

**Curl Example:**

```bash
curl http://<remote-server-ip>:8000/config/example/train_lora/llama_lora.yaml
```

---

#### **Update Configuration**

**Python Example:**

This API is used to modify YAML configuration files or `dataset.json`. 
The example demonstrates how to update the `model_name_or_path` field in 
`examples/merge_lora/llama3_full_sft.yaml` to a new path.

```python
from llf_server import LLamaFactoryClient

client = LLamaFactoryClient("http://<remote-server-ip>:8000")
update_result = client.update_yaml_config(
    file_path="examples/merge_lora/llama3_full_sft.yaml",
    config={"model_name_or_path": "new/path"},
    modified_file_path=...  # if None or same with file_path, replace original file, or save to a new file
)
print("Update Result:", update_result)
client.close()
```

**Curl Example:**

```bash
curl -X POST http://<remote-server-ip>:8000/update_yaml \
-H "Content-Type: application/json" \
-d '{"file_path": "examples/merge_lora/llama3_full_sft.yaml", "config": {"model_name_or_path": "new/path"}'
```

If add/modify a dataset to `dataset.json`, using function `update_json_config` or endpoint `\update_json`.

<details>
<summary>Updating Configuration Details</summary>

Updating Configuration relies on [`deep_update`](https://github.com/ErwinLiYH/LlamafactoryRemoteHTTP/blob/main/llf_server/llamafactory_server.py#L104), the `deep_update` function is a utility used to recursively merge two dictionaries. It takes a `source` dictionary and an `overrides` dictionary as input. For each key in `overrides`, it checks if the value is a dictionary. If so, it recursively updates the corresponding nested dictionary in `source`. Otherwise, it directly replaces the value in `source` with the value from `overrides`. This ensures that only the specified fields in the configuration are updated while preserving the rest of the structure.

For example:
```python
source = {"a": {"b": 1, "c": 2}, "d": 3}   # original config (json or yaml)
overrides = {"a": {"b": 10}, "d": 4}       # `config` parameter
result = deep_update(source, overrides)
# result: {"a": {"b": 10, "c": 2}, "d": 4}
```
This function is used in the API to modify configuration files (`YAML` or `JSON`) based on the provided `config` parameter.

</details>

**Filepath must be relative to the llamafactory path.**

---

#### **Upload a File**

**Python Example:**

```python
from pathlib import Path
from llf_server.llamafactory_server_call import LLamaFactoryClient

client = LLamaFactoryClient("http://<remote-server-ip>:8000")
upload_result = client.upload_data_file(Path("data/test_data.csv"))
print("Upload Result:", upload_result)
client.close()
```

**Curl Example:**

```bash
curl -X POST http://<remote-server-ip>:8000/upload_data \
-F "file=@test_data.csv"
```

---


## ALL API Endpoints

| Endpoint         | Method | Description                          |
|-------------------|--------|--------------------------------------|
| `/status`         | GET    | Get server status                   |
| `/cleanup`        | POST   | Manually clean up processes         |
| `/processes`      | GET    | List all processes                  |
| `/config/{path}`  | GET    | Get configuration file              |
| `/update_yaml`    | POST   | Update YAML configuration           |
| `/update_json`    | POST   | Update JSON configuration           |
| `/upload_data`    | POST   | Upload a file                       |
| `/run_command`    | POST   | Run a command and stream output     |

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

## Acknowledgments

This project is built to enhance the usability of LLaMA-Factory models in remote environments.