import itertools
import json
import typing
from abc import ABC

import tornado.web
import ts3_api


def ts3_api_call_wrapper(handler: tornado.web.RequestHandler, call_func) -> typing.Union[bool, typing.List[typing.Dict[str, str]], typing.Dict[str, str]]:
	try:
		return call_func()
	except ts3_api.TS3APIInternalError as e:
		handler.set_status(500)
		exception = e
	except ts3_api.TS3APINotFoundError as e:
		handler.set_status(404)
		exception = e
	except ts3_api.TS3APIBadRequestError as e:
		handler.set_status(400)
		exception = e

	handler.write(str(exception))
	return False


class AbstractRequestHandler(tornado.web.RequestHandler, ABC):
	def initialize(self, api):
		self.api: ts3_api.TeamSpeak3ServerAPI = api


class StateHandler(AbstractRequestHandler, ABC):
	def get(self):
		# Fetch server name and description
		result = ts3_api_call_wrapper(self, self.api.get_server_name_description)
		if not result:
			return

		server_name, server_description = result

		# Fetch channel information
		channel_list = ts3_api_call_wrapper(self, self.api.get_channel_list)
		if not channel_list:
			return

		# Convert channel list to dict
		channels = {int(channel["channel_id"]): channel for channel in channel_list}

		# Fetch online client information
		online_clients_list = ts3_api_call_wrapper(self, self.api.get_online_clients)
		if not online_clients_list:
			return

		# Group online clients by channel id and drop channel id
		online_clients_list = sorted(online_clients_list, key=lambda client: client["channel_id"])
		online_clients_by_channel = itertools.groupby(online_clients_list, key=lambda client: int(client["channel_id"]))
		online_clients_by_channels = {int(channel_id): list(clients) for channel_id, clients in online_clients_by_channel}
		for online_clients_in_channel in online_clients_by_channels.values():
			for client in online_clients_in_channel:
				del client["channel_id"]

		# Put channels into hierarchical order and make id names more intuitive
		# Channels are already in the same order as on the teamspeak
		hierarchy = {
			"server_name": server_name,
			"server_description": server_description,
			"channels": []
		}
		hierarchical_channels = hierarchy["channels"]

		for channel in channels.values():
			parent_channel_id = int(channel["pid"])
			del channel["pid"]

			channel_id = int(channel["channel_id"])
			del channel["channel_id"]

			if int(channel["total_clients"]) > 0:
				# Insert clients into channel
				del channel["total_clients"]
				channel["clients"] = online_clients_by_channels[channel_id]

			if parent_channel_id == 0:
				# Add channel to the top of the hierarchy
				hierarchical_channels.append(channel)
			else:
				# Add this channel to its parent channel
				parent_channel = channels[parent_channel_id]

				if "sub_channels" not in parent_channel:
					parent_channel["sub_channels"] = []

				parent_channel["sub_channels"].append(channel)

		self.set_header("Content-Type", "application/json")
		self.write(json.dumps(hierarchy))


class KnownClientsHandler(AbstractRequestHandler, ABC):
	def get(self, last_seen_after: str = None):
		known_clients = ts3_api_call_wrapper(self, self.api.get_known_clients)
		if not known_clients:
			return

		self.set_header("Content-Type", "application/json")
		self.write(json.dumps(known_clients))


class OnlineClientsHandler(AbstractRequestHandler, ABC):
	def get(self):
		online_clients = ts3_api_call_wrapper(self, self.api.get_online_clients)
		if not online_clients:
			return

		self.set_header("Content-Type", "application/json")
		self.write(json.dumps(online_clients))


class OnlineClientInfoHandler(AbstractRequestHandler, ABC):
	def get(self, online_client_id):
		online_client_info = ts3_api_call_wrapper(self, lambda: self.api.get_online_client_info(online_client_id))
		if not online_client_info:
			return

		self.set_header("Content-Type", "application/json")
		self.write(json.dumps(online_client_info))


class KnownClientInfoHandler(AbstractRequestHandler, ABC):
	def get(self, known_client_id):
		known_client_info = ts3_api_call_wrapper(self, lambda: self.api.get_known_client_info(known_client_id))
		if not known_client_info:
			return

		self.set_header("Content-Type", "application/json")
		self.write(json.dumps(known_client_info))
