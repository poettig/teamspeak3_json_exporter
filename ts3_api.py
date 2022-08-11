import json
import re
import typing

import requests


class TeamSpeak3ServerAPI:
	def __init__(self, host: str, scheme: str, port: int, virtual_server_id: int, token: str):
		self.host = host
		self.scheme = scheme
		self.port = port
		self.virtual_server_id = virtual_server_id
		self.token = token

		self.db_clients_cache = None

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

		if response.status_code != 200:
			raise ValueError(f"Failed request to path /{cleaned_path}: {response.content.decode('utf-8')}")

		try:
			data = response.json()
		except json.JSONDecodeError as jde:
			raise ValueError(f"Failed to decode TeamSpeak3 server response as JSON: {jde}")

		status = data.get("status")
		if status is None:
			raise ValueError("TeamSpeak3 server JSON response did not contain the request status info.")

		status_code = status.get("code")
		if status_code is None:
			raise ValueError("TeamSpeak3 server JSON response status info did not contain the status code.")

		if status_code != 0:
			raise ValueError(f"Request to /{cleaned_path} failed: {status_code} ({status.get('message', '')})")

		body = data.get("body")
		if body is None:
			raise ValueError("TeamSpeak3 server JSON response did not contain the expected 'body' key.")

		return body

	def get_version(self):
		return self.do_request(f"/version")[0]

	def get_channel_list(self) -> typing.List[typing.Dict[str, str]]:
		query_params = {
			"-flags": "",
			"-limits": "",
			"-secondsempty": ""
		}
		return self.do_request(f"/{self.virtual_server_id}/channellist", query_params)

	def get_online_clients(self) -> typing.List[typing.Dict[str, str]]:
		query_params = {
			"-away": "",
			"-voice": "",
			"-times": "",
			"-groups": "",
			"-country": ""
		}
		return self.do_request(f"/{self.virtual_server_id}/clientlist", query_params)

	def get_known_clients(self) -> typing.List[typing.Dict[str, str]]:
		if self.db_clients_cache:
			# Check if the client list changed (there is a new client with a higher cldbid)
			current_highest_cldbid = self.db_clients_cache[-1]["cldbid"]
			query_params = {"start": str(len(self.db_clients_cache) - 1)}
			last_db_client = self.do_request(f"/{self.virtual_server_id}/clientdblist", query_params)[0]

			if current_highest_cldbid == last_db_client["cldbid"]:
				# No change in clients, no need to redownload
				return self.db_clients_cache

		self.db_clients_cache = []
		max_clients_per_page = 25
		num_clients_in_page = max_clients_per_page

		while num_clients_in_page == max_clients_per_page:
			query_params = {"start": str(len(self.db_clients_cache))}
			clients_in_page = self.do_request(f"/{self.virtual_server_id}/clientdblist", query_params)
			self.db_clients_cache.extend(clients_in_page)
			num_clients_in_page = len(clients_in_page)

		return self.db_clients_cache

	def get_online_client_info(self, clid: str):
		return self.do_request(f"/{self.virtual_server_id}/clientinfo", {"clid": clid})[0]

	def get_known_client_info(self, cldbid: str):
		return self.do_request(f"/{self.virtual_server_id}/clientdbinfo", {"cldbid": cldbid})[0]
