import requests
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import closing
import time

class LLamaFactoryClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    # ====================
    # API for System Status
    # ====================
    def get_server_status(self) -> Dict:
        """Get server status (GET /status)"""
        url = f"{self.base_url}/status"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def manual_cleanup(self) -> Dict:
        """Manually clean up processes (POST /cleanup)"""
        url = f"{self.base_url}/cleanup"
        response = requests.post(url)
        response.raise_for_status()
        return response.json()

    def list_processes(self) -> Dict:
        """List all processes (GET /processes)"""
        url = f"{self.base_url}/processes"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    # ====================
    # Configuration Management APIs
    # ====================
    def get_config(self, file_path: str) -> Dict:
        """Get configuration file (GET /config/{file_path})"""
        url = f"{self.base_url}/config/{file_path.lstrip('/')}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def update_yaml_config(
        self,
        file_path: str,
        config: Dict,
        modified_file_path: Optional[str] = None
    ) -> Dict:
        """Update YAML configuration (POST /update_yaml)"""
        url = f"{self.base_url}/update_yaml"
        payload = {
            "file_path": file_path,
            "config": config,
            "modified_file_path": modified_file_path
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def update_json_config(
        self,
        file_path: str,
        config: Dict,
        modified_file_path: Optional[str] = None
    ) -> Dict:
        """Update JSON configuration (POST /update_json)"""
        url = f"{self.base_url}/update_json"
        payload = {
            "file_path": file_path,
            "config": config,
            "modified_file_path": modified_file_path
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    # ====================
    # File Operation APIs
    # ====================
    def upload_data_file(
        self,
        file_path: str,
        save_path: str,
        timeout: int = 30
    ) -> Dict:
        """
        Upload data file (POST /upload_data)
        
        Args:
            file_path: Local file to upload
            save_path: Target path on the server (required)
                       If it ends with '/', treated as directory and the file will be saved inside it
                       with the original filename
            timeout: Request timeout in seconds
            
        Returns:
            Dict with upload details including saved_path
        """
        url = f"{self.base_url}/upload_data"
        
        file_path = Path(file_path)
        if not file_path.is_file():
            raise FileNotFoundError(f"File {file_path} not found.")
        
        params = {'save_path': save_path}
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            response = requests.post(
                url,
                files=files,
                params=params,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()

    # ====================
    # Command Execution APIs
    # ====================
    def run_command(
        self,
        command: str,
        output_file: Optional[str] = None,
        print_output: bool = True,
        process_id: Optional[str] = None,
        time_out: int = 5,
        sleep_time: int = 1
    ) -> Dict:
        """
        Execute a command and get streaming output (POST /run_command)
        Returns a generator containing process_id and real-time output
        """
        url = f"{self.base_url}/run_command"
        payload = {
            "command": command,
            "process_id": process_id or f"client_{id(self)}"
        }
        with closing(requests.post(url, json=payload, stream=True, timeout=(time_out, None))) as resp:
            print(f"debug {command} after post, resp code: {resp.status_code}")
            resp.raise_for_status()
            
            # Get process_id
            process_id = resp.headers.get('X-Process-ID')
            pid = resp.headers.get('X-PID')
            if not process_id:
                raise ValueError("No process ID returned from server.")
            
            # Handle streaming output
            file_handle = open(output_file, 'a') if output_file else None
            
            try:
                for chunk in resp.iter_lines():
                    if chunk:  # Filter keep-alive empty chunks
                        decoded = chunk.decode('utf-8', errors='replace')
                        
                        # Real-time output to console
                        if print_output:
                            print(decoded, flush=True)
                        
                        # Write to file (if specified)
                        if file_handle:
                            file_handle.write(decoded)
                            file_handle.flush()
            finally:
                if file_handle:
                    file_handle.close()
            
            time.sleep(sleep_time)  # Ensure totally finished
            return process_id, pid
        
    def run_command_bg(
        self,
        command: str,
        process_id: Optional[str] = None,
        time_out: int = 5
    ):
        url = f"{self.base_url}/run_command"
        payload = {
            "command": command,
            "process_id": process_id or f"client_{id(self)}"
        }
        resp = requests.post(url, json=payload, stream=True, timeout=(time_out, None))
        resp.raise_for_status()
        process_id = resp.headers.get('X-Process-ID')
        pid = resp.headers.get('X-PID')
        if not process_id:
            raise ValueError("No process ID returned from server.")
        if not pid:
            raise ValueError("No PID returned from server.")
        return process_id, pid, resp
    
    def watch_bg_command(
        self,
        response,
        output_file: Optional[str] = None,
        print_output: bool = True,
        process_id: Optional[str] = None,
        sleep_time: int = 1
    ) -> Dict:
        # Handle streaming output
        file_handle = open(output_file, 'a') if output_file else None

        try:
            for chunk in response.iter_lines():
                if chunk:  # Filter keep-alive empty chunks
                    decoded = chunk.decode('utf-8', errors='replace')
                    
                    # Real-time output to console
                    if print_output:
                        print(decoded, flush=True)
                    
                    # Write to file (if specified)
                    if file_handle:
                        file_handle.write(decoded)
                        file_handle.flush()
        finally:
            if file_handle:
                file_handle.close()

        time.sleep(sleep_time)  # Ensure totally finished
        return process_id

    def kill_process(self, pid: int) -> Dict:
        """Kill a running process by its ID (DELETE /process/{pid})"""
        url = f"{self.base_url}/process/{pid}"
        response = requests.delete(url)
        response.raise_for_status()
        return response.json()

# Usage examples
if __name__ == "__main__":
    client = LLamaFactoryClient("http://localhost:9000")
    
    # Example 1: Get server status
    print("Server Status:", client.get_server_status())
    
    # Example 2: Run a command and save output
    pid, result = client.run_command(
        command="echo 'Hello World' && sleep 2",
        output_file="output.log"
    )
    print("Command Result:", result)
    
    # Example 3: Upload a file
    upload_result = client.upload_data_file(Path("test_data.csv"), save_path="/uploads/")
    print("Upload Result:", upload_result)
    
    # Example 4: Update configuration
    update_result = client.update_yaml_config(
        file_path="configs/model.yaml",
        config={"training": {"batch_size": 32}}
    )
    print("Config Update:", update_result)
    
    client.close()