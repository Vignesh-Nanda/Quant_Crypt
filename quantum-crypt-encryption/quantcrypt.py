import os
import json
from Crypto.PublicKey import RSA
from aws_integration.s3_upload import upload_to_s3, list_s3_files, download_from_s3
from aws_integration.config_manager import get_config, update_config
from performance_benchmark.benchmark import benchmark
from encryption_module.encryption import encrypt
from encryption_module.decryption import decrypt
import base64
from Crypto.Random import get_random_bytes

def generate_rsa_keypair():
    """Generate an RSA keypair and return the keys as strings."""
    key = RSA.generate(2048)
    private_key = key.export_key().decode('utf-8')
    public_key = key.publickey().export_key().decode('utf-8')
    return private_key, public_key

def generate_aes_key() -> str:
    """Generate a base64-encoded AES key."""
    aes_key = get_random_bytes(32)  # 32 bytes for AES-GCM-256
    return base64.b64encode(aes_key).decode('utf-8')

def save_keys_to_json(private_key: str, public_key: str, aes_key: str, file_path: str='./encryption_module/key.json'):
    """Save the RSA keys and AES key to a JSON file."""
    keys = {
        'private_key': private_key,
        'public_key': public_key,
        'aes_key': aes_key
    }
    with open(file_path, 'w') as file:
        json.dump(keys, file, indent=4)

def generate_and_save_keys(file_path: str='./encryption_module/key.json'):
    """Generate RSA keypair, generate AES key, and save to JSON file."""
    private_key, public_key = generate_rsa_keypair()
    aes_key = generate_aes_key()
    save_keys_to_json(private_key, public_key, aes_key, file_path)
    return private_key, public_key, aes_key  # Return the keys


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu():
    """Print the main menu."""
    clear_screen()

    bright_red = "\033[91m"
    bright_yellow = "\033[93m"
    bright_green = "\033[92m"
    bright_blue = "\033[94m"
    bright_magenta = "\033[95m"
    bright_cyan = "\033[96m"
    bold = "\033[1m"
    underline = "\033[4m"
    background_blue = "\033[44m"
    reset = "\033[0m"

    print(f"{background_blue}{bright_cyan}   ____                       _      ___                      _   {reset}")
    print(f"{background_blue}{bright_green}  /___ \\ _   _   __ _  _ __  | |_   / __\\ _ __  _   _  _ __  | |_ {reset}")
    print(f"{background_blue}{bright_yellow} //  / /| | | | / _` || '_ \\ | __| / /   | '__|| | | || '_ \\ | __|{reset}")
    print(f"{background_blue}{bright_magenta}/ \\_/ / | |_| || (_| || | | || |_ / /___ | |   | |_| || |_) || |_ {reset}")
    print(f"{background_blue}{bright_red}\\___,_\\  \\__,_| \\__,_||_| |_| \\__|\\____/ |_|    \\__, || .__/  \\__|{reset}")
    print(f"{background_blue}                                                |___/ |_|         {reset}")

    print(f"{bold}{bright_yellow}                Version : 1.0.0                {reset}")
    print(f"{underline}{bright_red}[-] Tool Created by Someone                {reset}")
    print(f"{bright_cyan}[::] {bold}Select an Operation{reset} {bright_cyan}[::]{reset}")

    print(f"{bright_green}[01]{reset} {bright_cyan}Encrypt and Upload Data{reset}")
    print(f"{bright_green}[02]{reset} {bright_cyan}Decrypt and Download Data{reset}")
    print(f"{bright_green}[03]{reset} {bright_cyan}View Configuration{reset}")
    print(f"{bright_green}[04]{reset} {bright_cyan}Update Configuration{reset}")
    print(f"{bright_green}[05]{reset} {bright_cyan}Benchmark Performance{reset}")
    print(f"{bright_green}[06]{reset} {bright_yellow}Exit{reset}")

    print(f"\n{bright_yellow}[-] {bold}Select an option : {reset}", end='')

