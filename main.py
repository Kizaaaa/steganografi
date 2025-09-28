import os
import random
import hashlib
from typing import List, Tuple

class VigenereCipher:
    @staticmethod
    def encrypt(plaintext: str, key: str) -> str:
        """Encrypt text using Vigenere cipher"""
        key = key.upper()
        plaintext = plaintext.upper()
        encrypted = ""
        key_index = 0
        
        for char in plaintext:
            if char.isalpha():
                shift = ord(key[key_index % len(key)]) - ord('A')
                encrypted_char = chr((ord(char) - ord('A') + shift) % 26 + ord('A'))
                encrypted += encrypted_char
                key_index += 1
            else:
                encrypted += char
        
        return encrypted
    
    @staticmethod
    def decrypt(ciphertext: str, key: str) -> str:
        """Decrypt text using Vigenere cipher"""
        key = key.upper()
        ciphertext = ciphertext.upper()
        decrypted = ""
        key_index = 0
        
        for char in ciphertext:
            if char.isalpha():
                shift = ord(key[key_index % len(key)]) - ord('A')
                decrypted_char = chr((ord(char) - ord('A') - shift + 26) % 26 + ord('A'))
                decrypted += decrypted_char
                key_index += 1
            else:
                decrypted += char
        
        return decrypted

