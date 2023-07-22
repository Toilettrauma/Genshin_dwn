# import PartialNetIO
import NewNetIO as PartialNetIO
import zipfile
import requests
import os
from time import perf_counter, sleep
import json
import hashlib

"""
Base api url : https://hk4e-launcher-static.hoyoverse.com/hk4e_global
api urls : [
	/mdk/launcher/api/prevResource
	/mdk/launcher/api/resource
	/mdk/launcher/api/prevContent
	/mdk/launcher/api/content
]
my api params : [
	key : gcStrarh
	language : ru-ru
	launcher_id : 10
]

plugin api params : [
	{default},
	device_id : win10
]
"""

api_params = "key=gcStgarh&language=ru-ru&launcher_id=10"
headers = { "content-type" : "application/json" }
def _GetGameInfo(api_url):
	r = requests.get(f"https://hk4e-launcher-static.hoyoverse.com/hk4e_global/mdk/launcher/api/{api_url}?{api_params}", headers = headers)
	return r.json()["data"]

# def _GetGamePartsUrl(game_url):
# 	urls = []
# 	for index in range(1, 100):
# 		url = f"{game_url}.{index:03d}"
# 		r = requests.head(url)
# 		if r.status_code == 404:
# 			break
# 		urls.append(url)
# 	return urls

def _GetGamePartsUrl(game_info):
	return [segment["path"] for segment in game_info["segments"]]


def _GetDownloadFiles(zip_file):
	download_files = []
	partial_download_files = []
	downloaded_size = 0
	for file in zip_file.namelist():
		zinfo = zip_file.getinfo(file)
		if file[-1] == "/":
			continue # is a dir 
		if os.path.isfile(file):
			real_file_size = os.path.getsize(file)
			if real_file_size != zinfo.file_size:
				partial_download_files.append((
					file,
					real_file_size
				))
			else:
				downloaded_size += real_file_size
		else:
			download_files.append(file)

	return downloaded_size, partial_download_files, download_files

# def _CreateDirStructure(files):
# 	for file in files:
# 		prev_dir = None
# 		file_dir = os.path.split(file)[0]
# 		while not os.path.isdir(file_dir):
# 			prev_dir = file_dir
# 			file_dir = os.path.split(file_dir)

def _OpenCachedZipFile(fp):
	try:
		zip_file = zipfile.ZipFile(f"cached_zipinfo.cache")
		zip_file.fp = fp
	except FileNotFoundError as e:
		print("Cached zip info not found. Creating...")
		zip_file = zipfile.ZipFile(fp)
		with open(f"cached_zipinfo.cache", "wb") as f:
			zip_file.fp = f
			zip_file.start_dir = 0
			zip_file._write_end_record()
		zip_file.fp = fp
		print("Created")

	return zip_file


def DownloadArchive(archive_urls, download_path="Genshin_impact", chunk_size=(1 << 20)): # chunk_size = 1M
	if not os.path.isdir(download_path):
		os.mkdir(download_path)
	os.chdir(download_path)

	nb = PartialNetIO.PartialNetIO(archive_urls)
	# zip_file = zipfile.ZipFile(nb)
	zip_file = _OpenCachedZipFile(nb)
	print(f"Content size: {sum(map(lambda v: v.file_size, zip_file.filelist)) / (1024 ** 3):.2f}GB")

	downloaded_size, partial_download_files, download_files = _GetDownloadFiles(zip_file)
	chunk_mb_size = chunk_size / 1024 // 1024
	total_size = nb.file_size
	total_size_mb = total_size / (1024 ** 2)
	# download partially downloaded files
	for file_opts in partial_download_files:
		file_name, real_size = file_opts
		file_path = os.path.split(file_name)[0]
		if file_path != "":
			os.makedirs(file_path, exist_ok=True)

		zip_ref = zip_file.open(file_name)
		zip_ref.seek(real_size)
		file_size = zip_file.getinfo(file_name).file_size
		with open(file_name, "ab") as fp:
			while not zip_ref._eof:
				# perfomance
				before_cur = fp.tell()
				start_time = perf_counter()
				# write to file
				fp.write(zip_ref.read(chunk_size))
				fp.flush()
				# perfomance calculate
				download_time = perf_counter() - start_time
				downloaded_size_mb = downloaded_size / (1024 ** 2)
				print(f'file: {file_name}', f'progress: {fp.tell() / (1024 ** 2):.1f}MB/{file_size:.1f}MB', f'total: {downloaded_size_mb:.1f}MB/{total_size_mb:.1f}MB ({downloaded_size_mb/total_size_mb*100:.2f}%)', f'avg: {(fp.tell() - before_cur) / (1024 ** 2) / download_time:.1f} M/s	', end="\r")

	# download files
	for file_name in download_files:
		file_path = os.path.split(file_name)[0]
		if file_path != "":
			os.makedirs(file_path, exist_ok=True)

		zip_ref = zip_file.open(file_name)
		file_size = zip_file.getinfo(file_name).file_size / (1024 ** 2) # MB
		with open(file_name, "wb") as fp:
			while not zip_ref._eof:
				# perfomance
				before_cur = fp.tell()
				start_time = perf_counter()
				# write to file
				fp.write(zip_ref.read(chunk_size))
				fp.flush()
				# perfomance calculate
				download_time = perf_counter() - start_time
				downloaded_size += fp.tell() - before_cur
				downloaded_size_mb = downloaded_size / (1024 ** 2)
				print(f'file: {file_name}', f'progress: {fp.tell() / (1024 ** 2):.1f}MB/{file_size:.1f}MB', f'total: {downloaded_size_mb:.1f}MB/{total_size_mb:.1f}MB ({downloaded_size_mb/total_size_mb*100:.2f}%)', f'avg: {(fp.tell() - before_cur) / (1024 ** 2) / download_time:.1f} M/s	', end="\r")

