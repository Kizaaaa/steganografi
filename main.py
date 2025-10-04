import os
import random
import hashlib
import struct
import json
import traceback
from typing import List, Dict, Tuple, Optional
from psnr import psnr

class VigenereCipher:
    @staticmethod
    def _to_bytes(x):
        if isinstance(x, bytes):
            return x
        if isinstance(x, str):
            return x.encode('utf-8')

    @staticmethod
    def encrypt(data, key):
        data_b = VigenereCipher._to_bytes(data)
        key_b = VigenereCipher._to_bytes(key)
        if len(key_b) == 0:
            return

        out = bytearray(len(data_b))
        for i, b in enumerate(data_b):
            shift = key_b[i % len(key_b)]
            out[i] = (b + shift) & 0xFF
        return bytes(out)

    @staticmethod
    def decrypt(data, key):
        data_b = VigenereCipher._to_bytes(data)
        key_b = VigenereCipher._to_bytes(key)
        if len(key_b) == 0:
            return

        out = bytearray(len(data_b))
        for i, b in enumerate(data_b):
            shift = key_b[i % len(key_b)]
            out[i] = (b - shift) & 0xFF
        return bytes(out)   

class MP3Steganography:
    def __init__(self):
        self.FRAME_SYNC = 0xFFE0
        self.MAGIC_HEADER = b'MP3STEGO'  # Magic bytes untuk identifikasi
        self.VERSION = 1
    
    def _generate_seed_hash(self, seed: str) -> int:
        return int(hashlib.sha256(seed.encode()).hexdigest(), 16) % (2**32)
    
    def _is_valid_header(self, header: int) -> bool:
        if (header >> 21) != 0x7FF:
            return False
        
        version_bits = (header >> 19) & 0x03
        layer_bits = (header >> 17) & 0x03
        bitrate_index = (header >> 12) & 0x0F
        samplerate_index = (header >> 10) & 0x03
        
        if version_bits == 1:  # Reserved
            return False
        if layer_bits == 0:  # Reserved
            return False
        if bitrate_index == 15:  # Bad bitrate
            return False
        if samplerate_index == 3:  # Reserved
            return False
        
        return True
    
    def _get_frame_length(self, header: int) -> int:
        # Bitrate tables
        bitrate_table_v1_l3 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
        bitrate_table_v2_l3 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]
        
        samplerate_table_v1 = [44100, 48000, 32000, 0]
        samplerate_table_v2 = [22050, 24000, 16000, 0]
        samplerate_table_v25 = [11025, 12000, 8000, 0]
        
        # Parse header bits
        version_bits = (header >> 19) & 0x03
        layer_bits = (header >> 17) & 0x03
        bitrate_index = (header >> 12) & 0x0F
        samplerate_index = (header >> 10) & 0x03
        padding = (header >> 9) & 0x01
        
        # Validate
        if bitrate_index == 0 or bitrate_index == 15:
            return 0
        if samplerate_index == 3:
            return 0
        
        # Determine version
        if version_bits == 3:  # MPEG Version 1
            version = 1
            samplerate_table = samplerate_table_v1
            bitrate_table = bitrate_table_v1_l3
        elif version_bits == 2:  # MPEG Version 2
            version = 2
            samplerate_table = samplerate_table_v2
            bitrate_table = bitrate_table_v2_l3
        elif version_bits == 0:  # MPEG Version 2.5
            version = 25
            samplerate_table = samplerate_table_v25
            bitrate_table = bitrate_table_v2_l3
        else:
            return 0
        
        # Determine layer
        if layer_bits == 1:  # Layer III
            layer = 3
        elif layer_bits == 2:  # Layer II
            layer = 2
        elif layer_bits == 3:  # Layer I
            layer = 1
        else:
            return 0
        
        # Get bitrate and samplerate
        bitrate = bitrate_table[bitrate_index] * 1000
        samplerate = samplerate_table[samplerate_index]
        
        if samplerate == 0:
            return 0
        
        # Calculate frame length based on layer
        if layer == 3:  # Layer III (MP3)
            if version == 1:  # MPEG1
                frame_length = int(144 * bitrate / samplerate) + padding
            else:  # MPEG2, MPEG2.5
                frame_length = int(72 * bitrate / samplerate) + padding
        elif layer == 2:  # Layer II
            frame_length = int(144 * bitrate / samplerate) + padding
        elif layer == 1:  # Layer I
            frame_length = int((12 * bitrate / samplerate) + padding) * 4
        else:
            return 0
        
        # Sanity check: frame length should be reasonable
        if frame_length < 24 or frame_length > 2881:  # Min/max valid MP3 frame sizes
            return 0
        
        return frame_length
    
    def _skip_id3_tags(self, data: bytes) -> int:
        if len(data) < 10:
            return 0
        
        # Check ID3v2 tag
        if data[0:3] == b'ID3':
            # ID3v2 size is in bytes 6-9 (synchsafe integer)
            size = ((data[6] & 0x7F) << 21) | \
                   ((data[7] & 0x7F) << 14) | \
                   ((data[8] & 0x7F) << 7) | \
                   (data[9] & 0x7F)
            
            return size + 10  # Header is 10 bytes
        
        return 0
    
    def _find_frames(self, data: bytes) -> List[Dict]:
        frames = []
        i = 0
        consecutive_failures = 0
        max_failures = 10  # Stop jika terlalu banyak kegagalan berturut-turut
        
        print(f" Scanning {len(data):,} bytes untuk frame MP3...")
        
        while i < len(data) - 4:
            # Cek sync word
            if data[i] == 0xFF and (data[i+1] & 0xE0) == 0xE0:
                # Possible frame header
                try:
                    header = struct.unpack('>I', data[i:i+4])[0]
                    
                    # Validasi header
                    if not self._is_valid_header(header):
                        i += 1
                        continue
                    
                    frame_length = self._get_frame_length(header)
                    
                    # Validasi frame length
                    if frame_length > 0 and i + frame_length <= len(data):
                        # ADDITIONAL CHECK: Cek apakah frame berikutnya juga valid
                        next_frame_pos = i + frame_length
                        
                        if next_frame_pos + 4 <= len(data):
                            # Check next frame sync
                            if data[next_frame_pos] == 0xFF and (data[next_frame_pos+1] & 0xE0) == 0xE0:
                                next_header = struct.unpack('>I', data[next_frame_pos:next_frame_pos+4])[0]
                                
                                if self._is_valid_header(next_header):
                                    # Frame ini kemungkinan valid!
                                    frames.append({
                                        'offset': i,
                                        'header_size': 4,
                                        'frame_length': frame_length
                                    })
                                    consecutive_failures = 0
                                    i += frame_length
                                    continue
                        else:
                            # Frame terakhir - terima saja jika valid
                            frames.append({
                                'offset': i,
                                'header_size': 4,
                                'frame_length': frame_length
                            })
                            consecutive_failures = 0
                            i += frame_length
                            continue
                    
                    consecutive_failures += 1
                    
                except struct.error:
                    pass
            
            consecutive_failures += 1
            i += 1
            
            # Jika terlalu banyak failure, skip beberapa byte
            if consecutive_failures > max_failures:
                consecutive_failures = 0
        
        return frames

    def _find_frames_robust(self, data: bytes) -> List[Dict]:
        frames = []
        
        # Skip ID3 tags
        offset = self._skip_id3_tags(data)
        
        if offset > 0:
            print(f" ID3v2 tag terdeteksi, skip {offset} bytes")
        
        i = offset
        frame_count = 0
        
        while i < len(data) - 4:
            # Check sync word
            if data[i] == 0xFF and (data[i+1] & 0xE0) == 0xE0:
                try:
                    header = struct.unpack('>I', data[i:i+4])[0]
                    
                    if not self._is_valid_header(header):
                        i += 1
                        continue
                    
                    frame_length = self._get_frame_length(header)
                    
                    if frame_length > 0 and i + frame_length <= len(data):
                        # Verify next frame exists
                        next_pos = i + frame_length
                        
                        # Last frame OR next frame is valid
                        if next_pos >= len(data) - 4 or \
                           (data[next_pos] == 0xFF and (data[next_pos+1] & 0xE0) == 0xE0):
                            
                            frames.append({
                                'offset': i,
                                'header_size': 4,
                                'frame_length': frame_length
                            })
                            
                            frame_count += 1
                            i += frame_length
                            
                            # Progress indicator
                            if frame_count % 1000 == 0:
                                progress = (i / len(data)) * 100
                                print(f"    Progress: {progress:.1f}% ({frame_count} frames)", end='\r')
                            
                            continue
                
                except (struct.error, ZeroDivisionError):
                    pass
            
            i += 1
        
        print(f"\n Scanning selesai")
        
        return frames
    
    def _calculate_capacity(self, frames: List[Dict], lsb_count: int) -> int:
        """Hitung kapasitas penyimpanan dalam bytes"""
        total_bits = 0
        for frame in frames:
            audio_data_size = frame['frame_length'] - frame['header_size']
            total_bits += audio_data_size * lsb_count
        
        return total_bits // 8
    
    def _generate_random_positions(self, total_positions: int, required_positions: int, 
                                   seed: str) -> List[int]:
        """Generate posisi random untuk embedding"""
        rng = random.Random(self._generate_seed_hash(seed))
        
        if required_positions > total_positions:
            raise ValueError("Data terlalu besar untuk kapasitas yang tersedia")
        
        # Generate shuffled positions
        positions = list(range(total_positions))
        rng.shuffle(positions)
        
        return positions[:required_positions]
    
    def _create_metadata(self, filename: str, filesize: int, encrypted: bool, 
                        randomized: bool, lsb_count: int) -> bytes:
        """Buat metadata untuk file tersembunyi"""
        metadata = {
            'version': self.VERSION,
            'filename': filename,
            'filesize': filesize,
            'encrypted': encrypted,
            'randomized': randomized,
            'lsb_count': lsb_count,
            'checksum': '' # diisi nanti ae lah
        }
        
        metadata_json = json.dumps(metadata, separators=(',', ':'))
        metadata_bytes = metadata_json.encode('utf-8')
        
        # Format: MAGIC_HEADER (8 bytes) + metadata_length (4 bytes) + metadata
        header = self.MAGIC_HEADER
        header += struct.pack('>I', len(metadata_bytes))
        header += metadata_bytes
        
        return header
    
    def _parse_metadata(self, data: bytes) -> Tuple[Dict, int]:
        """Parse metadata dari data tersembunyi"""
        if not data.startswith(self.MAGIC_HEADER):
            raise ValueError("Format data tidak valid - magic header tidak ditemukan")
        
        offset = len(self.MAGIC_HEADER)
        metadata_length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        
        metadata_bytes = data[offset:offset+metadata_length]
        metadata = json.loads(metadata_bytes.decode('utf-8'))
        
        return metadata, offset + metadata_length
    
    def _embed_bits(self, mp3_data: bytearray, frames: List[Dict], data_bits: str,
                   lsb_count: int, randomize: bool, seed: str) -> int:
        """Embed bits ke LSB audio data"""
        total_positions = 0
        position_map = []  # (frame_idx, byte_offset_in_frame)
        
        for frame_idx, frame in enumerate(frames):
            audio_start = frame['offset'] + frame['header_size']
            audio_end = frame['offset'] + frame['frame_length']
            
            for byte_pos in range(audio_start, audio_end):
                position_map.append((frame_idx, byte_pos))
                total_positions += 1
        
        # Hitung berapa posisi yang dibutuhkan
        bits_needed = len(data_bits)
        positions_needed = (bits_needed + lsb_count - 1) // lsb_count
        
        if randomize:
            # Generate random positions
            random_indices = self._generate_random_positions(
                total_positions, positions_needed, seed
            )
            selected_positions = [position_map[i] for i in random_indices]
        else:
            # Sequential positions
            selected_positions = position_map[:positions_needed]
        
        # Embed bits
        bit_index = 0
        embedded_bits = 0
        
        for frame_idx, byte_pos in selected_positions:
            if bit_index >= len(data_bits):
                break
            
            # Ambil lsb_count bits
            bits_to_embed = data_bits[bit_index:bit_index + lsb_count]
            
            # Pad jika kurang dari lsb_count
            if len(bits_to_embed) < lsb_count:
                bits_to_embed = bits_to_embed.ljust(lsb_count, '0')
            
            # Clear LSBs
            mask = (0xFF << lsb_count) & 0xFF
            mp3_data[byte_pos] = (mp3_data[byte_pos] & mask)
            
            # Set new LSBs
            new_lsb = int(bits_to_embed, 2)
            mp3_data[byte_pos] = mp3_data[byte_pos] | new_lsb
            
            bit_index += lsb_count
            embedded_bits += lsb_count
        
        return embedded_bits
    
    def _extract_bits(self, mp3_data: bytes, frames: List[Dict], num_bits: int,
                     lsb_count: int, randomize: bool, seed: str) -> str:
        """Extract bits dari LSB audio data"""
        # Build position map
        position_map = []
        
        for frame_idx, frame in enumerate(frames):
            audio_start = frame['offset'] + frame['header_size']
            audio_end = frame['offset'] + frame['frame_length']
            
            for byte_pos in range(audio_start, audio_end):
                position_map.append((frame_idx, byte_pos))
        
        total_positions = len(position_map)
        positions_needed = (num_bits + lsb_count - 1) // lsb_count
        
        if randomize:
            random_indices = self._generate_random_positions(
                total_positions, positions_needed, seed
            )
            selected_positions = [position_map[i] for i in random_indices]
        else:
            selected_positions = position_map[:positions_needed]
        
        # Extract bits
        extracted_bits = []
        
        for frame_idx, byte_pos in selected_positions:
            if len(extracted_bits) >= num_bits:
                break
            
            # Extract lsb_count bits
            mask = (1 << lsb_count) - 1
            lsb_value = mp3_data[byte_pos] & mask
            
            bits = format(lsb_value, f'0{lsb_count}b')
            extracted_bits.append(bits)
        
        result = ''.join(extracted_bits)
        return result[:num_bits]  # Trim to exact size
    
    def _embed_bits_with_offset(self, mp3_data: bytearray, frames: List[Dict], 
                                data_bits: str, lsb_count: int, randomize: bool, 
                                seed: str, offset_bits: int) -> int:
        """
        Embed bits dengan offset (skip posisi yang sudah digunakan)
        
        Args:
            offset_bits: Jumlah bits yang sudah digunakan sebelumnya
        """
        # Build position map (sama seperti _embed_bits)
        position_map = []
        
        for frame_idx, frame in enumerate(frames):
            audio_start = frame['offset'] + frame['header_size']
            audio_end = frame['offset'] + frame['frame_length']
            
            for byte_pos in range(audio_start, audio_end):
                position_map.append((frame_idx, byte_pos))
        
        total_positions = len(position_map)
        
        # Skip posisi yang sudah digunakan oleh offset_bits
        # offset_bits menggunakan LSB-1, jadi 1 bit per posisi
        start_position = offset_bits  # Skip posisi yang sudah digunakan
        
        # Hitung berapa posisi yang dibutuhkan untuk data_bits dengan lsb_count
        bits_needed = len(data_bits)
        positions_needed = (bits_needed + lsb_count - 1) // lsb_count
        
        if randomize:
            # Generate random positions, tapi skip yang sudah digunakan
            available_positions = list(range(start_position, total_positions))
            
            if positions_needed > len(available_positions):
                raise ValueError("Tidak cukup posisi tersisa untuk data!")
            
            rng = random.Random(self._generate_seed_hash(seed))
            rng.shuffle(available_positions)
            
            random_indices = available_positions[:positions_needed]
            selected_positions = [position_map[i] for i in random_indices]
        else:
            # Sequential, mulai dari start_position
            end_position = start_position + positions_needed
            
            if end_position > total_positions:
                raise ValueError("Tidak cukup posisi tersisa untuk data!")
            
            selected_positions = position_map[start_position:end_position]
        
        # Embed bits (sama seperti _embed_bits)
        bit_index = 0
        embedded_bits = 0
        
        for frame_idx, byte_pos in selected_positions:
            if bit_index >= len(data_bits):
                break
            
            bits_to_embed = data_bits[bit_index:bit_index + lsb_count]
            
            if len(bits_to_embed) < lsb_count:
                bits_to_embed = bits_to_embed.ljust(lsb_count, '0')
            
            # Clear LSBs
            mask = (0xFF << lsb_count) & 0xFF
            mp3_data[byte_pos] = (mp3_data[byte_pos] & mask)
            
            # Set new LSBs
            new_lsb = int(bits_to_embed, 2)
            mp3_data[byte_pos] = mp3_data[byte_pos] | new_lsb
            
            bit_index += lsb_count
            embedded_bits += lsb_count
        
        return embedded_bits
    
    def _extract_bits_with_offset(self, mp3_data: bytes, frames: List[Dict], 
                                num_bits: int, lsb_count: int, randomize: bool, 
                                seed: str, offset_bits: int) -> str:
        """
        Extract bits dengan offset (skip posisi yang sudah digunakan)
        
        Args:
            offset_bits: Jumlah bits yang sudah digunakan sebelumnya (untuk metadata)
        """
        # Build position map
        position_map = []
        
        for frame_idx, frame in enumerate(frames):
            audio_start = frame['offset'] + frame['header_size']
            audio_end = frame['offset'] + frame['frame_length']
            
            for byte_pos in range(audio_start, audio_end):
                position_map.append((frame_idx, byte_pos))
        
        total_positions = len(position_map)
        
        # Skip posisi yang sudah digunakan oleh metadata (offset_bits)
        start_position = offset_bits
        
        # Hitung berapa posisi yang dibutuhkan
        positions_needed = (num_bits + lsb_count - 1) // lsb_count
        
        if randomize:
            # Generate random positions dari available range
            available_positions = list(range(start_position, total_positions))
            
            if positions_needed > len(available_positions):
                raise ValueError(
                    f"Tidak cukup posisi! Butuh {positions_needed}, "
                    f"tersedia {len(available_positions)}"
                )
            
            rng = random.Random(self._generate_seed_hash(seed))
            rng.shuffle(available_positions)
            
            random_indices = available_positions[:positions_needed]
            selected_positions = [position_map[i] for i in random_indices]
        else:
            # Sequential dari start_position
            end_position = start_position + positions_needed
            
            if end_position > total_positions:
                raise ValueError(
                    f"Tidak cukup posisi! Butuh sampai {end_position}, "
                    f"total {total_positions}"
                )
            
            selected_positions = position_map[start_position:end_position]
        
        # Extract bits
        extracted_bits = []
        
        for frame_idx, byte_pos in selected_positions:
            if len(extracted_bits) * lsb_count >= num_bits:
                break
            
            # Extract lsb_count bits
            mask = (1 << lsb_count) - 1
            lsb_value = mp3_data[byte_pos] & mask
            
            bits = format(lsb_value, f'0{lsb_count}b')
            extracted_bits.append(bits)
        
        result = ''.join(extracted_bits)
        return result[:num_bits]  # Trim to exact size
    
    def embed_file(self, mp3_path: str, hidden_file_path: str, output_path: str,
                encrypt: bool, randomize: bool, seed: str, lsb_count: int = 1) -> bool:
        """Embed file ke dalam MP3"""
        print("="*60)
        print("MP3 LSB STEGANOGRAPHY - EMBED MODE")
        print("="*60)
        
        # Baca file MP3
        print(f"\n Membaca carrier MP3: {mp3_path}")
        with open(mp3_path, 'rb') as f:
            mp3_data = bytearray(f.read())
        print(f"     Ukuran: {len(mp3_data):,} bytes")
        
        # Baca file rahasia
        print(f"\n Membaca file rahasia: {hidden_file_path}")
        with open(hidden_file_path, 'rb') as f:
            secret_data = f.read()
        
        filename = os.path.basename(hidden_file_path)
        original_size = len(secret_data)
        print(f"     Nama file: {filename}")
        print(f"     Ukuran original: {original_size:,} bytes")
        
        # Calculate checksum
        checksum = hashlib.sha256(secret_data).hexdigest()
        print(f"     SHA256: {checksum[:16]}...")
        
        # Enkripsi jika diminta
        if encrypt:
            print(f"\n Mengenkripsi data file...")
            secret_data_encrypted = VigenereCipher.encrypt(secret_data, seed)
            print(f"     Data terenkripsi: {len(secret_data_encrypted)} bytes")
            secret_data_to_embed = secret_data_encrypted
        else:
            secret_data_to_embed = secret_data
        
        # Buat metadata
        print(f"\n Membuat metadata...")
        metadata_header = self._create_metadata(
            filename, original_size, encrypt, randomize, lsb_count
        )
        
        checksum_bytes = bytes.fromhex(checksum)
        
        # ===== STRUKTUR DATA =====
        # PART 1: Metadata + Checksum (SELALU LSB-1, Sequential)
        # PART 2: File Data (Gunakan LSB sesuai parameter, randomize sesuai parameter)
        
        part1_metadata = metadata_header + checksum_bytes
        part2_filedata = secret_data_to_embed
        
        print(f"     Part 1 (Metadata+Checksum): {len(part1_metadata)} bytes")
        print(f"      → Akan di-embed dengan: LSB-1, Sequential")
        print(f"     Part 2 (File Data): {len(part2_filedata)} bytes")
        print(f"      → Akan di-embed dengan: LSB-{lsb_count}, {'Random' if randomize else 'Sequential'}")
        
        # Parse MP3 frames
        print(f"\n Menganalisis struktur MP3...")
        frames = self._find_frames_robust(mp3_data)
        print(f"     Ditemukan {len(frames)} frame")
        
        # Hitung kapasitas
        capacity_part1 = self._calculate_capacity(frames, 1)  # LSB-1 untuk metadata
        capacity_part2 = self._calculate_capacity(frames, lsb_count)  # LSB-n untuk data
        
        print(f"\n Kapasitas:")
        print(f"     Part 1 capacity (LSB-1): {capacity_part1:,} bytes")
        print(f"     Part 2 capacity (LSB-{lsb_count}): {capacity_part2:,} bytes")
        
        # Validasi kapasitas
        if len(part1_metadata) > capacity_part1:
            raise ValueError(f"Metadata terlalu besar! {len(part1_metadata)} > {capacity_part1}")
        
        # Hitung sisa kapasitas setelah metadata
        # Part 1 menggunakan beberapa posisi dengan LSB-1
        positions_used_by_part1 = len(part1_metadata) * 8  # bits needed for part1
        
        # Kapasitas tersisa untuk part 2
        total_positions = sum(f['frame_length'] - f['header_size'] for f in frames)
        positions_remaining = total_positions - positions_used_by_part1
        capacity_remaining = (positions_remaining * lsb_count) // 8
        
        print(f"     Posisi digunakan Part 1: {positions_used_by_part1:,} bits")
        print(f"     Kapasitas tersisa Part 2: {capacity_remaining:,} bytes")
        print(f"     Part 2 butuh: {len(part2_filedata):,} bytes")
        
        if len(part2_filedata) > capacity_remaining:
            raise ValueError(
                f"File data terlalu besar! "
                f"Butuh {len(part2_filedata):,} bytes, tersisa {capacity_remaining:,} bytes"
            )
        
        # ===== EMBED PART 1: METADATA + CHECKSUM (LSB-1, Sequential) =====
        print(f"\n Embedding Part 1 (Metadata+Checksum)...")
        part1_bits = ''.join(format(byte, '08b') for byte in part1_metadata)
        
        embedded_bits_part1 = self._embed_bits(
            mp3_data, frames, part1_bits,
            lsb_count=1,        # FIXED: LSB-1
            randomize=False,    # FIXED: Sequential
            seed=seed
        )
        
        positions_used_part1 = embedded_bits_part1 // 1 
        
        print(f"     Part 1 embedded: {embedded_bits_part1:,} bits ({embedded_bits_part1//8} bytes)")
        
        # ===== EMBED PART 2: FILE DATA (LSB-n, Random/Sequential sesuai parameter) =====
        print(f"\n Embedding Part 2 (File Data)...")
        print(f"     LSB count: {lsb_count}")
        print(f"     Randomize: {randomize}")
        
        part2_bits = ''.join(format(byte, '08b') for byte in part2_filedata)
        
        # Embed part 2 SETELAH part 1
        embedded_bits_part2 = self._embed_bits_with_offset(
            mp3_data, frames, part2_bits,
            lsb_count=lsb_count,
            randomize=randomize,
            seed=seed,
            offset_bits=embedded_bits_part1  # Mulai setelah part 1
        )
        
        print(f"     Part 2 embedded: {embedded_bits_part2:,} bits ({embedded_bits_part2//8} bytes)")
        print(f"     Total embedded: {embedded_bits_part1 + embedded_bits_part2:,} bits")
        
        # Simpan file
        print(f"\n Menyimpan file stego: {output_path}")
        with open(output_path, 'wb') as f:
            f.write(mp3_data)
        
        output_size = os.path.getsize(output_path)
        print(f"     Ukuran output: {output_size:,} bytes")
        
        print("\n" + "="*60)
        print("EMBED BERHASIL!")
        print("="*60)
        print(f"File output: {output_path}")
        print(f"Seed: {seed}")
        print(f"Embedding scheme:")
        print(f"    Part 1 (Metadata): LSB-1, Sequential")
        print(f"    Part 2 (Data): LSB-{lsb_count}, {'Random' if randomize else 'Sequential'}")
        print("="*60)
        
        return True
    
    def extract_file(self, stego_mp3_path: str, seed: str, output_dir: str = ".") -> bool:
        """Extract file dari stego MP3"""
        print("="*60)
        print("MP3 LSB STEGANOGRAPHY - EXTRACT MODE")
        print("="*60)
        
        # ... (baca file dan parse frames sama) ...
        
        # ===== EXTRACT PART 1: METADATA (SELALU LSB-1, Sequential) =====
        print(f"\n Mengekstrak Part 1 (Metadata)...")
        
        metadata_max_bits = 2048 * 8
        print(f"\n Membaca stego MP3: {stego_mp3_path}")
        with open(stego_mp3_path, 'rb') as f:
            mp3_data = f.read()  # ← DEFINISI mp3_data
        print(f"     Ukuran: {len(mp3_data):,} bytes")
        print(f"\n Menganalisis struktur MP3...")
        frames = self._find_frames_robust(mp3_data)  # ← DEFINISI frames
        print(f"     Ditemukan {len(frames)} frame")
        
        part1_bits = self._extract_bits(
            mp3_data, frames, metadata_max_bits,
            lsb_count=1,     # FIXED
            randomize=False, # FIXED
            seed=seed
        )
        
        # Convert to bytes
        part1_bytes = bytearray()
        for i in range(0, len(part1_bits), 8):
            byte = int(part1_bits[i:i+8], 2)
            part1_bytes.append(byte)
        
        # Parse metadata
        try:
            metadata, data_start_byte = self._parse_metadata(bytes(part1_bytes))
        except Exception as e:
            print(f"\nERROR: Gagal parsing metadata")
            print(f"    First 32 bytes: {part1_bytes[:32].hex()}")
            print(f"    Expected: {self.MAGIC_HEADER.hex()}")
            raise ValueError(f"Gagal parsing metadata: {e}")
        
        print(f"     Metadata parsed!")
        print(f"     Filename: {metadata['filename']}")
        print(f"     Filesize: {metadata['filesize']:,} bytes")
        print(f"     Encrypted: {metadata['encrypted']}")
        print(f"     Randomized: {metadata['randomized']}")
        print(f"     LSB count: {metadata['lsb_count']}")
        
        # ===== EXTRACT PART 2: FILE DATA (sesuai metadata) =====
        print(f"\n Mengekstrak Part 2 (File Data)...")
        print(f"     LSB count: {metadata['lsb_count']}")
        print(f"     Randomize: {metadata['randomized']}")
        
        checksum_size = 32
        part2_size = checksum_size + metadata['filesize']
        part2_bits_needed = part2_size * 8
        
        # Hitung offset (part 1 menggunakan LSB-1)
        offset_bits = data_start_byte * 8
        
        print(f"     Offset: {offset_bits} bits ({data_start_byte} bytes)")
        print(f"     Part 2 size: {part2_size} bytes")
        
        # Extract part 2
        part2_bits = self._extract_bits_with_offset(
            mp3_data, frames, part2_bits_needed,
            lsb_count=metadata['lsb_count'],
            randomize=metadata['randomized'],
            seed=seed,
            offset_bits=offset_bits
        )
        
        # Convert to bytes
        part2_bytes = bytearray()
        for i in range(0, len(part2_bits), 8):
            if i + 8 <= len(part2_bits):
                byte = int(part2_bits[i:i+8], 2)
                part2_bytes.append(byte)
        
        print(f"     Part 2 extracted: {len(part2_bytes)} bytes")
        
        # Pisahkan checksum dan data
        stored_checksum = part2_bytes[:checksum_size].hex()
        file_data_encrypted = bytes(part2_bytes[checksum_size:checksum_size + metadata['filesize']])
        
        # Decrypt jika perlu
        if metadata['encrypted']:
            print(f"\n Mendekripsi data...")
            file_data = VigenereCipher.decrypt(file_data_encrypted, seed)
            print(f"     Decrypted: {len(file_data)} bytes")
        else:
            file_data = file_data_encrypted
        
        # Verify checksum
        print(f"\n Verifikasi checksum...")
        calculated_checksum = hashlib.sha256(file_data).hexdigest()
        
        print(f"     Stored:     {stored_checksum[:16]}...")
        print(f"     Calculated: {calculated_checksum[:16]}...")
        
        if stored_checksum != calculated_checksum:
            print(f"    WARNING: Checksum tidak cocok!")
            response = input("\n    Lanjutkan simpan file? (y/n): ").strip().lower()
            if response != 'y':
                print("\n Extract dibatalkan")
                return False
        else:
            print(f"     Checksum VALID!")
        
        # Simpan file
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_path = os.path.join(output_dir, metadata['filename'])
        
        # Handle jika file sudah ada
        if os.path.exists(output_path):
            base, ext = os.path.splitext(metadata['filename'])
            counter = 1
            while os.path.exists(output_path):
                output_path = os.path.join(output_dir, f"{base}_{counter}{ext}")
                counter += 1
        
        print(f"\n Menyimpan file: {output_path}")
        with open(output_path, 'wb') as f:
            f.write(file_data)
        
        print(f"     File tersimpan: {len(file_data):,} bytes")
        
        print("\n" + "="*60)
        print("EXTRACT BERHASIL!")
        print("="*60)
        print(f"File: {output_path}")
        print(f"Size: {len(file_data):,} bytes")
        print(f" Checksum: {'VALID' if stored_checksum == calculated_checksum else 'INVALID'}")
        print("="*60)
        
        return True


    
