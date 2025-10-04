import os
import random
import hashlib
from typing import List, Tuple

class VigenereCipher:
    @staticmethod
    def encrypt(plaintext: str, key: str) -> str:
        key = key.upper()
        encrypted = ""
        key_index = 0
        
        for char in plaintext:
            if char.isalpha():
                shift = ord(key[key_index % len(key)]) - ord('A')
                if char.isupper():
                    encrypted_char = chr((ord(char) - ord('A') + shift) % 26 + ord('A'))
                else:
                    encrypted_char = chr((ord(char.upper()) - ord('A') + shift) % 26 + ord('A')).lower()
                encrypted += encrypted_char
                key_index += 1
            else:
                encrypted += char
        
        return encrypted
    
    @staticmethod
    def decrypt(ciphertext: str, key: str) -> str:
        """Decrypt text using Vigenere cipher - preserves case and non-alphabetic chars"""
        key = key.upper()
        decrypted = ""
        key_index = 0
        
        for char in ciphertext:
            if char.isalpha():
                shift = ord(key[key_index % len(key)]) - ord('A')
                if char.isupper():
                    decrypted_char = chr((ord(char) - ord('A') - shift + 26) % 26 + ord('A'))
                else:
                    decrypted_char = chr((ord(char.upper()) - ord('A') - shift + 26) % 26 + ord('A')).lower()
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
    
    def _create_flag_bits(self, randomize: bool, encrypt: bool, lsb_count: int) -> List[int]:
        """Create 4-bit flag: [random_bit, encrypt_bit, lsb_bit1, lsb_bit0]"""
        random_bit = 1 if randomize else 0
        encrypt_bit = 1 if encrypt else 0
        
        # Convert lsb_count (1-4) to 2 bits (00-11)
        lsb_bits = lsb_count - 1  # Convert 1-4 to 0-3
        lsb_bit1 = (lsb_bits >> 1) & 1
        lsb_bit0 = lsb_bits & 1
        
        return [random_bit, encrypt_bit, lsb_bit1, lsb_bit0]
    
    def _parse_flag_bits(self, flag_bits: List[int]) -> Tuple[bool, bool, int]:
        """Parse 4-bit flag to get randomize, encrypt, and lsb_count"""
        if len(flag_bits) < 4:
            return False, False, 1
        
        randomize = flag_bits[0] == 1
        encrypt = flag_bits[1] == 1
        
        # Convert 2 LSB bits back to count (0-3 becomes 1-4)
        lsb_value = (flag_bits[2] << 1) | flag_bits[3]
        lsb_count = lsb_value + 1
        
        return randomize, encrypt, lsb_count
    
    def _generate_safe_positions(self, mp3_data: bytes) -> List[int]:
        """Generate safe positions for data embedding"""
        safe_positions = []
        
        # Skip ID3v2 header if present
        start_pos = 0
        if len(mp3_data) >= 10 and mp3_data[:3] == b'ID3':
            size = int.from_bytes(mp3_data[6:10], 'big')
            # ID3v2 size is synchsafe integer
            size = ((size & 0x7f000000) >> 3) | ((size & 0x7f0000) >> 2) | ((size & 0x7f00) >> 1) | (size & 0x7f)
            start_pos = 10 + size
        
        # Start from a safe position (skip at least 4KB)
        safe_start = max(start_pos + 4096, 4096)
        
        # Generate positions every 8 bytes, skipping 0xFF bytes
        pos = safe_start
        while pos < len(mp3_data):
            if mp3_data[pos] != 0xFF:
                safe_positions.append(pos)
            pos += 8
        
        return safe_positions
    
    def _generate_positions(self, seed: str, mp3_data: bytes, positions_needed: int, randomize: bool) -> List[int]:
        """Generate positions for embedding/extracting data"""
        safe_positions = self._generate_safe_positions(mp3_data)
        
        if len(safe_positions) < positions_needed:
            print(f"Warning: Only {len(safe_positions)} safe positions available, need {positions_needed}")
            # Use all available positions
            return safe_positions[:positions_needed] if positions_needed <= len(safe_positions) else safe_positions
        
        if randomize:
            # Use random sampling but with consistent seed
            # Important: To ensure reproducible results, we always generate the same 
            # random sequence and then take the first positions_needed items
            random.seed(seed)
            
            # Shuffle a copy of all safe positions to get consistent random order
            shuffled_positions = safe_positions.copy()
            random.shuffle(shuffled_positions)
            
            # Return the first positions_needed from the shuffled list
            return shuffled_positions[:positions_needed]
        else:
            # Use sequential positions starting from a FIXED seed-based offset
            # This ensures the same starting point regardless of positions_needed
            hash_obj = hashlib.md5(seed.encode())
            start_index = int(hash_obj.hexdigest()[:8], 16) % 1000  # Fixed small range
            return safe_positions[start_index:start_index + positions_needed]
    
    def _generate_flag_positions(self, seed: str, mp3_data: bytes) -> List[int]:
        """Generate fixed positions for the 4-bit flag"""
        # Use a different hash for flag positions to avoid conflict with data positions
        hash_obj = hashlib.md5((seed + "_FLAG").encode())
        start_offset = int(hash_obj.hexdigest()[:4], 16) % 1024 + 2048  # 2KB-3KB range
        
        flag_positions = []
        pos = start_offset
        count = 0
        while count < 4 and pos < len(mp3_data):
            if mp3_data[pos] != 0xFF:  # Skip frame sync bytes
                flag_positions.append(pos)
                count += 1
            pos += 1
        
        return flag_positions
    
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
            
            # Create metadata: filename length + filename + data length
            filename_bytes = filename.encode('utf-8')
            metadata = len(filename_bytes).to_bytes(2, 'big') + filename_bytes + len(payload).to_bytes(4, 'big')
            
            # Complete payload: magic header + metadata + actual data + end marker
            complete_payload = self.magic_header + metadata + payload + self.end_marker
            
            print(f"Complete payload size: {len(complete_payload)} bytes")
            
            # === EMBED 4-BIT FLAG FIRST ===
            flag_bits = self._create_flag_bits(randomize, encrypt, lsb_count)
            flag_positions = self._generate_flag_positions(seed, mp3_data)
            
            if len(flag_positions) < 4:
                print("Error: Cannot find enough positions for flag bits")
                return False
            
            # Embed flag bits (always use 1-LSB for flags)
            for i, bit in enumerate(flag_bits):
                pos = flag_positions[i]
                mp3_data[pos] = self._embed_bit(mp3_data[pos], bit)
            
            print(f"Flag embedded: randomize={randomize}, encrypt={encrypt}, lsb_count={lsb_count}")
            print(f"Flag bits: {flag_bits}")
            print(f"Flag positions: {flag_positions}")
            
            # === EMBED MAIN PAYLOAD ===
            # Calculate positions needed for payload
            if lsb_count == 1:
                positions_needed = len(complete_payload) * 8  # 8 positions per byte for 1-LSB
            else:
                total_bits = len(complete_payload) * 8
                positions_needed = (total_bits + lsb_count - 1) // lsb_count  # Ceiling division
            
            print(f"Positions needed for payload: {positions_needed}")
            
            # Generate positions for payload data
            positions = self._generate_positions(seed, mp3_data, positions_needed, randomize)
            
            # Remove flag positions from available positions to avoid conflicts
            positions = [pos for pos in positions if pos not in flag_positions]
            
            print(f"Available positions after flag exclusion: {len(positions)}")
            
            # Check if we have enough positions
            if len(positions) < positions_needed:
                print(f"Error: Not enough positions. Need {positions_needed}, have {len(positions)}")
                return False
            
            # Embed the payload
            if lsb_count == 1:
                # Traditional single-bit embedding
                bit_index = 0
                for byte_val in complete_payload:
                    for bit_pos in range(8):
                        if bit_index < len(positions):
                            bit = (byte_val >> (7 - bit_pos)) & 1
                            pos = positions[bit_index]
                            mp3_data[pos] = self._embed_bit(mp3_data[pos], bit)
                            bit_index += 1
            else:
                # Multi-LSB embedding
                all_bits = []
                for byte_val in complete_payload:
                    for bit_pos in range(8):
                        all_bits.append((byte_val >> (7 - bit_pos)) & 1)
                
                bit_index = 0
                pos_index = 0
                while bit_index < len(all_bits) and pos_index < len(positions):
                    # Collect bits for this position
                    bits_to_embed = 0
                    actual_bits = min(lsb_count, len(all_bits) - bit_index)
                    
                    for i in range(actual_bits):
                        bit = all_bits[bit_index + i]
                        bits_to_embed |= (bit << (actual_bits - 1 - i))
                    
                    # Embed the bits
                    pos = positions[pos_index]
                    mp3_data[pos] = self._embed_bits(mp3_data[pos], bits_to_embed, actual_bits)
                    
                    bit_index += actual_bits
                    pos_index += 1
            
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
            import traceback
            traceback.print_exc()
            return False
    
    def extract_file(self, stego_mp3_path: str, seed: str, output_dir: str = ".") -> bool:
        """Extract a hidden file from an MP3 file using flag-based detection"""
        try:
            # Read the steganographic MP3
            with open(stego_mp3_path, 'rb') as mp3_file:
                mp3_data = mp3_file.read()
            
            print("Extracting flag bits...")
            
            # === EXTRACT 4-BIT FLAG FIRST ===
            flag_positions = self._generate_flag_positions(seed, mp3_data)
            
            if len(flag_positions) < 4:
                print("Error: Cannot find flag positions")
                return False
            
            print(f"Flag positions: {flag_positions}")
            
            # Extract flag bits
            flag_bits = []
            for pos in flag_positions:
                if pos < len(mp3_data):
                    bit = self._extract_bit(mp3_data[pos])
                    flag_bits.append(bit)
                else:
                    print("Error: Flag position out of range")
                    return False
            
            # Parse flag bits to get parameters
            randomize, encrypt, lsb_count = self._parse_flag_bits(flag_bits)
            
            print(f"Flag extracted: randomize={randomize}, encrypt={encrypt}, lsb_count={lsb_count}")
            print(f"Flag bits: {flag_bits}")
            
            # === EXTRACT MAIN PAYLOAD ===
            # Generate positions using a large number to ensure we get the same sequence as embedding
            # The key insight: we need to use the same start_index regardless of how many positions we need
            max_possible_positions = 10000  # Large enough for any reasonable payload
            all_positions = self._generate_positions(seed, mp3_data, max_possible_positions, randomize)
            
            # Remove flag positions from extraction positions
            all_positions = [pos for pos in all_positions if pos not in flag_positions]
            
            print(f"Generated {len(all_positions)} positions for extraction")
            
            if not all_positions:
                print("Error: No valid positions for extraction")
                return False
            
            # Extract data based on LSB count
            if lsb_count == 1:
                # Traditional single-bit extraction
                # Extract a reasonable amount of data to find magic header and payload
                extracted_bits = []
                for i, pos in enumerate(all_positions):
                    if i >= 5000:  # Limit to first 5000 positions to avoid extracting too much
                        break
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
                
                for i, pos in enumerate(all_positions):
                    if i >= 2500:  # Limit positions for multi-LSB
                        break
                    if pos < len(mp3_data):
                        # Extract multiple bits from this position
                        bits = self._extract_bits(mp3_data[pos], lsb_count)
                        
                        # Convert bits back to individual bit array
                        for j in range(lsb_count):
                            bit = (bits >> (lsb_count - 1 - j)) & 1
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
            print(f"Extracted {len(extracted_data)} bytes of data")
            
            # Look for magic header
            magic_pos = extracted_data.find(self.magic_header)
            
            if magic_pos == -1:
                print("Error: Magic header not found.")
                print(f"First 100 bytes of extracted data: {extracted_data[:100]}")
                print(f"Looking for magic header: {self.magic_header}")
                return False
            
            print(f"Magic header found at position {magic_pos}!")
            
            # Start parsing from after magic header
            data_start = magic_pos + len(self.magic_header)
            
            if data_start + 6 > len(extracted_data):  # Need at least 6 bytes for metadata
                print("Error: Not enough data after magic header")
                return False
            
            # Extract filename length (2 bytes)
            filename_len = int.from_bytes(extracted_data[data_start:data_start+2], 'big')
            data_start += 2
            
            if data_start + filename_len + 4 > len(extracted_data):
                print("Error: Invalid filename length")
                return False
            
            # Extract filename
            filename = extracted_data[data_start:data_start+filename_len].decode('utf-8')
            data_start += filename_len
            
            # Extract data length (4 bytes)
            data_len = int.from_bytes(extracted_data[data_start:data_start+4], 'big')
            data_start += 4
            
            if data_start + data_len > len(extracted_data):
                print("Error: Invalid data length or insufficient extracted data")
                print(f"Need {data_len} bytes but only {len(extracted_data) - data_start} available")
                return False
            
            # Extract the actual data
            file_data = extracted_data[data_start:data_start+data_len]
            
            # Use the flag to determine if decryption is needed
            final_data = file_data
            
            if encrypt:
                try:
                    # Decrypt the data
                    import base64
                    decrypted_text = VigenereCipher.decrypt(file_data.decode('ascii'), seed)
                    final_data = base64.b64decode(decrypted_text.encode('ascii'))
                    print("Data was encrypted and has been decrypted.")
                except Exception as e:
                    print(f"Decryption failed: {e}")
                    return False
            else:
                print("Data was not encrypted.")
            
            # Save the extracted file
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'wb') as output_file:
                output_file.write(final_data)
            
            print(f"File successfully extracted to: {output_path}")
            print(f"Original filename: {filename}")
            print(f"Data length: {len(final_data)} bytes")
            print(f"Extraction used: {lsb_count}-LSB, randomize={randomize}, encrypt={encrypt}")
            return True
            
        except Exception as e:
            print(f"Error extracting file: {str(e)}")
            import traceback
            traceback.print_exc()
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
                print(f"Settings embedded in flag: randomize={randomize}, encrypt={encrypt}, lsb_count={lsb_count}")
        
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
            
            output_dir = input("Enter output directory (press Enter for current directory): ").strip()
            if not output_dir:
                output_dir = "."
            
            print("Note: Extraction parameters will be automatically detected from embedded flag.")
            stego.extract_file(stego_mp3, seed, output_dir)
        
        elif choice == '3':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice! Please try again.")

if __name__ == "__main__":
    main()