time_unit_downloaded = 0
current_file = None
def speed_worker():
	...

def worker(fileslist):
	...

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def CheckGame(pkg_version_file, game_dir="Genshin_impact"):
	if not os.path.isdir(game_dir):
		print('game not found')
	os.chdir(game_dir)
	with open(pkg_version_file, "r") as f:
		total_entries = len(list(f))
		f.seek(0)
		for index, line in enumerate(f, start=1):
			file_info = json.loads(line)
			file_name, file_hash, file_size = file_info.values()
			# if not os.path.isfile(file_name):
			# 	print(f'file not found: {file_name}')
			# 	continue
			real_hash = md5(file_name)
			if real_hash != file_hash:
				print(f'Wrong hash for file: {file_name}, real: {real_hash}, orig: {file_hash}')
				continue
			real_size = os.path.getsize(file_name)
			if real_size != file_size:
				print(f'Wrong size for file: {file_name}, real: {real_size}, orig: {file_size}')
			print(f'checked: {index}/{total_entries}  file: {file_name}             ', end="\r")

# # debug
# import signal
# def break_signal(sig, frame):
# 	breakpoint()
# 	signal.sigpending()
# signal.signal(signal.SIGINT, break_signal)

if __name__ == "__main__":
	info = _GetGameInfo("resource")
	game_info = info["game"]["latest"]
	game_diffs = info["game"]["diffs"]

	choice_action = input("choose action (banner/download/check/update): ")
	if choice_action == "banner":
		info = _GetGameInfo("content")
		for post in info["post"]:
			if post["type"] == "POST_TYPE_ACTIVITY":
				print(f'BANNER_NAME: {post["tittle"]}')
				print(f'BANNER_URL: {post["url"]}')
				print()
	elif choice_action == "download":
		print(f'GAME_VERSION: {game_info["version"]}')

		choice_download_action = input("choose to download (game/voice): ")
		if choice_download_action == "game":
			parts_url = _GetGamePartsUrl(game_info)
			DownloadArchive(parts_url)
		elif choice_download_action == "voice":
			voice_packs = game_info["voice_packs"]
			voice_packs_names = list(map(lambda v: v["language"], voice_packs))
			choice_lang = input(f'choose game language ({"/".join(voice_packs_names)}): ')

			voice_path = voice_packs[voice_packs_names.index(choice_lang)]["path"]
			DownloadArchive([voice_path], download_path="Genshin_impact_voice")
	elif choice_action == "check":
		choice_check = input("choose to check (game/voice): ")
		if choice_check == "game":
			CheckGame("pkg_version")
		elif choice_check == "voice":
			pkg_version_file = [f for f in os.listdir("Genshin_impact_voice") if f.startswith("Audio") and f.endswith("pkg_version")][0]
			CheckGame(pkg_version_file, game_dir="Genshin_impact_voice")

	elif choice_action == "update":
		choice_ver = input("input your game version: ")
		for diff in game_diffs:
			if diff["version"] == choice_ver:
				update_diff = diff
				break
		else:
			print("Version not found")
			exit()

		choice_download_action = input("choose to update (game/voice): ")
		if choice_download_action == "game":
			DownloadArchive([diff["path"]], download_path="Genshin_impact_update")
		elif choice_download_action == "voice":
			voice_packs = update_diff["voice_packs"]
			voice_packs_names = list(map(lambda v: v["language"], voice_packs))
			choice_lang = input(f'choose game language ({"/".join(voice_packs_names)}): ')

			voice_path = voice_packs[voice_packs_names.index(choice_lang)]["path"]
			DownloadArchive([voice_path], download_path="Genshin_impact_voice_update")