def main():
    print("MP3 LSB STEGANOGRAPHY TOOL")

    stego = MP3Steganography()
    
    print("\nPilih Mode:")
    print("  1. EMBED")
    print("  2. EXTRACT")
    print("  3. Cek PSNR")

    choice = input("\nPilihan (1/2/3): ").strip()

    if choice == '1':
        # ============ MODE EMBED ============
        print("\n" + "="*60)
        print("MODE: EMBED FILE")
        print("="*60)
        
        # Input files
        mp3_path = input("\nPath file MP3 carrier: ").strip()
        hidden_file = input("Path file yang akan disembunyikan: ").strip()
        output_path = input("Path output stego MP3: ").strip()
        
        if not output_path:
            output_path = "stego_output.mp3"
        
        # LSB count
        print("\nLSB Count (jumlah bit per byte):")
        print("   1 = Paling aman, kapasitas kecil")
        print("   2 = Seimbang")
        print("   3 = Kapasitas besar, lebih berisiko")
        print("   4 = Kapasitas maksimal, audio rusak")
        
        lsb_input = input("LSB count (1-4) [default: 1]: ").strip()
        lsb_count = int(lsb_input) if lsb_input else 1
        
        # Encryption
        print("\nEnkripsi:")
        encrypt_input = input("Enkripsi data? (y/n) [default: y]: ").strip().lower()
        encrypt = encrypt_input != 'n'
        
        # Randomization
        print("\nRandomisasi Posisi:")
        print("    Sequential: Embedding berurutan (cepat)")
        print("    Random: Embedding acak (lebih aman)")
        random_input = input("Gunakan posisi random? (y/n) [default: y]: ").strip().lower()
        randomize = random_input != 'n'
        
        # Seed
        print("\nSeed (password untuk enkripsi & randomisasi):")
        seed = input("Masukkan seed: ").strip()
        
        if not seed:
            print("Seed tidak boleh kosong!")
            return
        
        # Konfirmasi
        print("\n" + "="*60)
        print("RINGKASAN:")
        print("="*60)
        print(f"  Carrier MP3    : {mp3_path}")
        print(f"  File rahasia   : {hidden_file}")
        print(f"  Output         : {output_path}")
        print(f"  LSB count      : {lsb_count}")
        print(f"  Enkripsi       : {' Ya' if encrypt else 'Tidak'}")
        print(f"  Randomisasi    : {' Ya' if randomize else 'Tidak'}")
        print(f"  Seed           : {'*' * len(seed)}")
        print("="*60)
        
        confirm = input("\nLanjutkan? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("Dibatalkan")
            return
        
        # Execute embed
        try:
            stego.embed_file(
                mp3_path=mp3_path,
                hidden_file_path=hidden_file,
                output_path=output_path,
                encrypt=encrypt,
                randomize=randomize,
                seed=seed,
                lsb_count=lsb_count
            )
        except Exception as e:
            print(f"\nERROR: {e}")
            traceback.print_exc()
    
    elif choice == '2':
        # ============ MODE EXTRACT ============
        print("\n" + "="*60)
        print("MODE: EXTRACT FILE")
        print("="*60)
        
        stego_path = input("\nPath file stego MP3: ").strip()
        seed = input("Seed yang digunakan saat embed: ").strip()
        
        output_dir = input("Directory output [default: .]: ").strip()
        if not output_dir:
            output_dir = "."
        
        # Konfirmasi
        print("\n" + "="*60)
        print("RINGKASAN:")
        print("="*60)
        print(f"  Stego MP3      : {stego_path}")
        print(f"  Seed           : {'*' * len(seed)}")
        print(f"  Output dir     : {output_dir}")
        print("="*60)
        
        confirm = input("\nLanjutkan? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("Dibatalkan")
            return
        
        # Execute extract
        try:
            stego.extract_file(
                stego_mp3_path=stego_path,
                seed=seed,
                output_dir=output_dir
            )
        except Exception as e:
            print(f"\nERROR: {e}")
            traceback.print_exc()
            
    elif choice == '3':
        path1 = input("\nPath file MP3 pertama: ").strip()
        path2 = input("Path file MP3 kedua: ").strip()
        print("\n====Menghitung PSNR...=====")
        print(f'PSNR VALUE : {psnr(path1, path2)} dB')
    
    else:
        print("Pilihan tidak valid!\nkeluar dari program.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram dihentikan oleh user")
    except Exception as e:
        print(f"\nERROR: {e}")
        traceback.print_exc()