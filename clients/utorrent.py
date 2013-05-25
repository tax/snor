import transmissionrpc
from clients import BaseCLient

class Client(BaseCLient):

	def add_magnet_link(self, url, dowload_dir):
		client = transmissionrpc.Client('localhost', port=9091)
		return client.add_torrent(url, download_dir=download_dir)

	def get_completed(self):
		print 'Completed'

	def is_active(self):
		return True