class MP3Steganography:
    def __init__(self):
        self.magic_header = b"STEGO"  # Magic bytes to identify steganographic content
        self.end_marker = b"ENDSTEGO"  # End marker
    
    def _embed_bits(self, byte_val: int, bits: int, lsb_count: int) -> int:
        """Embed multiple bits into the LSBs of a byte"""
        # Create mask to clear the LSBs we want to modify
        mask = (0xFF << lsb_count) & 0xFF
        # Clear the LSBs and set the new bits
        return (byte_val & mask) | (bits & ((1 << lsb_count) - 1))
    
    def _extract_bits(self, byte_val: int, lsb_count: int) -> int:
        """Extract multiple bits from the LSBs of a byte"""
        return byte_val & ((1 << lsb_count) - 1)
    
    def _find_safe_positions_improved(self, mp3_data: bytes) -> List[int]:
        """Improved safe position detection for better MP3 compatibility"""
        safe_positions = []
        
        # Skip ID3v2 header if present
        start_pos = 0
        if mp3_data[:3] == b'ID3':
            if len(mp3_data) >= 10:
                size = int.from_bytes(mp3_data[6:10], 'big')
                # ID3v2 size is synchsafe integer
                size = ((size & 0x7f000000) >> 3) | ((size & 0x7f0000) >> 2) | ((size & 0x7f00) >> 1) | (size & 0x7f)
                start_pos = 10 + size
        
        # Use a more conservative approach - skip more of the beginning
        # and use wider spacing to avoid frame boundaries
        safe_start = max(start_pos + 4096, 4096)  # Skip at least 4KB
        
        # Use every 16th byte for maximum safety, but skip 0xFF bytes completely
        pos = safe_start
        while pos < len(mp3_data):
            # Skip bytes that could be frame sync or important structure
            if (mp3_data[pos] != 0xFF and 
                mp3_data[pos] != 0x00 and  # Avoid null bytes
                pos % 16 == 0):  # Every 16th byte only
                safe_positions.append(pos)
            pos += 1
        
        return safe_positions
    
    def _find_safe_positions(self, mp3_data: bytes) -> List[int]:
        """Find safe positions in MP3 file that won't break playback"""
        safe_positions = []
        
        # Simple but reliable approach: skip first part of file and use every Nth byte
        # Skip ID3 header and initial frames (first 2048 bytes to be very safe)
        start_pos = 2048
        
        # Use every 8th byte starting from safe position
        # This avoids most critical MP3 structure while providing enough positions
        pos = start_pos
        while pos < len(mp3_data):
            # Skip potential frame sync bytes (0xFF)
            if mp3_data[pos] != 0xFF:
                safe_positions.append(pos)
            pos += 8  # Every 8th byte for safety
        
        return safe_positions

    def _generate_positions(self, seed: str, file_size: int, data_size: int, randomize: bool, lsb_count: int = 1, mp3_data: bytes = None) -> List[int]:
        """Generate positions for embedding data"""
        # Calculate total bits needed
        data_bits_needed = data_size * 8
        return self._generate_positions_mp3_safe(seed, file_size, data_bits_needed, randomize, lsb_count, mp3_data)
    
    def _generate_positions_mp3_safe(self, seed: str, file_size: int, data_bits_needed: int, randomize: bool, lsb_count: int, mp3_data: bytes = None) -> List[int]:
        """Generate MP3-safe positions with improved detection"""
        if mp3_data is not None:
            # Use improved safe position detection
            safe_positions = self._find_safe_positions_improved(mp3_data)
            
            # Calculate positions needed based on LSB count
            positions_needed = (data_bits_needed + lsb_count - 1) // lsb_count  # Ceiling division
            
            if len(safe_positions) < positions_needed:
                # Fallback to simpler method if not enough safe positions
                return self._generate_positions_simple_safe(seed, file_size, positions_needed, randomize)
            
            if randomize:
                random.seed(seed)
                positions = random.sample(safe_positions, positions_needed)
                positions.sort()
                return positions
            else:
                hash_obj = hashlib.md5(seed.encode())
                start_index = int(hash_obj.hexdigest()[:8], 16) % max(1, len(safe_positions) - positions_needed)
                return safe_positions[start_index:start_index + positions_needed]
        else:
            positions_needed = (data_bits_needed + lsb_count - 1) // lsb_count
            return self._generate_positions_simple_safe(seed, file_size, positions_needed, randomize)
    
    def _generate_positions_simple_safe(self, seed: str, file_size: int, positions_needed: int, randomize: bool) -> List[int]:
        """Simple but safe position generation"""
        if randomize:
            random.seed(seed)
            # Use wider range but still avoid critical areas
            available_positions = []
            for i in range(4096, file_size):  # Skip first 4KB
                if i % 16 == 0:  # Every 16th byte for safety
                    available_positions.append(i)
            
            if len(available_positions) < positions_needed:
                # Fallback to sequential if not enough positions
                return list(range(4096, 4096 + positions_needed))
            
            positions = random.sample(available_positions, positions_needed)
            positions.sort()
            return positions
        else:
            hash_obj = hashlib.md5(seed.encode())
            start_offset = int(hash_obj.hexdigest()[:8], 16) % 2048 + 4096
            return list(range(start_offset, start_offset + positions_needed))
    
    def _generate_positions_fallback(self, seed: str, file_size: int, data_size: int, randomize: bool) -> List[int]:
        """Fallback position generation method"""
        if randomize:
            # Use seed to generate random positions
            random.seed(seed)
            # Skip MP3 header (first 1024 bytes to be safe)
            available_positions = list(range(1024, file_size))
            positions = random.sample(available_positions, min(data_size * 8, len(available_positions)))
            positions.sort()
            return positions
        else:
            # Use sequential positions starting from a seed-determined offset
            hash_obj = hashlib.md5(seed.encode())
            start_offset = int(hash_obj.hexdigest()[:8], 16) % 1024 + 1024
            return list(range(start_offset, start_offset + data_size * 8))
    
    def validate_mp3_structure(self, mp3_path: str) -> bool:
        """Validate basic MP3 structure to ensure playability"""
        try:
            with open(mp3_path, 'rb') as f:
                data = f.read()
            
            if len(data) < 10:
                return False
            
            # Check for valid MP3 indicators
            pos = 0
            
            # Skip ID3v2 if present
            if data[:3] == b'ID3':
                if len(data) >= 10:
                    size = int.from_bytes(data[6:10], 'big')
                    size = ((size & 0x7f000000) >> 3) | ((size & 0x7f0000) >> 2) | ((size & 0x7f00) >> 1) | (size & 0x7f)
                    pos = 10 + size
            
            # Look for at least one valid MP3 frame
            frame_found = False
            search_limit = min(pos + 5000, len(data) - 4)  # Don't search entire file
            
            while pos < search_limit:
                if data[pos] == 0xFF and (data[pos + 1] & 0xE0) == 0xE0:
                    # Potential frame header found
                    header = int.from_bytes(data[pos:pos+4], 'big')
                    version = (header >> 19) & 0x3
                    layer = (header >> 17) & 0x3
                    bitrate_index = (header >> 12) & 0xF
                    sampling_freq = (header >> 10) & 0x3
                    
                    # Check if it's a valid frame
                    if (bitrate_index != 0 and bitrate_index != 15 and 
                        sampling_freq != 3 and layer != 0):
                        frame_found = True
                        break
                
                pos += 1
            
            return frame_found
            
        except Exception as e:
            print(f"MP3 validation error: {e}")
            return False

    def _string_to_bytes(self, text: str) -> bytes:
        """Convert string to bytes"""
        return text.encode('utf-8')
    
    def _bytes_to_string(self, data: bytes) -> str:
        """Convert bytes to string"""
        try:
            return data.decode('utf-8')
        except:
            return str(data)
    
    def _embed_bit(self, byte_val: int, bit: int) -> int:
        """Embed a bit into the LSB of a byte"""
        return (byte_val & 0xFE) | bit
    
    def _extract_bit(self, byte_val: int) -> int:
        """Extract the LSB from a byte"""
        return byte_val & 1
    
    def embed_file(self, mp3_path: str, hidden_file_path: str, output_path: str, 
                   encrypt: bool, randomize: bool, seed: str, lsb_count: int = 1) -> bool:
        """Embed a file into an MP3 file using specified number of LSBs"""
        try:
            # Validate LSB count
            if lsb_count < 1 or lsb_count > 4:
                print("Error: LSB count must be between 1 and 4")
                return False
                
            print(f"Using {lsb_count} LSB(s) for embedding")
            
            # Validate input MP3 structure
            if not self.validate_mp3_structure(mp3_path):
                print("Warning: Input file may not be a valid MP3 file!")
            
            # Read the files
            with open(mp3_path, 'rb') as mp3_file:
                mp3_data = bytearray(mp3_file.read())
            
            with open(hidden_file_path, 'rb') as hidden_file:
                hidden_data = hidden_file.read()
            
            # Get original filename
            filename = os.path.basename(hidden_file_path)
            
            # Convert hidden data to string if needed and encrypt if requested
            if encrypt:
                # Convert to base64 for binary files to ensure it's text-safe
                import base64
                hidden_text = base64.b64encode(hidden_data).decode('ascii')
                encrypted_text = VigenereCipher.encrypt(hidden_text, seed)
                payload = self._string_to_bytes(encrypted_text)
            else:
                payload = hidden_data
            
            # Create metadata: encryption flag (1 byte) + filename length + filename + data length
            filename_bytes = filename.encode('utf-8')
            encryption_flag = b'\x01' if encrypt else b'\x00'
            metadata = encryption_flag + len(filename_bytes).to_bytes(2, 'big') + filename_bytes + len(payload).to_bytes(4, 'big')
            
            # Complete payload: magic header + metadata + actual data + end marker
            complete_payload = self.magic_header + metadata + payload + self.end_marker
            
            # Convert payload to bits (organized by LSB count)
            if lsb_count == 1:
                # Traditional single-bit embedding
                payload_bits = []
                for byte in complete_payload:
                    for i in range(8):
                        payload_bits.append((byte >> (7 - i)) & 1)
                
                # Generate embedding positions
                positions = self._generate_positions(seed, len(mp3_data), len(complete_payload), randomize, lsb_count)
                
                if len(positions) < len(payload_bits):
                    print(f"Error: MP3 file too small. Need {len(payload_bits)} positions, but only {len(positions)} available.")
                    return False
                
                # Embed single bits
                for i, bit in enumerate(payload_bits):
                    if i < len(positions):
                        pos = positions[i]
                        if pos < len(mp3_data):
                            mp3_data[pos] = self._embed_bit(mp3_data[pos], bit)
            else:
                # Multi-LSB embedding (2-4 bits per byte)
                # Convert payload to a flat bit array first
                all_payload_bits = []
                for byte in complete_payload:
                    for i in range(8):
                        all_payload_bits.append((byte >> (7 - i)) & 1)
                
                # Calculate positions needed for multi-LSB
                positions_needed = (len(all_payload_bits) + lsb_count - 1) // lsb_count
                
                # Generate embedding positions
                positions = self._generate_positions(seed, len(mp3_data), positions_needed, randomize, lsb_count)
                
                if len(positions) < positions_needed:
                    print(f"Error: MP3 file too small. Need {positions_needed} positions for {lsb_count}-LSB embedding, but only {len(positions)} available.")
                    return False
                
                # Embed bits in groups
                bit_index = 0
                for pos_index in range(positions_needed):
                    if pos_index >= len(positions):
                        break
                    
                    # Collect bits for this position
                    bits_to_embed = 0
                    actual_bits = min(lsb_count, len(all_payload_bits) - bit_index)
                    
                    for i in range(actual_bits):
                        if bit_index + i < len(all_payload_bits):
                            bit = all_payload_bits[bit_index + i]
                            bits_to_embed |= (bit << (actual_bits - 1 - i))
                    
                    # Embed the bits at this position
                    pos = positions[pos_index]
                    if pos < len(mp3_data):
                        mp3_data[pos] = self._embed_bits(mp3_data[pos], bits_to_embed, actual_bits)
                    
                    bit_index += actual_bits
                    
                    if bit_index >= len(all_payload_bits):
                        break
            
            # Write the modified MP3
            with open(output_path, 'wb') as output_file:
                output_file.write(mp3_data)
            
            # Validate output MP3 structure
            if self.validate_mp3_structure(output_path):
                print(f"File '{hidden_file_path}' successfully embedded into '{output_path}'")
                print("✓ Output MP3 structure validated - should be playable")
            else:
                print(f"File '{hidden_file_path}' embedded into '{output_path}' but MP3 structure may be damaged")
                print("⚠ Output file may not be playable")
            
            return True
            
        except Exception as e:
            print(f"Error embedding file: {str(e)}")
            return False
    
    def extract_file(self, stego_mp3_path: str, seed: str, output_dir: str = ".", lsb_count: int = 1) -> bool:
        """Extract a hidden file from an MP3 file"""
        try:
            # Read the steganographic MP3
            with open(stego_mp3_path, 'rb') as mp3_file:
                mp3_data = mp3_file.read()
            
            # Try both randomized and sequential positioning
            # Try randomized first as it's more common for security
            for randomize in [True, False]:
                try:
                    print(f"Trying {'randomized' if randomize else 'sequential'} positioning...")
                    
                    # Try with a fixed known size first (the actual payload size we embedded)
                    # Start with small search to find the header, then expand
                    for search_size in [100, 200, 500, 1000]:
                        print(f"  Trying search size: {search_size} bytes")
                        
                        # Generate positions the same way as embedding
                        positions_needed = (search_size * 8 + lsb_count - 1) // lsb_count if lsb_count > 1 else search_size
                        positions = self._generate_positions(seed, len(mp3_data), positions_needed, randomize, lsb_count)
                        
                        header_positions_needed = (len(self.magic_header) * 8 + lsb_count - 1) // lsb_count if lsb_count > 1 else len(self.magic_header) * 8
                        if len(positions) < header_positions_needed:
                            print(f"  Not enough positions: {len(positions)} < {header_positions_needed}")
                            continue
                        
                        # Extract data based on LSB count
                        if lsb_count == 1:
                            # Traditional single-bit extraction
                            extracted_bits = []
                            for pos in positions:
                                if pos < len(mp3_data):
                                    bit = self._extract_bit(mp3_data[pos])
                                    extracted_bits.append(bit)
                                else:
                                    break
                            
                            # Convert bits to bytes
                            extracted_bytes = []
                            for i in range(0, len(extracted_bits), 8):
                                if i + 7 < len(extracted_bits):
                                    byte_val = 0
                                    for j in range(8):
                                        byte_val |= (extracted_bits[i + j] << (7 - j))
                                    extracted_bytes.append(byte_val)
                        else:
                            # Multi-LSB extraction
                            all_extracted_bits = []
                            
                            for pos in positions:
                                if pos < len(mp3_data):
                                    # Extract multiple bits from this position
                                    bits = self._extract_bits(mp3_data[pos], lsb_count)
                                    
                                    # Convert bits back to individual bit array
                                    for i in range(lsb_count):
                                        bit = (bits >> (lsb_count - 1 - i)) & 1
                                        all_extracted_bits.append(bit)
                                else:
                                    break
                            
                            # Convert bit array to bytes
                            extracted_bytes = []
                            for i in range(0, len(all_extracted_bits), 8):
                                if i + 7 < len(all_extracted_bits):
                                    byte_val = 0
                                    for j in range(8):
                                        byte_val |= (all_extracted_bits[i + j] << (7 - j))
                                    extracted_bytes.append(byte_val)
                        
                        extracted_data = bytes(extracted_bytes)
                        
                        # Look for magic header
                        magic_pos = extracted_data.find(self.magic_header)
                        print(f"  Looking for magic header in {len(extracted_data)} bytes of extracted data")
                        
                        if magic_pos != -1:
                            print(f"Magic header found at position {magic_pos}! Using {'randomized' if randomize else 'sequential'} positioning with {search_size} byte search.")
                            break
                    
                    if magic_pos == -1:
                        print("Magic header not found with any search size")
                        continue
                    
                    print(f"Magic header found at position {magic_pos}! Using {'randomized' if randomize else 'sequential'} positioning.")
                    
                    # Start parsing from after magic header
                    data_start = magic_pos + len(self.magic_header)
                    
                    if data_start + 7 > len(extracted_data):  # Need at least 7 bytes for metadata
                        continue
                    
                    # Extract encryption flag (1 byte)
                    encryption_flag = extracted_data[data_start]
                    is_encrypted = encryption_flag == 1
                    data_start += 1
                    
                    # Extract filename length (2 bytes)
                    filename_len = int.from_bytes(extracted_data[data_start:data_start+2], 'big')
                    data_start += 2
                    
                    if data_start + filename_len + 4 > len(extracted_data):
                        continue
                    
                    # Extract filename
                    filename = extracted_data[data_start:data_start+filename_len].decode('utf-8')
                    data_start += filename_len
                    
                    # Extract data length (4 bytes)
                    data_len = int.from_bytes(extracted_data[data_start:data_start+4], 'big')
                    data_start += 4
                    
                    if data_start + data_len > len(extracted_data):
                        continue
                    
                    # Extract the actual data
                    file_data = extracted_data[data_start:data_start+data_len]
                    
                    # Use the encryption flag to determine if decryption is needed
                    final_data = file_data
                    
                    if is_encrypted:
                        try:
                            # Decrypt the data
                            import base64
                            decrypted_text = VigenereCipher.decrypt(file_data.decode('ascii'), seed)
                            final_data = base64.b64decode(decrypted_text.encode('ascii'))
                            print("Data was encrypted and has been decrypted.")
                        except Exception as e:
                            print(f"Decryption failed: {e}, using raw data.")
                            final_data = file_data
                    else:
                        print("Data was not encrypted.")
                    
                    # Save the extracted file
                    output_path = os.path.join(output_dir, filename)
                    with open(output_path, 'wb') as output_file:
                        output_file.write(final_data)
                    
                    print(f"File successfully extracted to: {output_path}")
                    print(f"Original filename: {filename}")
                    print(f"Data length: {len(final_data)} bytes")
                    return True
                        
                except Exception as e:
                    print(f"Error with {'randomized' if randomize else 'sequential'} method: {str(e)}")
                    continue  # Try the other positioning method
            
            print("No steganographic data found or incorrect seed.")
            return False
            
        except Exception as e:
            print(f"Error extracting file: {str(e)}")
            return False

