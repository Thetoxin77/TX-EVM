from web3 import Web3
import time
import random
from eth_account import Account
import sys
import json

class ChainTransfer:
    def __init__(self, chain_config_file='Chain_list.json'):
        # Load chain configurations
        try:
            with open(chain_config_file, 'r') as f:
                self.chains = json.load(f)['chains']
        except Exception as e:
            print(f"Error membaca konfigurasi: {e}")
            sys.exit(1)

    def select_chain(self):
        """Pilih chain dari daftar yang tersedia"""
        print("Pilih Jaringan:")
        for i, chain in enumerate(self.chains, 1):
            print(f"{i}. {chain['name']}")
        
        while True:
            try:
                choice = int(input("Masukkan nomor jaringan: "))
                if 1 <= choice <= len(self.chains):
                    return self.chains[choice-1]
                else:
                    print("Pilihan tidak valid!")
            except ValueError:
                print("Masukkan nomor yang valid!")

    def connect_to_chain(self, chain_config):
        """Sambungkan ke jaringan blockchain"""
        try:
            web3 = Web3(Web3.HTTPProvider(chain_config['rpc_url']))
            
            if not web3.isConnected():
                print(f"Gagal terhubung ke {chain_config['name']}")
                return None, None
            
            print(f"✅ Terhubung ke {chain_config['name']}")
            print(f"🔗 Chain ID: {chain_config['chain_id']}")
            print(f"💰 Mata Uang: {chain_config['currency']}")
            
            return web3, chain_config
        
        except Exception as e:
            print(f"Error koneksi: {e}")
            return None, None

    def load_private_keys(self, filename='evm_private_keys.txt'):
        """Muat private keys dari file"""
        try:
            with open(filename, 'r') as f:
                keys = [line.strip() for line in f if line.strip()]
            print(f"✅ Berhasil memuat {len(keys)} private keys")
            return keys
        except FileNotFoundError:
            print(f"❌ File {filename} tidak ditemukan!")
            return []

    def load_addresses(self, filename='listaddress.txt'):
        """Muat daftar alamat tujuan"""
        try:
            with open(filename, 'r') as f:
                addresses = [line.strip() for line in f if line.strip()]
            print(f"✅ Berhasil memuat {len(addresses)} alamat")
            return addresses
        except FileNotFoundError:
            print(f"❌ File {filename} tidak ditemukan!")
            return []

    def is_valid_address(self, web3, address):
        """Validasi alamat blockchain"""
        return web3.isAddress(address) and len(address) == 42

    def transfer_token(self, web3, chain_config, sender, sender_key, recipient, amount):
        """Kirim token antar alamat"""
        try:
            # Persiapan transaksi
            tx_config = {
                'chainId': chain_config['chain_id'],
                'from': sender,
                'to': recipient,
                'value': web3.toWei(amount, 'ether'),
                'nonce': web3.eth.get_transaction_count(sender),
                'gasPrice': web3.eth.gas_price
            }

            # Estimasi gas
            tx_config['gas'] = web3.eth.estimate_gas(tx_config)

            # Tanda tangani transaksi
            signed_tx = web3.eth.account.sign_transaction(tx_config, sender_key)
            
            # Kirim transaksi
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Tunggu konfirmasi
            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            
            print(f"✅ Transfer {amount} {chain_config['currency']} berhasil!")
            print(f"📍 TX Hash: {web3.toHex(tx_hash)}")
            
            return True
        
        except Exception as e:
            print(f"❌ Gagal transfer: {e}")
            return False

    def execute_transfer(self):
        """Proses utama transfer token dengan delay dan jumlah yang ditentukan"""
        while True:  # Loop untuk kembali ke menu setelah semua transaksi selesai
            # Pilih chain
            chain_config = self.select_chain()
            
            # Sambungkan ke chain
            web3, chain_config = self.connect_to_chain(chain_config)
            
            if not web3:
                return
            
            # Muat private keys dan alamat
            private_keys = self.load_private_keys()
            addresses = self.load_addresses()
            
            if not private_keys or not addresses:
                return
            
            # Filter alamat valid
            valid_addresses = [
                addr for addr in addresses 
                if self.is_valid_address(web3, addr)
            ]
            
            print(f"✅ Total alamat valid: {len(valid_addresses)}")
            
            # Input jumlah minimal dan maksimal
            min_amount = float(input("Masukkan jumlah minimal yang akan dikirim: "))
            max_amount = float(input("Masukkan jumlah maksimal yang akan dikirim: "))
            
            # Input delay antar transfer
            min_delay = float(input("Masukkan delay minimal antar transfer (detik): "))
            max_delay = float(input("Masukkan delay maksimal antar transfer (detik): "))
            
            # Proses transfer untuk setiap private key
            for pk in private_keys:
                try:
                    # Buat akun dari private key
                    account = Account.from_key(pk)
                    sender = account.address
                    
                    print(f"\n🔑 Mengirim dari: {sender}")
                    
                    # Transfer ke setiap alamat
                    for recipient in valid_addresses:
                        # Hitung jumlah transfer acak
                        amount = random.uniform(min_amount, max_amount)
                        
                        # Lakukan transfer
                        success = self.transfer_token(
                            web3, 
                            chain_config, 
                            sender, 
                            pk, 
                            recipient, 
                            amount
                        )
                        
                        # Jika transfer gagal, lanjut ke private key berikutnya
                        if not success:
                            print(f"🔄 Melanjutkan ke private key berikutnya setelah gagal transfer.")
                            break  # Break out of the inner loop to go to the next private key
                        
                        # Jeda antar transfer
                        delay = random.uniform(min_delay, max_delay)
                        print(f"⏳ Menunggu {delay:.2f} detik sebelum transfer berikutnya...")
                        time.sleep(delay)
                
                except Exception as e:
                    print(f"❌ Kesalahan pada private key: {e}")

            # Tanyakan apakah pengguna ingin melakukan transfer lagi
            repeat = input("Apakah Anda ingin melakukan transfer lagi? (y/n): ").strip().lower()
            if repeat != 'y':
                print("Terima kasih telah menggunakan aplikasi ini!")
                break  # Exit the loop and end the program

def main():
    transfer = ChainTransfer()
    transfer.execute_transfer()

if __name__ == '__main__':
    main()