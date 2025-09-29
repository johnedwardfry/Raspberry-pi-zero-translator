import pyaudio
import wave

# --- Settings ---
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 3
FILENAME = "ultimate_test.wav"

# --- Main Test ---
p = pyaudio.PyAudio()

# --- Recording Phase ---
try:
    print("--- Starting 3-second recording... Speak now! ---")
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    print("--- Recording complete. ---")

    # Save the recording
    with wave.open(FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    # --- Playback Phase ---
    print("--- Playing audio back... ---")
    with wave.open(FILENAME, 'rb') as wf:
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        data = wf.readframes(CHUNK)
        while data:
            stream.write(data)
            data = wf.readframes(CHUNK)

        stream.stop_stream()
        stream.close()

    print("--- ✅ Test finished. Did you hear the recording? ---")

except Exception as e:
    print(f"--- ❌ An error occurred: {e} ---")
finally:
    p.terminate()
    if os.path.exists(FILENAME):
        os.remove(FILENAME)