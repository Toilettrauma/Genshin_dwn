import requests
from io import BufferedIOBase

def _FileSizeByUrl(url):
	r = requests.head(url)
	return int(r.headers["Content-Length"])

def _CreateBytesStreamRange(url, s_range):
	# print(f"_DownloadBytesRange(*, {s_range})")
	if s_range is None:
		r = requests.get(url, stream=True)
	else:
		r = requests.get(url, headers = { "Range" : f"bytes={s_range}" }, stream=True)
	return r.raw

class PartialNetIO(BufferedIOBase):
	def __init__(self, urls):
		self.urls = urls
		self.parts_size = list(map(_FileSizeByUrl, urls))
		self.offset = 0
		self.current_part = 0
		self.current_part_offset = 0
		self.file_size = sum(self.parts_size)

		self._stream = None
		self._stream_offset = 0
		self._stream_part_size = 0
	def readable(self):
		return True
	def writeable(self):
		return False
	def seekable(self):
		return True
	def close(self):
		super().close()
	def read(self, size=-1):
		if self.offset >= self.file_size:
			return b""

		if not (self._stream and self._stream_offset == self.offset):
			self._stream = _CreateBytesStreamRange(self.urls[self.current_part], f"-{self.parts_size[self.current_part] - self.current_part_offset}")
			self._stream_part_size = self.parts_size[self.current_part] - self.current_part_offset

		return_bytes = bytes()
		last_size = size
		while len(return_bytes) < size or size == -1:
			# print(size, last_size, self._stream_part_size, self.current_part)
			if size == -1:
				stream_ret = self._stream.read()
			else:
				stream_ret = self._stream.read(min(last_size, self._stream_part_size))
			if not stream_ret:
				print("something went wrong!")
				breakpoint()
			self._stream_part_size -= len(stream_ret)
			last_size -= len(stream_ret)
			return_bytes += stream_ret

			if last_size <= 0 and size != -1:
				break
			if self._stream_part_size <= 0:
				# print(size, self._stream_part_size, self.current_part)
				if self.current_part + 1 >= len(self.urls):
					self.current_part = -1
					break
				self.current_part += 1
				self._stream_part_size = self.parts_size[self.current_part]
				# print(self.urls[self.current_part])
				self._stream = _CreateBytesStreamRange(self.urls[self.current_part], None)

		self.offset += len(return_bytes)
		self._stream_offset = self.offset

		return return_bytes
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