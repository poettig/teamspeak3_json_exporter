import json
import re
import typing

import requests


class TS3APIInternalError(Exception):
	pass


class TS3APINotFoundError(Exception):
	pass


class TS3APIBadRequestError(Exception):
	pass


class TeamSpeak3ServerAPI:
	def __init__(self, host: str, scheme: str, port: int, virtual_server_id: int, token: str):
		self.host = host
		self.scheme = scheme
		self.port = port
		self.virtual_server_id = virtual_server_id
		self.token = token

		self.known_clients_cache = None

	def do_request(self, path: str, query_params: typing.Dict[str, str] = None):
		cleaned_path = path
		if path.startswith("/"):
			cleaned_path = re.sub(r"^/+", "", path)

		auth_header = {"x-api-key": self.token}
		response = requests.get(
			f"{self.scheme}://{self.host}:{self.port}/{cleaned_path}",
			headers=auth_header,
			params=query_params
		)

		try:
			data = response.json()
		except json.JSONDecodeError as jde:
			raise TS3APIInternalError(f"Failed to decode TeamSpeak3 server response as JSON: {jde}")

		status = data.get("status")
		if status is None:
			raise TS3APIInternalError("TeamSpeak3 server JSON response did not contain the request status info.")

		status_code = status.get("code")
		if status_code is None:
			raise TS3APIInternalError("TeamSpeak3 server JSON response status info did not contain the status code.")

		if status_code != 0:
			if status_code in [512]:
				raise TS3APINotFoundError(f"{status_code} ({status.get('message', '')})")
			else:
				raise TS3APIBadRequestError(f"Request to TS3 WebQuery API failed: {status_code} ({status.get('message', '')})")

		body = data.get("body")
		if body is None:
			raise TS3APIInternalError("TeamSpeak3 server JSON response did not contain the expected 'body' key.")

		return body

	def get_version(self):
		return self.do_request(f"/version")[0]

	def get_channel_list(self) -> typing.List[typing.Dict[str, str]]:
		query_params = {
			"-flags": "",
			"-limits": "",
			"-secondsempty": ""
		}
		channel_list = self.do_request(f"/{self.virtual_server_id}/channellist", query_params)

		# Replace cid with channel_id as it is more intuitive
		for channel in channel_list:
			channel["channel_id"] = channel["cid"]
			del channel["cid"]

		return channel_list

	def get_online_clients(self) -> typing.List[typing.Dict[str, str]]:
		query_params = {
			"-away": "",
			"-voice": "",
			"-times": "",
			"-groups": "",
			"-country": ""
		}
		online_clients = self.do_request(f"/{self.virtual_server_id}/clientlist", query_params)

		# Replace cid and clid by channel_id and online_client_id as it is more intuitive
		for online_client in online_clients:
			online_client["channel_id"] = online_client["cid"]
			del online_client["cid"]

			online_client["online_client_id"] = online_client["clid"]
			del online_client["clid"]

		return online_clients

	def get_known_clients(self) -> typing.List[typing.Dict[str, str]]:
		if self.known_clients_cache:
			# Check if the client list changed (there is a new client with a higher known_client_id)
			current_highest_known_client_id = self.known_clients_cache[-1]["known_client_id"]
			query_params = {"start": str(len(self.known_clients_cache) - 1)}
			last_db_client = self.do_request(f"/{self.virtual_server_id}/clientdblist", query_params)[0]

			if current_highest_known_client_id == last_db_client["cldbid"]:
				# No change in clients, no need to redownload
				return self.known_clients_cache

		self.known_clients_cache = []
		max_clients_per_page = 25
		num_clients_in_page = max_clients_per_page

		while num_clients_in_page == max_clients_per_page:
			query_params = {"start": str(len(self.known_clients_cache))}
			clients_in_page = self.do_request(f"/{self.virtual_server_id}/clientdblist", query_params)
			self.known_clients_cache.extend(clients_in_page)
			num_clients_in_page = len(clients_in_page)

		# Replace cldbid with known_client_id as it is more intuitive
		for known_client in self.known_clients_cache:
			known_client["known_client_id"] = known_client["cldbid"]
			del known_client["cldbid"]

		return self.known_clients_cache

	def get_online_client_info(self, online_client_id: str):
		online_client_list = self.do_request(f"/{self.virtual_server_id}/clientinfo", {"clid": online_client_id})

		if len(online_client_list) > 1:
			raise TS3APIInternalError(f"Unexpectedly got more than one online client for id {online_client_id}")
		elif len(online_client_list) == 0:
			raise TS3APINotFoundError(f"No online client with id {online_client_id} found.")

		# Replace cid by channel_id as it is more intuitive
		online_client = online_client_list[0]
		online_client["channel_id"] = online_client["cid"]
		del online_client["cid"]

		return online_client

	def get_known_client_info(self, known_client_id: str):
		known_client_list = self.do_request(f"/{self.virtual_server_id}/clientdbinfo", {"cldbid": known_client_id})[0]

		if len(known_client_list) > 1:
			raise TS3APIInternalError(f"Unexpectedly got more than one online client for id {known_client_id}")
		elif len(known_client_list) == 0:
			raise TS3APINotFoundError(f"No online client with id {known_client_id} found.")

		return known_client_list[0]

	def get_server_name_description(self):
		server_info = self.do_request(f"/{self.virtual_server_id}/serverinfo")[0]
		return server_info["virtualserver_name"], server_info["virtualserver_welcomemessage"]

	def get_channel_info(self, channel_id: str):
		return self.do_request(f"/{self.virtual_server_id}/channelinfo", {"cid": channel_id})
