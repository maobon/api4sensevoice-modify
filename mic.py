import pyaudio
import numpy as np
import asyncio
import websockets

class Recorder:
    def __init__(self, input_sample_rate=48000, output_sample_rate=16000, channel_count=1, server_uri="ws://localhost:8765"):
        self.sample_bits = 16
        self.input_sample_rate = input_sample_rate
        self.output_sample_rate = output_sample_rate
        self.channel_count = channel_count
        self.audio_data = {
            'size': 0,
            'buffer': []
        }
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.server_uri = server_uri

    def clear(self):
        """Clears the audio buffer."""
        self.audio_data['buffer'] = []
        self.audio_data['size'] = 0

    def input_data(self, data):
        """Inputs audio data into the buffer."""
        float_array = np.frombuffer(data, dtype=np.float32)
        self.audio_data['buffer'].append(float_array)
        self.audio_data['size'] += len(float_array)

    def encode_pcm(self):
        """Encodes the audio buffer into PCM format."""
        bytes_data = np.concatenate(self.audio_data['buffer']).astype(np.float32)
        data_length = bytes_data.size * (self.sample_bits // 8)
        buffer = np.zeros(data_length, dtype=np.uint8)

        for i, sample in enumerate(bytes_data):
            s = np.clip(sample, -1, 1)
            int_sample = int(s * 32767)  # Convert to int16
            buffer[i * 2] = int_sample & 0xFF  # Lower byte
            buffer[i * 2 + 1] = (int_sample >> 8) & 0xFF  # Upper byte

        return bytes(buffer)

    def downsample_buffer(self, buffer, input_sample_rate, output_sample_rate):
        """Downsamples the buffer to the specified output sample rate."""
        if output_sample_rate == input_sample_rate:
            return buffer

        sample_rate_ratio = input_sample_rate / output_sample_rate
        new_length = int(np.round(len(buffer) / sample_rate_ratio))
        result = np.zeros(new_length, dtype=np.float32)

        offset_result = 0
        offset_buffer = 0
        while offset_result < new_length:
            next_offset_buffer = int(np.round((offset_result + 1) * sample_rate_ratio))
            accum = 0.0
            count = 0
            for i in range(offset_buffer, min(next_offset_buffer, len(buffer))):
                accum += buffer[i]
                count += 1
            result[offset_result] = accum / count if count > 0 else 0
            offset_result += 1
            offset_buffer = next_offset_buffer

        return result

    def audio_callback(self, in_data, frame_count, time_info, status_flags):
        """Processes audio input data."""
        if status_flags:
            print(status_flags)
        resampled_data = self.downsample_buffer(np.frombuffer(in_data, dtype=np.float32), self.input_sample_rate, self.output_sample_rate)
        self.input_data(resampled_data.tobytes())
        return (in_data, pyaudio.paContinue)

    async def send_audio_data(self):
        """Sends the encoded PCM data to the server via WebSocket."""
        async with websockets.connect(self.server_uri) as websocket:
            while self.is_recording:
                if self.audio_data['size'] > 0:
                    pcm_data = self.encode_pcm()
                    await websocket.send(pcm_data)
                    self.clear()  # Clear after sending
                await asyncio.sleep(0.5)  # Control the sending frequency

    def start(self):
        """Starts recording audio and the WebSocket transmission."""
        self.is_recording = True
        self.stream = self.pyaudio_instance.open(
            format=pyaudio.paFloat32,
            channels=self.channel_count,
            rate=self.input_sample_rate,
            input=True,
            stream_callback=self.audio_callback
        )
        print("Recording and sending data... Press Ctrl+C to stop.")
        asyncio.run(self.send_audio_data())

    def stop(self):
        """Stops recording audio."""
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        self.pyaudio_instance.terminate()

# Example usage
if __name__ == "__main__":
    recorder = Recorder(
        input_sample_rate=44100,
        output_sample_rate=16000,
        channel_count=1,
        server_uri="ws://127.0.0.1:8888/ws/transcribe?lang=zh"
    )

    try:
        recorder.start()
    except Exception as e:
        print(f"Error: {e}")

    recorder.stop()
