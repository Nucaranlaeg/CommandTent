# from multiprocessing import freeze_support
from typing import Any
from RealtimeSTT import AudioToTextRecorder
from map.map import game_map

def process_text(text: str) -> None:
	print(f"Received text: {text}")
	for word in text.split():
		word = word.strip(" .,!?")
		try:
			cell = game_map.find_cell(word)
			print(f"Found cell: {cell}")
		except:
			print(f"'{word}' is not a valid cell location.")
			pass

if __name__ == '__main__':
	recorder: Any = AudioToTextRecorder()
	print("Game is ready!")
	try:
		while True:
			recorder.text(process_text)
	except KeyboardInterrupt as e:
		recorder.stop()