def main():
    stego = MP3Steganography()
    
    while True:
        print("\n=== MP3 Steganography Tool ===")
        print("1. Embed file into MP3")
        print("2. Extract file from MP3")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            print("\n--- Embed File ---")
            mp3_file = input("Enter MP3 file path: ").strip()
            hidden_file = input("Enter file to hide: ").strip()
            
            if not os.path.exists(mp3_file):
                print("MP3 file not found!")
                continue
            if not os.path.exists(hidden_file):
                print("Hidden file not found!")
                continue
            
            encrypt = input("Encrypt the hidden file? (y/n): ").strip().lower() == 'y'
            randomize = input("Randomize starting bit positions? (y/n): ").strip().lower() == 'y'
            
            # LSB count selection
            print("\nSelect LSB count (bits to modify per byte):")
            print("1 = 1 bit (most secure, least capacity)")
            print("2 = 2 bits (balanced)")
            print("3 = 3 bits (higher capacity)")
            print("4 = 4 bits (highest capacity, less secure)")
            
            while True:
                try:
                    lsb_count = int(input("Enter LSB count (1-4): ").strip())
                    if 1 <= lsb_count <= 4:
                        break
                    else:
                        print("Please enter a number between 1 and 4.")
                except ValueError:
                    print("Please enter a valid number.")
            
            seed = input("Enter seed string: ").strip()
            
            if not seed:
                print("Seed cannot be empty!")
                continue
            
            output_file = input("Enter output MP3 file path: ").strip()
            if not output_file:
                output_file = f"stego_{os.path.basename(mp3_file)}"
            
            success = stego.embed_file(mp3_file, hidden_file, output_file, encrypt, randomize, seed, lsb_count)
            if success:
                print(f"Steganographic MP3 saved as: {output_file}")
                print(f"Used {lsb_count}-LSB embedding for {'higher capacity' if lsb_count > 2 else 'balance of security and capacity'}")
        
        elif choice == '2':
            print("\n--- Extract File ---")
            stego_mp3 = input("Enter steganographic MP3 file path: ").strip()
            seed = input("Enter seed string: ").strip()
            
            if not os.path.exists(stego_mp3):
                print("MP3 file not found!")
                continue
            
            if not seed:
                print("Seed cannot be empty!")
                continue
            
            # LSB count selection for extraction
            print("\nSelect LSB count used during embedding:")
            print("1 = 1 bit (default)")
            print("2 = 2 bits")
            print("3 = 3 bits")
            print("4 = 4 bits")
            
            while True:
                try:
                    lsb_count = int(input("Enter LSB count (1-4): ").strip())
                    if 1 <= lsb_count <= 4:
                        break
                    else:
                        print("Please enter a number between 1 and 4.")
                except ValueError:
                    print("Please enter a valid number.")
            
            output_dir = input("Enter output directory (press Enter for current directory): ").strip()
            if not output_dir:
                output_dir = "."
            
            stego.extract_file(stego_mp3, seed, output_dir, lsb_count)
        
        elif choice == '3':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice! Please try again.")

if __name__ == "__main__":
    main()