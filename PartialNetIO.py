import requests
from io import BufferedIOBase

def _FileSizeByUrl(url):
	r = requests.head(url)
	return int(r.headers["Content-Length"])

def _DownloadBytesRange(url, s_range):
	# print(f"_DownloadBytesRange(*, {s_range})")
	r = requests.get(url, headers = { "Range" : f"bytes={s_range}" })
	return r.content

class PartialNetIO(BufferedIOBase):
	def __init__(self, urls):
		self.urls = urls
		self.parts_size = list(map(_FileSizeByUrl, urls))
		# for index in range(1, parts_count):
		# 	part_url = url + f".{index:03d}"
		# 	self.urls.append(part_url)
		# 	self.parts_size.append(_FileSizeByUrl(part_url))
		self.offset = 0
		self.current_part = 0
		self.current_part_offset = 0
		self.file_size = sum(self.parts_size)
	def readable(self):
		return True
	def writeable(self):
		return False
	def seekable(self):
		return True
	def close(self):
		super().close()
	def read(self, size=-1):
		if self.current_part == -1:
			return b""

		# get needed part
		part_requests = []
		check_size = size
		if size == -1:
			# read until end
			first = True
			for url in self.urls[self.current_part:]:
				if first:
					part_requests.append((
						url,
						f"{self.current_part_offset}-"
					))
					first = False
				else:
					part_requests.append((
						url,
						"0"
					))
		else:
			# read normal
			current_size = self.parts_size[self.current_part]
			current_url = self.urls[self.current_part]
			only_current = False
			if check_size <= current_size - self.current_part_offset:
				# only read current part
				part_requests.append((
					current_url,
					f"{self.current_part_offset}-{self.current_part_offset + check_size - 1}"
				))
				only_current = True
			else:
				# start from current
				part_requests.append((
					current_url,
					f"{self.current_part_offset}-"
				))
				check_size -= (current_size - self.current_part_offset)
				self.current_part_offset = 0
			next_part = self.current_part + 1
			if not only_current:
				for url, part_size in zip(self.urls[next_part:], self.parts_size[next_part:]):
					# print(f"check: {check_size}, part: {part_size}")
					if check_size <= part_size:
						# read size inside this part
						part_requests.append((
							url,
							f"{self.current_part_offset}-{self.current_part_offset + check_size - 1}"
						))
						break
					else:
						# read size outside this part
						part_requests.append((
							url,
							"0"
						))

					check_size -= part_size



		# self.current_part = self.urls.index(part_requests[-1][0])
		# print(f"current part: {self.current_part}")
		# print(f"download: {part_requests}")
		# downloaded_bytes = _DownloadBytesRange(*part_requests.pop(0))
		downloaded_bytes = b""
		for request in part_requests:
			downloaded_bytes += _DownloadBytesRange(*request)

		self.offset += size

		return downloaded_bytes
	def seek(self, offset, whence=0):
		if whence == 0: # Seek from start of file
			if offset < 0:
				raise OSError("[Errno 22] Invalid argument")
			self.offset = offset
		elif whence == 1: # Seek from current position
			if self.offset - offset < 0:
				raise OSError("[Errno 22] Invalid argument")
			self.offset += offset
		elif whence == 2: # Seek from EOF
			if self.file_size - offset < 0:
				raise OSError("[Errno 22] Invalid argument")
			self.offset = self.file_size + offset
		else:
			raise ValueError("whence must be os.SEEK_SET (0), "
							 "os.SEEK_CUR (1), or os.SEEK_END (2)")

		total = 0
		for index, part_size in enumerate(self.parts_size):
			if total <= self.offset and self.offset < total + part_size:
				self.current_part = index
				# print(f"total: {total}, offset: {self.offset}")
				self.current_part_offset = self.offset - total
				break
			total += part_size
		else:
			self.current_part = -1

		return self.offset

	def tell(self):
		return self.offset