def handle_encrypt_and_upload():
    """Handle data encryption, create a file, and upload it to S3."""
    data = input("Enter data to encrypt: ")
    encrypted_data = encrypt(data)
    
    if encrypted_data is None:
        print("Encryption failed. Encrypted data is None.")
        return
    
    file_name = input("Enter file name to upload to S3 (without .txt extension): ").strip() + '.txt'
    if not file_name:
        print("File name cannot be empty. Please provide a valid file name.")
        return
    
    try:
        with open(file_name, 'w') as file:
            file.write(encrypted_data)
        print(f"Created local file: {file_name}")
    except Exception as e:
        print(f"Failed to create file: {e}")
        return
    
    try:
        response = upload_to_s3(file_name, encrypted_data)
        if response:
            print(f"Data encrypted and uploaded as {file_name}.")
    except Exception as e:
        print(f"Failed to upload to S3: {e}")
    
    input("\nPress Enter to return to the main menu...")

    
def handle_decrypt_and_download():
    """Handle data decryption and download from S3."""
    file_name = input("Enter file name to download from S3: ")
    encrypted_data_bytes = download_from_s3(file_name)
    
    if encrypted_data_bytes:
        try:
            # Convert bytes to JSON string if needed
            if isinstance(encrypted_data_bytes, bytes):
                encrypted_data_str = encrypted_data_bytes.decode('utf-8')
            else:
                encrypted_data_str = encrypted_data_bytes
            
            # print(encrypted_data_str)
            
            # Convert JSON string to dictionary
            encrypted_data = json.loads(encrypted_data_str)
            
            # Extract encrypted data and AES key from JSON
            encrypted_data_content = encrypted_data['encrypted_data']
            encrypted_aes_key_str = encrypted_data['encrypted_aes_key']
            
            # Decrypt data
            decrypted_data = decrypt(encrypted_data_content, encrypted_aes_key_str)
            print(f"Decrypted data: {decrypted_data}")
        except Exception as e:
            print(f"An error occurred: {e}")

    else:
        print("No data found for the given file name.")
    input("\nPress Enter to return to the main menu...")

def handle_view_config():
    """Handle viewing the configuration."""
    config = get_config()
    print(json.dumps(config, indent=4))
    input("\nPress Enter to return to the main menu...")

def handle_update_config():
    """Handle updating the configuration."""
    aws_access_key_id = input("Enter new AWS Access Key ID (leave blank to keep current): ")
    aws_secret_access_key = input("Enter new AWS Secret Access Key (leave blank to keep current): ")
    aws_region = input("Enter new AWS Region (leave blank to keep current): ")
    aws_s3_bucket_name = input("Enter new AWS S3 Bucket Name (leave blank to keep current): ")

    update_config(
        aws_access_key_id or None,
        aws_secret_access_key or None,
        aws_region or None,
        aws_s3_bucket_name or None
    )
    print("Configuration updated successfully.")
    input("\nPress Enter to return to the main menu...")

def handle_benchmark():
    """Handle performance benchmarking."""
    data = input("Enter data to benchmark (e.g., 'Test data'): ").encode()
    benchmark(data)
    input("\nPress Enter to return to the main menu...")

def main():
    """Main function to run the CLI application."""
    # private_key, public_key = generate_rsa_keypair()

    # # Generate AES key
    # aes_key = generate_aes_key()

    # # Save RSA keypair and AES key to JSON file
    # save_keys_to_json(private_key, public_key, aes_key)
    while True:
        print_menu()
        option = input().strip()

        if option == '01':
            handle_encrypt_and_upload()
        elif option == '02':
            handle_decrypt_and_download()
        elif option == '03':
            handle_view_config()
        elif option == '04':
            handle_update_config()
        elif option == '05':
            handle_benchmark()
        elif option == '06':
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
