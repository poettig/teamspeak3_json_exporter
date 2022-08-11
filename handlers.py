import json
from abc import ABC

import tornado.web
import ts3_api


class PingHandler(tornado.web.RequestHandler, ABC):
	def get(self):
		self.write("pong")


class StateHandler(tornado.web.RequestHandler, ABC):
	def initialize(self, api):
		self.api: ts3_api.TeamSpeak3ServerAPI = api

	def get(self):
		self.write(",".join([channel["channel_name"] for channel in self.api.get_channel_list()]))


class KnownClientsHandler(tornado.web.RequestHandler, ABC):
	def initialize(self, api):
		self.api: ts3_api.TeamSpeak3ServerAPI = api

	def get(self, last_seen_after: str = None):
		print(last_seen_after)
		known_clients = self.api.get_known_clients()

		if len(known_clients) == 0:
			self.set_status(404)
			self.write("No known clients found.")

		self.write(json.dumps(known_clients))


class OnlineClientsHandler(tornado.web.RequestHandler, ABC):
	def initialize(self, api):
		self.api: ts3_api.TeamSpeak3ServerAPI = api

	def get(self):
		online_clients = self.api.get_online_clients()

		if len(online_clients) == 0:
			self.set_status(404)
			self.write("No online clients found.")

		self.write(json.dumps(online_clients))


class OnlineClientInfoHandler(tornado.web.RequestHandler, ABC):
	def initialize(self, api):
		self.api: ts3_api.TeamSpeak3ServerAPI = api

	def get(self, online_client_id):
		self.write(json.dumps(self.api.get_online_client_info(online_client_id)))


class KnownClientInfoHandler(tornado.web.RequestHandler):
	def initialize(self, api):
		self.api: ts3_api.TeamSpeak3ServerAPI = api

	def get(self, known_client_id):
		self.write(json.dumps(self.api.get_known_client_info(known_client_id)))
